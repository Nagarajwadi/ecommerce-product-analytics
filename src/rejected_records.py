"""In-memory quarantine and reconciliation for incoming event records.

This module has no file or database I/O. It classifies rows using explicitly
supplied validation rules and preserves the original row values in the rejected
output. Duplicate detection is intentionally not performed here; duplicate
delivery and invalid data are separate outcomes.
"""
from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


DEFAULT_REQUIRED_COLUMNS = ("user_id", "session_id", "event_name", "timestamp")
DEFAULT_VALID_EVENT_TYPES = {
    "app_open",
    "search",
    "view_product",
    "add_to_cart",
    "checkout_start",
    "purchase",
}


def classify_event_batch(
    batch: pd.DataFrame,
    required_columns: Iterable[str] = DEFAULT_REQUIRED_COLUMNS,
    valid_event_types: Iterable[str] = DEFAULT_VALID_EVENT_TYPES,
) -> dict[str, object]:
    """Split an input batch into accepted and rejected rows with reason codes.

    Reasons are accumulated per row in deterministic order. Required fields are
    checked for missing/blank values, timestamps must match the documented
    '%Y-%m-%d %H:%M:%S' format, and event names must be in the allowed set.
    Original values are retained in both outputs. Duplicate/replay detection is
    deliberately separate from validation.
    """
    required_columns = list(required_columns)
    valid_event_types = set(valid_event_types)
    missing_columns = [column for column in required_columns if column not in batch.columns]
    if missing_columns:
        raise ValueError(f"Input batch is missing required columns: {missing_columns}")

    original = batch.copy(deep=True)
    reasons_by_position: list[list[str]] = [[] for _ in range(len(original))]

    for column in required_columns:
        values = original[column]
        missing = values.isna()
        if pd.api.types.is_string_dtype(values.dtype) or values.dtype == object:
            missing = missing | values.astype("string").str.strip().eq("").fillna(False)
        for position in range(len(original)):
            if bool(missing.iloc[position]):
                reasons_by_position[position].append(f"missing_required:{column}")

    parsed_timestamps = pd.to_datetime(
        original["timestamp"],
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )
    for position, parsed in enumerate(parsed_timestamps):
        if pd.isna(parsed) and not any(
            reason == "missing_required:timestamp"
            for reason in reasons_by_position[position]
        ):
            reasons_by_position[position].append("invalid_timestamp")

    events = original["event_name"].astype("string").str.strip()
    for position, event_name in enumerate(events):
        if pd.notna(event_name) and event_name not in valid_event_types:
            reasons_by_position[position].append("invalid_event_name")

    rejected_positions = [i for i, reasons in enumerate(reasons_by_position) if reasons]
    accepted_positions = [i for i, reasons in enumerate(reasons_by_position) if not reasons]

    accepted = original.iloc[accepted_positions].copy().reset_index(drop=True)
    rejected = original.iloc[rejected_positions].copy()
    rejected["rejection_reasons"] = [
        "|".join(reasons_by_position[i]) for i in rejected_positions
    ]
    rejected = rejected.reset_index(drop=True)

    received_rows = len(original)
    accepted_rows = len(accepted)
    rejected_rows = len(rejected)
    if received_rows != accepted_rows + rejected_rows:
        raise ValueError("Batch reconciliation failed: received rows must equal accepted plus rejected.")

    return {
        "accepted": accepted,
        "rejected": rejected,
        "received_rows": int(received_rows),
        "accepted_rows": int(accepted_rows),
        "rejected_rows": int(rejected_rows),
        "reconciliation_passed": True,
        "duplicate_policy": "not_checked_by_validation; use a separate identity/replay step",
    }

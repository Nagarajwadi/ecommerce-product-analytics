"""In-memory incremental batch prototype with explicit identity limitations.

This module performs no file or database I/O. It does not modify the input
DataFrames. The default composite fingerprint is a batch deduplication aid,
not a guaranteed event identifier: two legitimate identical events can collide.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable

import pandas as pd


DEFAULT_IDENTITY_COLUMNS = [
    "user_id",
    "timestamp",
    "session_id",
    "event_name",
    "product_id",
    "category",
    "price",
    "quantity",
    "device",
    "country",
    "traffic_source",
    "experiment_group",
]


def _canonical_value(value: object) -> object:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except (TypeError, ValueError):
            pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


def event_fingerprint(
    row: pd.Series,
    identity_columns: Iterable[str] = DEFAULT_IDENTITY_COLUMNS,
) -> str:
    """Return a deterministic hash of selected fields, not a source event ID."""
    payload = {
        column: _canonical_value(row[column])
        for column in identity_columns
    }
    serialized = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def process_incremental_batch(
    existing_events: pd.DataFrame,
    incoming_batch: pd.DataFrame,
    identity_columns: Iterable[str] = DEFAULT_IDENTITY_COLUMNS,
) -> dict[str, object]:
    """Append unseen fingerprints in memory and report batch reconciliation.

    Existing and incoming frames must have compatible columns and include all
    identity columns. Existing rows are retained as-is. Duplicate fingerprints
    inside the incoming batch are counted as duplicates and only the first is
    accepted. No input frame is mutated.
    """
    identity_columns = list(identity_columns)
    if list(existing_events.columns) != list(incoming_batch.columns):
        raise ValueError("Existing and incoming batches must have identical column order.")

    for label, frame in (
        ("existing_events", existing_events),
        ("incoming_batch", incoming_batch),
    ):
        missing = [col for col in identity_columns if col not in frame.columns]
        if missing:
            raise ValueError(f"{label} is missing identity columns: {missing}")

    existing = existing_events.copy(deep=True)
    incoming = incoming_batch.copy(deep=True)

    existing_fingerprints = existing.apply(
        lambda row: event_fingerprint(row, identity_columns), axis=1
    )
    incoming["_fingerprint"] = incoming.apply(
        lambda row: event_fingerprint(row, identity_columns), axis=1
    )

    seen = set(existing_fingerprints.tolist())
    accepted_indices: list[int] = []
    duplicate_existing = 0
    duplicate_within_batch = 0

    for idx, fingerprint in incoming["_fingerprint"].items():
        if fingerprint in seen:
            duplicate_existing += 1
            continue
        seen.add(fingerprint)
        accepted_indices.append(idx)

    accepted_fingerprints = incoming.loc[accepted_indices, "_fingerprint"]
    # A fingerprint that repeats within the incoming batch is excluded by the
    # same seen-set rule; report all excluded rows in one count for clarity.
    accepted_count = len(accepted_indices)
    duplicates_excluded = len(incoming) - accepted_count
    duplicate_within_batch = max(0, duplicates_excluded - duplicate_existing)

    accepted = incoming.loc[accepted_indices, existing.columns].copy()
    combined = pd.concat([existing, accepted], ignore_index=True)

    return {
        "events": combined,
        "accepted_batch": accepted.reset_index(drop=True),
        "incoming_rows": int(len(incoming)),
        "accepted_rows": int(len(accepted)),
        "duplicates_excluded": int(duplicates_excluded),
        "existing_rows": int(len(existing)),
        "result_rows": int(len(combined)),
        "identity_columns": identity_columns,
        "identity_strategy": "sha256_composite_fingerprint",
        "identity_warning": (
            "This fingerprint is not a stable source event ID. Legitimate "
            "events identical across the selected columns may be treated as duplicates."
        ),
    }

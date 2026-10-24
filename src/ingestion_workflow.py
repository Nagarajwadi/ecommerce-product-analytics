"""In-memory orchestration for event validation and incremental loading.

This workflow has no file or database I/O. It validates incoming rows first,
then applies the existing composite-fingerprint deduplication prototype only
to valid rows. Rejected rows are kept separate from duplicate counts.
"""
from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from src.incremental_loading import DEFAULT_IDENTITY_COLUMNS, process_incremental_batch
from src.rejected_records import (
    DEFAULT_REQUIRED_COLUMNS,
    DEFAULT_VALID_EVENT_TYPES,
    classify_event_batch,
)


def run_ingestion_workflow(
    existing_events: pd.DataFrame,
    incoming_batch: pd.DataFrame,
    identity_columns: Iterable[str] = DEFAULT_IDENTITY_COLUMNS,
    required_columns: Iterable[str] = DEFAULT_REQUIRED_COLUMNS,
    valid_event_types: Iterable[str] = DEFAULT_VALID_EVENT_TYPES,
) -> dict[str, object]:
    """Validate, deduplicate, and reconcile a batch entirely in memory.

    Existing and incoming DataFrames must have the same ordered columns.
    Invalid rows are excluded before duplicate detection. The composite
    fingerprint is only a prototype identity strategy; it can classify two
    legitimate but identical events as duplicates.
    """
    if list(existing_events.columns) != list(incoming_batch.columns):
        raise ValueError("Existing and incoming batches must have identical column order.")

    existing = existing_events.copy(deep=True)
    incoming = incoming_batch.copy(deep=True)

    validation = classify_event_batch(
        incoming,
        required_columns=required_columns,
        valid_event_types=valid_event_types,
    )
    valid_batch = validation["accepted"]

    incremental = process_incremental_batch(
        existing,
        valid_batch,
        identity_columns=identity_columns,
    )

    received_rows = int(validation["received_rows"])
    valid_rows = int(validation["accepted_rows"])
    rejected_rows = int(validation["rejected_rows"])
    duplicates_excluded = int(incremental["duplicates_excluded"])
    newly_accepted_rows = int(incremental["accepted_rows"])
    result_rows = int(incremental["result_rows"])
    existing_rows = int(incremental["existing_rows"])

    reconciliation_passed = (
        received_rows == rejected_rows + duplicates_excluded + newly_accepted_rows
        and result_rows == existing_rows + newly_accepted_rows
        and valid_rows == duplicates_excluded + newly_accepted_rows
    )
    if not reconciliation_passed:
        raise ValueError("Ingestion reconciliation failed.")

    return {
        "events": incremental["events"],
        "accepted_batch": incremental["accepted_batch"],
        "rejected": validation["rejected"],
        "received_rows": received_rows,
        "valid_rows": valid_rows,
        "rejected_rows": rejected_rows,
        "duplicates_excluded": duplicates_excluded,
        "accepted_rows": newly_accepted_rows,
        "existing_rows": existing_rows,
        "result_rows": result_rows,
        "reconciliation_passed": True,
        "identity_strategy": incremental["identity_strategy"],
        "identity_warning": incremental["identity_warning"],
        "reconciliation": {
            "received_rows": received_rows,
            "rejected_rows": rejected_rows,
            "duplicates_excluded": duplicates_excluded,
            "newly_accepted_rows": newly_accepted_rows,
            "existing_rows": existing_rows,
            "result_rows": result_rows,
        },
    }

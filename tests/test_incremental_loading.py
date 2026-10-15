import pandas as pd
import pytest

from src.incremental_loading import process_incremental_batch


COLUMNS = [
    "user_id", "timestamp", "session_id", "event_name", "product_id",
    "category", "price", "quantity", "device", "country",
    "traffic_source", "experiment_group",
]


def row(user="u1", timestamp="2026-01-01T10:00:00", event="app_open"):
    return {
        "user_id": user, "timestamp": timestamp, "session_id": "s1",
        "event_name": event, "product_id": None, "category": None,
        "price": None, "quantity": None, "device": "mobile",
        "country": "India", "traffic_source": "organic",
        "experiment_group": "control",
    }


def frame(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def test_new_batch_rows_are_accepted_and_reconciled():
    existing = frame([row()])
    incoming = frame([row("u2", "2026-01-01T11:00:00")])

    result = process_incremental_batch(existing, incoming)

    assert result["incoming_rows"] == 1
    assert result["accepted_rows"] == 1
    assert result["duplicates_excluded"] == 0
    assert result["result_rows"] == 2
    assert len(result["events"]) == len(existing) + result["accepted_rows"]


def test_reprocessing_same_batch_is_idempotent():
    existing = frame([row()])
    incoming = frame([row("u2", "2026-01-01T11:00:00")])

    first = process_incremental_batch(existing, incoming)
    second = process_incremental_batch(first["events"], incoming)

    assert second["accepted_rows"] == 0
    assert second["duplicates_excluded"] == 1
    assert len(second["events"]) == len(first["events"])


def test_duplicate_rows_inside_batch_are_only_accepted_once():
    incoming = frame([
        row("u2", "2026-01-01T11:00:00"),
        row("u2", "2026-01-01T11:00:00"),
    ])

    result = process_incremental_batch(frame([]), incoming)

    assert result["accepted_rows"] == 1
    assert result["duplicates_excluded"] == 1


def test_inputs_are_not_mutated():
    existing = frame([row()])
    incoming = frame([row("u2", "2026-01-01T11:00:00")])
    existing_before = existing.copy(deep=True)
    incoming_before = incoming.copy(deep=True)

    process_incremental_batch(existing, incoming)

    pd.testing.assert_frame_equal(existing, existing_before)
    pd.testing.assert_frame_equal(incoming, incoming_before)


def test_missing_identity_column_is_rejected():
    existing = frame([row()]).drop(columns=["session_id"])

    with pytest.raises(ValueError, match="missing identity columns"):
        process_incremental_batch(existing, existing)


def test_column_mismatch_is_rejected():
    existing = frame([row()])
    incoming = frame([row()]).drop(columns=["country"])

    with pytest.raises(ValueError, match="identical column order"):
        process_incremental_batch(existing, incoming)


def test_identity_limitation_is_returned_to_caller():
    result = process_incremental_batch(frame([]), frame([row()]))

    assert result["identity_strategy"] == "sha256_composite_fingerprint"
    assert "not a stable source event ID" in result["identity_warning"]

import pandas as pd
import pytest

from src.ingestion_workflow import run_ingestion_workflow


COLUMNS = [
    "user_id", "timestamp", "session_id", "event_name", "product_id",
    "category", "price", "quantity", "device", "country",
    "traffic_source", "experiment_group",
]


def row(
    user="u1",
    timestamp="2026-01-01 10:00:00",
    event="app_open",
    session="s1",
):
    return {
        "user_id": user,
        "timestamp": timestamp,
        "session_id": session,
        "event_name": event,
        "product_id": None,
        "category": None,
        "price": None,
        "quantity": None,
        "device": "mobile",
        "country": "India",
        "traffic_source": "organic",
        "experiment_group": "control",
    }


def frame(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def test_mixed_batch_reconciles_valid_rejected_duplicate_and_new_rows():
    existing = frame([row()])
    incoming = frame([
        row(),  # duplicate of existing
        row(user="u2", timestamp="2026-01-01 11:00:00"),  # new valid row
        row(user="u3", timestamp="not-a-time"),  # rejected
        row(user="u4", timestamp="2026-01-01 12:00:00", event="unknown"),  # rejected
    ])

    result = run_ingestion_workflow(existing, incoming)

    assert result["received_rows"] == 4
    assert result["valid_rows"] == 2
    assert result["rejected_rows"] == 2
    assert result["duplicates_excluded"] == 1
    assert result["accepted_rows"] == 1
    assert result["result_rows"] == 2
    assert result["reconciliation_passed"] is True
    assert result["received_rows"] == (
        result["rejected_rows"]
        + result["duplicates_excluded"]
        + result["accepted_rows"]
    )
    assert len(result["rejected"]) == 2
    assert len(result["accepted_batch"]) == 1


def test_duplicate_inside_incoming_batch_is_counted_once():
    duplicate = row(user="u2", timestamp="2026-01-01 11:00:00")
    result = run_ingestion_workflow(frame([]), frame([duplicate, duplicate]))

    assert result["received_rows"] == 2
    assert result["accepted_rows"] == 1
    assert result["duplicates_excluded"] == 1
    assert result["result_rows"] == 1


def test_invalid_rows_are_not_counted_as_duplicates():
    invalid = row(timestamp="bad-time")
    result = run_ingestion_workflow(frame([invalid]), frame([invalid]))

    assert result["rejected_rows"] == 1
    assert result["duplicates_excluded"] == 0
    assert result["accepted_rows"] == 0
    assert result["result_rows"] == 1


def test_empty_batch_reconciles_without_changing_existing_events():
    existing = frame([row()])
    result = run_ingestion_workflow(existing, frame([]))

    assert result["received_rows"] == 0
    assert result["accepted_rows"] == 0
    assert result["rejected_rows"] == 0
    assert result["duplicates_excluded"] == 0
    pd.testing.assert_frame_equal(result["events"], existing)


def test_inputs_are_not_mutated():
    existing = frame([row()])
    incoming = frame([
        row(user="u2", timestamp="2026-01-01 11:00:00"),
        row(user="u3", timestamp="bad-time"),
    ])
    existing_before = existing.copy(deep=True)
    incoming_before = incoming.copy(deep=True)

    run_ingestion_workflow(existing, incoming)

    pd.testing.assert_frame_equal(existing, existing_before)
    pd.testing.assert_frame_equal(incoming, incoming_before)


def test_column_mismatch_fails_before_processing():
    existing = frame([row()])
    incoming = frame([row()]).drop(columns=["country"])

    with pytest.raises(ValueError, match="identical column order"):
        run_ingestion_workflow(existing, incoming)


def test_identity_limitation_is_included_in_workflow_report():
    result = run_ingestion_workflow(frame([]), frame([row()]))

    assert result["identity_strategy"] == "sha256_composite_fingerprint"
    assert "not a stable source event ID" in result["identity_warning"]


def test_reconciliation_summary_matches_top_level_counts():
    result = run_ingestion_workflow(
        frame([]),
        frame([
            row(user="u1"),
            row(user="u2", timestamp="2026-01-01 11:00:00", event="bad"),
        ]),
    )

    assert result["reconciliation"]["received_rows"] == result["received_rows"]
    assert result["reconciliation"]["rejected_rows"] == result["rejected_rows"]
    assert result["reconciliation"]["newly_accepted_rows"] == result["accepted_rows"]
    assert result["reconciliation"]["result_rows"] == result["result_rows"]

import pandas as pd
import pytest

from src.rejected_records import classify_event_batch


COLUMNS = ["user_id", "session_id", "event_name", "timestamp", "payload"]


def make_batch(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def valid_row(user="u1", event="app_open", timestamp="2026-01-01 10:00:00"):
    return {
        "user_id": user,
        "session_id": f"s-{user}",
        "event_name": event,
        "timestamp": timestamp,
        "payload": "preserve-me",
    }


def test_valid_rows_are_accepted_and_reconciled():
    batch = make_batch([valid_row(), valid_row("u2", "purchase")])

    result = classify_event_batch(batch)

    assert result["accepted_rows"] == 2
    assert result["rejected_rows"] == 0
    assert result["received_rows"] == result["accepted_rows"] + result["rejected_rows"]
    assert result["reconciliation_passed"] is True


def test_missing_required_values_are_rejected_with_reason():
    row = valid_row()
    row["user_id"] = "  "
    result = classify_event_batch(make_batch([row]))

    assert result["accepted_rows"] == 0
    assert "missing_required:user_id" in result["rejected"].loc[0, "rejection_reasons"]


def test_invalid_timestamp_is_rejected_without_inference_warning():
    result = classify_event_batch(make_batch([valid_row(timestamp="not-a-timestamp")]))

    assert result["rejected_rows"] == 1
    assert "invalid_timestamp" in result["rejected"].loc[0, "rejection_reasons"]


def test_invalid_event_name_is_rejected():
    result = classify_event_batch(make_batch([valid_row(event="made_up_event")]))

    assert result["rejected_rows"] == 1
    assert "invalid_event_name" in result["rejected"].loc[0, "rejection_reasons"]


def test_multiple_reasons_are_reported_for_one_row():
    row = valid_row(event="made_up_event", timestamp="bad-time")
    row["session_id"] = None

    result = classify_event_batch(make_batch([row]))
    reasons = result["rejected"].loc[0, "rejection_reasons"]

    assert "missing_required:session_id" in reasons
    assert "invalid_timestamp" in reasons
    assert "invalid_event_name" in reasons
    assert result["rejected_rows"] == 1


def test_rejected_rows_preserve_original_values():
    row = valid_row(timestamp="bad-time")
    result = classify_event_batch(make_batch([row]))

    assert result["rejected"].loc[0, "timestamp"] == "bad-time"
    assert result["rejected"].loc[0, "payload"] == "preserve-me"


def test_missing_required_column_fails_batch_contract():
    batch = make_batch([valid_row()]).drop(columns=["session_id"])

    with pytest.raises(ValueError, match="missing required columns"):
        classify_event_batch(batch)


def test_duplicate_rows_are_not_misclassified_as_invalid():
    batch = make_batch([valid_row(), valid_row()])

    result = classify_event_batch(batch)

    assert result["accepted_rows"] == 2
    assert result["rejected_rows"] == 0
    assert "not_checked" in result["duplicate_policy"]


def test_input_frame_is_not_mutated():
    batch = make_batch([valid_row(timestamp="bad-time")])
    before = batch.copy(deep=True)

    classify_event_batch(batch)

    pd.testing.assert_frame_equal(batch, before)

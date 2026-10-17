import pandas as pd
import pytest

from etl.etl_pipeline import (
    REQUIRED_COLUMNS,
    transform_data,
    validate_data_quality,
    validate_event_types,
    validate_schema,
)


def sample_events():
    return pd.DataFrame([
        {
            "user_id": "u1",
            "timestamp": "2026-01-01 10:00:00",
            "session_id": "s1",
            "event_name": "app_open",
            "product_id": None,
            "category": None,
            "price": None,
            "quantity": None,
            "device": " mobile ",
            "country": "India",
            "traffic_source": "organic",
            "experiment_group": "control",
        },
        {
            "user_id": "u1",
            "timestamp": "2026-01-01 10:01:00",
            "session_id": "s1",
            "event_name": "purchase",
            "product_id": "p1",
            "category": "Electronics",
            "price": 10.0,
            "quantity": 1,
            "device": "mobile",
            "country": "India",
            "traffic_source": "organic",
            "experiment_group": "control",
        },
    ])


def test_schema_validation_accepts_required_columns():
    validate_schema(sample_events())


def test_schema_validation_rejects_missing_column():
    df = sample_events().drop(columns=["session_id"])
    with pytest.raises(ValueError, match="session_id"):
        validate_schema(df)


def test_event_validation_rejects_unrecognized_event():
    df = sample_events()
    df.loc[0, "event_name"] = "made_up_event"
    with pytest.raises(ValueError, match="Invalid event types"):
        validate_event_types(df)


def test_transform_deduplicates_trims_and_sorts_without_mutating_input():
    df = sample_events()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    original_rows = len(df)

    transformed = transform_data(df)

    assert len(transformed) == original_rows - 1
    assert transformed["timestamp"].is_monotonic_increasing
    assert transformed.loc[0, "device"] == "mobile"
    assert df.loc[0, "device"] == " mobile "


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("timestamp", None, "timestamp"),
        ("user_id", None, "user_id"),
        ("session_id", None, "session_id"),
        ("event_name", None, "event_name"),
        ("price", -1.0, "negative product prices"),
        ("quantity", 0, "invalid quantities"),
    ],
)
def test_data_quality_rejects_invalid_values(column, value, message):
    df = sample_events()
    df[column] = df[column].astype(object)
    df.loc[0, column] = value
    if column == "timestamp":
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    with pytest.raises(ValueError, match=message):
        validate_data_quality(df)


def test_data_quality_accepts_null_price_and_quantity_for_non_purchase_event():
    df = sample_events()
    validate_data_quality(df)

def test_transform_parses_documented_timestamp_format_without_warning():
    import warnings

    df = sample_events()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        transformed = transform_data(df)

    assert str(transformed["timestamp"].dtype).startswith("datetime64")
    assert transformed.loc[0, "timestamp"] == pd.Timestamp("2026-01-01 10:00:00")
    assert not [
        warning for warning in caught
        if "Could not infer format" in str(warning.message)
    ]


def test_transform_coerces_invalid_timestamp_for_quality_check():
    df = sample_events()
    df.loc[0, "timestamp"] = "not-a-timestamp"

    transformed = transform_data(df)

    assert transformed["timestamp"].isna().any()
    with pytest.raises(ValueError, match="invalid or missing timestamps"):
        validate_data_quality(transformed)

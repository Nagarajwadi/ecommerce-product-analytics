import pandas as pd
from pathlib import Path


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Processed dataset
DATA_PATH = BASE_DIR / "data" / "processed" / "clean_events.csv"


# Expected schema
REQUIRED_COLUMNS = {
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
}


# Valid event types
VALID_EVENTS = {
    "app_open",
    "search",
    "view_product",
    "add_to_cart",
    "checkout_start",
    "purchase",
}


def load_data():
    """Load the processed event dataset."""
    assert DATA_PATH.exists(), f"Dataset not found: {DATA_PATH}"
    return pd.read_csv(DATA_PATH)


def test_dataset_exists_and_is_not_empty():
    """The processed dataset should exist and contain rows."""
    df = load_data()

    assert len(df) > 0, "Processed dataset is empty"


def test_required_columns_exist():
    """All expected columns should exist."""
    df = load_data()

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    assert not missing_columns, (
        f"Missing required columns: {missing_columns}"
    )


def test_required_fields_have_no_nulls():
    """Critical identifier and event fields should not contain nulls."""
    df = load_data()

    required_fields = [
        "user_id",
        "session_id",
        "event_name",
    ]

    for column in required_fields:
        assert df[column].notna().all(), (
            f"Null values found in {column}"
        )


def test_event_names_are_valid():
    """Every event should belong to the expected event taxonomy."""
    df = load_data()

    invalid_events = set(df["event_name"].dropna().unique()) - VALID_EVENTS

    assert not invalid_events, (
        f"Invalid event types found: {invalid_events}"
    )


def test_timestamps_are_valid():
    """All event timestamps should be parseable."""
    df = load_data()

    timestamps = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    assert timestamps.notna().all(), (
        "Invalid or unparseable timestamps found"
    )


def test_prices_are_non_negative_when_present():
    """Prices should be non-negative whenever a price is recorded."""
    df = load_data()

    prices = df["price"].dropna()

    assert (prices >= 0).all(), (
        "Negative prices found"
    )


def test_quantities_are_positive_when_present():
    """Quantities should be positive whenever a quantity is recorded."""
    df = load_data()

    quantities = df["quantity"].dropna()

    assert (quantities > 0).all(), (
        "Zero or negative quantities found"
    )


def test_purchase_events_have_valid_prices():
    """Purchase events should have positive prices."""
    df = load_data()

    purchases = df[df["event_name"] == "purchase"]

    assert len(purchases) > 0, (
        "No purchase events found"
    )

    assert (purchases["price"] > 0).all(), (
        "Purchase events contain invalid prices"
    )


def test_user_ids_are_valid():
    """User IDs should follow the expected Uxxxxx format."""
    df = load_data()

    valid_user_ids = (
        df["user_id"]
        .astype(str)
        .str.match(r"^U\d{5}$")
    )

    assert valid_user_ids.all(), (
        "Invalid user IDs found"
    )


def test_session_ids_are_present():
    """Every event should belong to a session."""
    df = load_data()

    assert df["session_id"].astype(str).str.len().gt(0).all(), (
        "Empty session IDs found"
    )
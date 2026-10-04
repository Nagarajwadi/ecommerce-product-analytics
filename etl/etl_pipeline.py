from pathlib import Path

import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "raw_events.csv"
PROCESSED_FILE = (
    PROJECT_ROOT / "data" / "processed" / "clean_events.csv"
)


# ============================================================
# REQUIRED SCHEMA
# ============================================================

REQUIRED_COLUMNS = [
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


VALID_EVENT_TYPES = {
    "app_open",
    "search",
    "view_product",
    "add_to_cart",
    "checkout_start",
    "purchase",
}


# ============================================================
# EXTRACT
# ============================================================

def extract_data():
    """
    Read raw event data.
    """

    print("Extracting raw data...")

    df = pd.read_csv(RAW_FILE)

    print(f"Extracted {len(df):,} events.")

    return df


# ============================================================
# VALIDATION
# ============================================================

def validate_schema(df):
    """
    Validate that all required columns exist.
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    print("Schema validation: PASSED")


def validate_event_types(df):
    """
    Validate event names.
    """

    invalid_events = set(df["event_name"].dropna()) - VALID_EVENT_TYPES

    if invalid_events:
        raise ValueError(
            f"Invalid event types: {invalid_events}"
        )

    print("Event validation: PASSED")


# ============================================================
# TRANSFORM
# ============================================================

def transform_data(df):
    """
    Clean and transform the raw event data.
    """

    print("Transforming data...")

    df = df.copy()

    # --------------------------------------------------------
    # Convert timestamp
    # --------------------------------------------------------

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Remove duplicate rows
    # --------------------------------------------------------

    before = len(df)

    df = df.drop_duplicates()

    duplicates_removed = before - len(df)

    print(
        f"Duplicates removed: {duplicates_removed:,}"
    )

    # --------------------------------------------------------
    # Clean categorical columns
    # --------------------------------------------------------

    categorical_columns = [
        "event_name",
        "device",
        "country",
        "traffic_source",
        "experiment_group",
    ]

    for column in categorical_columns:
        df[column] = df[column].astype("string").str.strip()

    # --------------------------------------------------------
    # Sort events
    # --------------------------------------------------------

    df = df.sort_values(
        ["user_id", "timestamp", "session_id"]
    ).reset_index(drop=True)

    return df


# ============================================================
# DATA QUALITY CHECKS
# ============================================================

def validate_data_quality(df):
    """
    Run final data quality checks.
    """

    print("Running data quality checks...")

    # --------------------------------------------------------
    # Timestamp check
    # --------------------------------------------------------

    if df["timestamp"].isna().any():
        raise ValueError(
            "Found invalid or missing timestamps."
        )

    # --------------------------------------------------------
    # Required identifiers
    # --------------------------------------------------------

    for column in ["user_id", "session_id", "event_name"]:
        if df[column].isna().any():
            raise ValueError(
                f"Missing values found in {column}."
            )

    # --------------------------------------------------------
    # Price validation
    # --------------------------------------------------------

    invalid_prices = df[
        df["price"].notna()
        & (df["price"] < 0)
    ]

    if len(invalid_prices) > 0:
        raise ValueError(
            "Found negative product prices."
        )

    # --------------------------------------------------------
    # Quantity validation
    # --------------------------------------------------------

    invalid_quantity = df[
        df["quantity"].notna()
        & (df["quantity"] <= 0)
    ]

    if len(invalid_quantity) > 0:
        raise ValueError(
            "Found invalid quantities."
        )

    print("Data quality checks: PASSED")


# ============================================================
# LOAD
# ============================================================

def load_data(df):
    """
    Save cleaned data.
    """

    print("Loading processed data...")

    PROCESSED_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        PROCESSED_FILE,
        index=False,
    )

    print(
        f"Saved {len(df):,} events to:"
    )

    print(PROCESSED_FILE)


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print()
    print("====================================")
    print(" E-COMMERCE PRODUCT ANALYTICS ETL")
    print("====================================")
    print()

    # Extract
    df = extract_data()

    # Validate schema
    validate_schema(df)

    # Validate event types
    validate_event_types(df)

    # Transform
    df = transform_data(df)

    # Validate transformed data
    validate_data_quality(df)

    # Load
    load_data(df)

    print()
    print("ETL PIPELINE COMPLETE")
    print("=====================")


if __name__ == "__main__":
    main()
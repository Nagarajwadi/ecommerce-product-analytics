import sqlite3
from pathlib import Path

import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clean_events.csv"
)

DATABASE_FILE = (
    PROJECT_ROOT
    / "data"
    / "product_analytics.db"
)


# ============================================================
# DATABASE SETUP
# ============================================================

def create_database():

    print("Loading clean event data...")

    df = pd.read_csv(
        PROCESSED_FILE,
        parse_dates=["timestamp"],
    )

    print(
        f"Loaded {len(df):,} events."
    )

    print("Creating SQLite database...")

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    df.to_sql(
        "events",
        connection,
        if_exists="replace",
        index=False,
    )

    # --------------------------------------------------------
    # Create indexes
    # --------------------------------------------------------

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_user
        ON events(user_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_session
        ON events(session_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_timestamp
        ON events(timestamp)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_event_name
        ON events(event_name)
        """
    )

    connection.commit()

    # --------------------------------------------------------
    # Verify database
    # --------------------------------------------------------

    result = connection.execute(
        "SELECT COUNT(*) FROM events"
    ).fetchone()

    print(
        f"Database contains {result[0]:,} events."
    )

    connection.close()

    print()
    print(
        f"Database setup complete. "
        f"Saved to: {DATABASE_FILE}"
    )


if __name__ == "__main__":
    create_database()
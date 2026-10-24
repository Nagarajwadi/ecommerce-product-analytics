import sqlite3
from pathlib import Path

import pandas as pd


QUERY_PATH = Path(__file__).resolve().parents[1] / "sql" / "sequential_funnel.sql"


def run_query(rows):
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """CREATE TABLE events (
            user_id TEXT, timestamp TEXT, session_id TEXT,
            event_name TEXT, product_id TEXT, category TEXT,
            price REAL, quantity REAL, device TEXT, country TEXT,
            traffic_source TEXT, experiment_group TEXT
        )"""
    )
    connection.executemany(
        "INSERT INTO events (user_id, timestamp, session_id, event_name) VALUES (?, ?, ?, ?)",
        rows,
    )
    result = pd.read_sql_query(QUERY_PATH.read_text(encoding="utf-8"), connection)
    connection.close()
    return result


def test_sequential_funnel_counts_only_ordered_stages_within_session():
    result = run_query([
        ("u1", "2026-01-01 10:00:00", "s1", "app_open"),
        ("u1", "2026-01-01 10:01:00", "s1", "view_product"),
        ("u1", "2026-01-01 10:02:00", "s1", "add_to_cart"),
        ("u1", "2026-01-01 10:03:00", "s1", "checkout_start"),
        ("u1", "2026-01-01 10:04:00", "s1", "purchase"),
        # A separate session with events in the wrong order must not progress.
        ("u2", "2026-01-01 11:00:00", "s2", "view_product"),
        ("u2", "2026-01-01 11:01:00", "s2", "app_open"),
        ("u2", "2026-01-01 11:02:00", "s2", "add_to_cart"),
        # Another session exits after viewing a product.
        ("u3", "2026-01-01 12:00:00", "s3", "app_open"),
        ("u3", "2026-01-01 12:01:00", "s3", "view_product"),
    ])
    counts = result.set_index("stage")["sessions"].to_dict()
    assert counts == {
        "app_open": 3,
        "view_product": 2,
        "add_to_cart": 1,
        "checkout_start": 1,
        "purchase": 1,
    }
    view = result.loc[result["stage"] == "view_product"].iloc[0]
    assert view["conversion_from_previous_pct"] == round(2 / 3 * 100, 2)


def test_funnel_is_session_grain_not_user_grain():
    result = run_query([
        ("u1", "2026-01-01 10:00:00", "s1", "app_open"),
        ("u1", "2026-01-01 10:01:00", "s1", "view_product"),
        ("u1", "2026-01-01 11:00:00", "s2", "app_open"),
        ("u1", "2026-01-01 11:01:00", "s2", "view_product"),
    ])
    counts = result.set_index("stage")["sessions"].to_dict()
    assert counts["app_open"] == 2
    assert counts["view_product"] == 2

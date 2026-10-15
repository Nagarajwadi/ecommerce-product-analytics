import sqlite3
from pathlib import Path

import pandas as pd


QUERY_PATH = Path(__file__).resolve().parents[1] / "sql" / "engagement_conversion.sql"


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


def test_engagement_segments_are_mutually_exclusive_and_user_level():
    result = run_query([
        ("u1", "2026-01-01 10:00:00", "s1", "app_open"),
        ("u1", "2026-01-01 10:01:00", "s1", "purchase"),
        ("u2", "2026-01-01 10:00:00", "s2", "app_open"),
        ("u2", "2026-01-02 10:00:00", "s3", "view_product"),
        ("u3", "2026-01-01 10:00:00", "s4", "app_open"),
        ("u3", "2026-01-02 10:00:00", "s5", "view_product"),
        ("u3", "2026-01-03 10:00:00", "s6", "purchase"),
        ("u3", "2026-01-03 10:01:00", "s6", "purchase"),
    ])
    segments = result.set_index("segment")
    assert int(segments.loc["1 session", "users"]) == 1
    assert int(segments.loc["1 session", "purchasers"]) == 1
    assert int(segments.loc["2 sessions", "users"]) == 1
    assert int(segments.loc["2 sessions", "purchasers"]) == 0
    assert int(segments.loc["3+ sessions", "users"]) == 1
    assert int(segments.loc["3+ sessions", "purchasers"]) == 1
    assert int(result["users"].sum()) == 3
    assert int(result["purchasers"].sum()) == 2


def test_engagement_query_handles_missing_session_ids():
    result = run_query([
        ("u1", "2026-01-01 10:00:00", None, "app_open"),
        ("u1", "2026-01-01 10:01:00", None, "purchase"),
        ("u2", "2026-01-01 10:00:00", "s2", "app_open"),
    ])
    segments = result.set_index("segment")
    assert int(segments.loc["1 session", "users"]) == 2

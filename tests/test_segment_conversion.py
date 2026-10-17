import sqlite3
from pathlib import Path

import pandas as pd


QUERY_PATH = Path(__file__).resolve().parents[1] / "sql" / "segment_conversion.sql"


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
        """INSERT INTO events
           (user_id, timestamp, session_id, event_name, device, traffic_source)
           VALUES (?, ?, ?, ?, ?, ?)""",
        rows,
    )
    result = pd.read_sql_query(QUERY_PATH.read_text(encoding="utf-8"), connection)
    connection.close()
    return result


def test_segment_conversion_counts_each_user_once_per_dimension():
    result = run_query([
        ("u1", "2026-01-01 10:00:00", "s1", "app_open", "mobile", "paid_search"),
        ("u1", "2026-01-01 10:01:00", "s1", "purchase", "web", "email"),
        ("u2", "2026-01-01 10:00:00", "s2", "app_open", "web", "organic"),
        ("u2", "2026-01-01 10:01:00", "s2", "view_product", "web", "organic"),
        ("u3", "2026-01-01 10:00:00", "s3", "app_open", None, None),
    ])
    device = result[result["segment_type"] == "device"].set_index("segment")
    source = result[result["segment_type"] == "traffic_source"].set_index("segment")

    assert int(device.loc["mobile", "users"]) == 1
    assert int(device.loc["mobile", "purchasers"]) == 1
    assert int(device.loc["web", "users"]) == 1
    assert int(device.loc["web", "purchasers"]) == 0
    assert int(device.loc["unknown", "users"]) == 1
    assert int(source.loc["paid_search", "users"]) == 1
    assert int(source.loc["organic", "users"]) == 1
    assert int(source.loc["unknown", "users"]) == 1


def test_segment_rates_are_user_level_and_partition_totals_reconcile():
    result = run_query([
        ("u1", "2026-01-01 10:00:00", "s1", "app_open", "mobile", "paid_search"),
        ("u1", "2026-01-01 10:01:00", "s1", "purchase", "mobile", "paid_search"),
        ("u2", "2026-01-01 10:00:00", "s2", "app_open", "web", "organic"),
    ])
    for _, group in result.groupby("segment_type"):
        assert int(group["users"].sum()) == 2
        assert int(group["purchasers"].sum()) == 1

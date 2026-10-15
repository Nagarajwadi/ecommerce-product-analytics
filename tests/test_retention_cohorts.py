import sqlite3
from pathlib import Path

import pandas as pd


QUERY_PATH = Path(__file__).resolve().parents[1] / "sql" / "retention_cohorts.sql"


def run_query(rows):
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """CREATE TABLE events (
            user_id TEXT, timestamp TIMESTAMP, session_id TEXT,
            event_name TEXT, product_id TEXT, category TEXT,
            price REAL, quantity REAL, device TEXT, country TEXT,
            traffic_source TEXT, experiment_group TEXT
        )"""
    )
    connection.executemany(
        "INSERT INTO events (user_id, timestamp, event_name) VALUES (?, ?, ?)",
        rows,
    )
    result = pd.read_sql_query(QUERY_PATH.read_text(encoding="utf-8"), connection)
    connection.close()
    return result


def test_cohort_retention_excludes_users_without_full_horizon():
    result = run_query([
        ("early", "2026-06-01 09:00:00", "app_open"),
        ("early", "2026-06-02 09:00:00", "app_open"),
        ("early", "2026-06-08 09:00:00", "app_open"),
        ("early", "2026-07-01 09:00:00", "app_open"),
        ("late", "2026-06-20 09:00:00", "app_open"),
        ("late", "2026-06-21 09:00:00", "app_open"),
        ("late", "2026-06-27 09:00:00", "app_open"),
        ("latest", "2026-07-05 09:00:00", "app_open"),
    ])
    june = result.loc[result["cohort_month"] == "2026-06"].iloc[0]
    assert june["cohort_users"] == 2
    assert june["d1_eligible_users"] == 2
    assert june["d1_users"] == 2
    assert june["d30_eligible_users"] == 1
    assert june["d30_users"] == 1
    assert june["d30_retention_pct"] == 100.0


def test_d30_is_null_when_no_cohort_users_have_matured():
    result = run_query([
        ("u1", "2026-06-20 09:00:00", "app_open"),
        ("u1", "2026-06-21 09:00:00", "app_open"),
        ("u2", "2026-06-25 09:00:00", "app_open"),
        ("u2", "2026-06-26 09:00:00", "app_open"),
    ])
    june = result.loc[result["cohort_month"] == "2026-06"].iloc[0]
    assert june["d30_eligible_users"] == 0
    assert pd.isna(june["d30_retention_pct"])

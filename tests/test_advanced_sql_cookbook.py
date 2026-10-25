import re
import sqlite3
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
COOKBOOK_PATH = ROOT / "sql" / "advanced_sql_cookbook.sql"


def load_query(number):
    """Extract one numbered SQL query, excluding its heading and comments."""
    source = COOKBOOK_PATH.read_text(encoding="utf-8")
    markers = list(re.finditer(r"(?m)^-- ([1-7])\.", source))

    for index, marker in enumerate(markers):
        if int(marker.group(1)) != number:
            continue

        end = (
            markers[index + 1].start()
            if index + 1 < len(markers)
            else len(source)
        )
        section = source[marker.end():end]

        # The first line is the remainder of the numbered heading.
        lines = [
            line for line in section.splitlines()[1:]
            if not line.lstrip().startswith("--")
        ]
        query = "\n".join(lines).strip()
        if not query:
            raise AssertionError(f"Query {number} is empty")
        return query

    raise AssertionError(f"Query {number} was not found")

@pytest.fixture
def connection():
    """Use an isolated database; never open the project database."""
    db = sqlite3.connect(":memory:")
    db.execute(
        """
        CREATE TABLE events (
            user_id TEXT,
            timestamp TEXT,
            session_id TEXT,
            event_name TEXT,
            product_id TEXT,
            category TEXT,
            price REAL,
            quantity REAL,
            device TEXT,
            country TEXT,
            traffic_source TEXT,
            experiment_group TEXT
        )
        """
    )
    try:
        yield db
    finally:
        db.close()


def insert_events(connection, events):
    connection.executemany(
        """
        INSERT INTO events (
            user_id, timestamp, session_id, event_name,
            price, quantity, device, traffic_source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        events,
    )


def run_query(connection, number):
    return connection.execute(load_query(number)).fetchall()


def test_query_1_counts_event_presence_per_user(connection):
    insert_events(
        connection,
        [
            ("u1", "2026-01-01 09:00:00", "s1", "app_open",
             None, None, "mobile", "search"),
            ("u1", "2026-01-01 09:01:00", "s1", "view_product",
             None, None, "mobile", "search"),
            ("u1", "2026-01-01 09:02:00", "s1", "add_to_cart",
             None, None, "mobile", "search"),
            ("u2", "2026-01-01 10:00:00", "s2", "app_open",
             None, None, "desktop", "email"),
            ("u2", "2026-01-01 10:05:00", "s2", "purchase",
             10.0, 1, "desktop", "email"),
            ("u3", "2026-01-01 11:00:00", "s3", "view_product",
             None, None, "mobile", "social"),
        ],
    )

    row = run_query(connection, 1)[0]

    # users, opened, viewed, carted, checked out, purchased
    assert row == (3, 2, 2, 1, 0, 1)


def test_query_2_calculates_daily_and_rolling_revenue(connection):
    insert_events(
        connection,
        [
            ("u1", "2026-01-01 09:00:00", "s1", "purchase",
             10.0, 2, "mobile", "search"),
            ("u1", "2026-01-02 09:00:00", "s2", "app_open",
             None, None, "mobile", "search"),
            ("u2", "2026-01-03 09:00:00", "s3", "purchase",
             5.0, 1, "desktop", "email"),
        ],
    )

    rows = run_query(connection, 2)

    assert [row[0] for row in rows] == [
        "2026-01-01", "2026-01-02", "2026-01-03"
    ]
    assert [row[1] for row in rows] == [20.0, 0, 5.0]
    assert [row[2] for row in rows] == [20.0, 20.0, 25.0]


def test_query_3_calculates_channel_metrics(connection):
    insert_events(
        connection,
        [
            ("u1", "2026-01-01 09:00:00", "s1", "app_open",
             None, None, "mobile", "search"),
            ("u1", "2026-01-01 09:01:00", "s1", "purchase",
             10.0, 2, "mobile", "search"),
            ("u2", "2026-01-01 10:00:00", "s2", "view_product",
             None, None, "desktop", "search"),
            ("u3", "2026-01-01 11:00:00", "s3", "purchase",
             5.0, 3, "mobile", "social"),
        ],
    )

    rows = run_query(connection, 3)
    by_source = {row[0]: row[1:] for row in rows}

    # users, purchasers, purchaser rate (%), revenue
    assert by_source["search"] == (2, 1, 50.0, 20.0)
    assert by_source["social"] == (1, 1, 100.0, 15.0)


def test_query_4_selects_latest_event_per_user(connection):
    insert_events(
        connection,
        [
            ("u1", "2026-01-01 09:00:00", "s1", "app_open",
             None, None, "mobile", "search"),
            ("u1", "2026-01-01 09:05:00", "s1", "purchase",
             12.0, 1, "mobile", "search"),
            ("u2", "2026-01-01 10:00:00", "s2", "app_open",
             None, None, "desktop", "email"),
            ("u2", "2026-01-01 10:03:00", "s2", "view_product",
             None, None, "desktop", "email"),
        ],
    )

    rows = run_query(connection, 4)
    by_user = {row[0]: row[1:] for row in rows}

    assert by_user["u1"] == (
        "2026-01-01 09:05:00", "purchase", "mobile", "search"
    )
    assert by_user["u2"] == (
        "2026-01-01 10:03:00", "view_product", "desktop", "email"
    )


def test_query_5_summarizes_sessions_by_user_and_session_id(connection):
    insert_events(
        connection,
        [
            ("u1", "2026-01-01 09:00:00", "shared", "app_open",
             None, None, "mobile", "search"),
            ("u1", "2026-01-01 09:01:00", "shared", "purchase",
             10.0, 1, "mobile", "search"),
            ("u1", "2026-01-01 10:00:00", "s2", "app_open",
             None, None, "mobile", "search"),
            # The same session_id can belong to a different user.
            ("u2", "2026-01-01 09:02:00", "shared", "app_open",
             None, None, "desktop", "email"),
            ("u2", "2026-01-01 09:03:00", "shared", "view_product",
             None, None, "desktop", "email"),
        ],
    )

    rows = run_query(connection, 5)
    by_user = {row[0]: row[1:] for row in rows}

    # sessions, average events per session, purchasing sessions
    assert by_user["u1"] == (2, 1.5, 1)
    assert by_user["u2"] == (1, 2.0, 0)


@pytest.mark.parametrize("number", range(1, 8))
def test_cookbook_query_can_be_extracted(number):
    query = load_query(number)
    assert query.upper().startswith(("WITH", "SELECT"))

def test_query_7_ranks_category_revenue_and_handles_ties(connection):
    connection.executemany(
        """
        INSERT INTO events (
            user_id, timestamp, session_id, event_name, product_id,
            category, price, quantity, device, country,
            traffic_source, experiment_group
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "u1", "2026-01-01 09:00:00", "s1", "purchase",
                "p1", "Sports", 100.0, 2, "mobile", "US",
                "search", None,
            ),
            (
                "u2", "2026-01-01 09:01:00", "s2", "purchase",
                "p2", "Grocery", 50.0, 4, "mobile", "US",
                "search", None,
            ),
            (
                "u3", "2026-01-01 09:02:00", "s3", "purchase",
                "p3", "Books", 100.0, 1, "desktop", "US",
                "email", None,
            ),
            (
                "u4", "2026-01-01 09:03:00", "s4", "purchase",
                "p4", None, 999.0, 1, "mobile", "US",
                "search", None,
            ),
            (
                "u5", "2026-01-01 09:04:00", "s5", "view_product",
                "p5", "Beauty", 500.0, 1, "mobile", "US",
                "search", None,
            ),
        ],
    )

    rows = run_query(connection, 7)
    by_category = {row[0]: row[1:] for row in rows}

    # Columns: revenue, row_num, revenue_rank, dense_rank.
    assert by_category["Grocery"] == (200.0, 1, 1, 1)
    assert by_category["Sports"] == (200.0, 2, 1, 1)
    assert by_category["Books"] == (100.0, 3, 3, 2)

    # Uncategorised purchases and non-purchase events are excluded.
    assert None not in by_category
    assert "Beauty" not in by_category
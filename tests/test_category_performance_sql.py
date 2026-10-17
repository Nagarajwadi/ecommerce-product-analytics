import sqlite3
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
QUERY_PATH = ROOT / "sql" / "category_performance.sql"


@pytest.fixture
def category_results():
    """Run the category query against a small, isolated SQLite fixture."""
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE events (
            user_id TEXT,
            event_name TEXT,
            category TEXT,
            price REAL,
            quantity REAL
        )
        """
    )

    connection.executemany(
        """
        INSERT INTO events (user_id, event_name, category, price, quantity)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("u1", "view_product", "Sports", None, None),
            ("u1", "add_to_cart", "Sports", None, None),
            ("u1", "purchase", "Sports", 100.0, 2),
            # The same user purchases in a second category.
            ("u1", "purchase", "Grocery", 25.0, 1),
            ("u2", "purchase", "Grocery", 10.0, 3),
            ("u3", "view_product", "Beauty", None, None),
            # Events without a category should not appear in the output.
            ("u4", "purchase", None, 999.0, 1),
            # Irrelevant event types should not affect category counts.
            ("u5", "search", "Sports", None, None),
        ],
    )

    query = QUERY_PATH.read_text(encoding="utf-8")
    try:
        columns = [
            row[0] for row in connection.execute(query).description
        ]
        rows = connection.execute(query).fetchall()
        yield {
            row[0]: dict(zip(columns, row))
            for row in rows
        }
    finally:
        connection.close()


def test_category_query_returns_expected_event_counts(category_results):
    assert category_results["Sports"]["product_view_events"] == 1
    assert category_results["Sports"]["add_to_cart_events"] == 1
    assert category_results["Sports"]["purchase_events"] == 1
    assert category_results["Grocery"]["purchase_events"] == 2
    assert category_results["Beauty"]["product_view_events"] == 1


def test_purchase_revenue_uses_price_times_quantity(category_results):
    assert category_results["Sports"]["purchase_event_revenue"] == 200.0
    assert category_results["Grocery"]["purchase_event_revenue"] == 55.0


def test_category_purchasing_users_can_overlap(category_results):
    summed_category_users = sum(
        row["purchasing_users"] for row in category_results.values()
    )
    assert summed_category_users == 3

    # Across all categories, u1, u2, and no other categorized purchasers
    # are represented: u1 appears in both Sports and Grocery.
    assert category_results["Sports"]["purchasing_users"] == 1
    assert category_results["Grocery"]["purchasing_users"] == 2


def test_uncategorized_purchases_are_excluded(category_results):
    assert None not in category_results
    assert sum(
        row["purchase_events"] for row in category_results.values()
    ) == 3


def test_query_file_exists():
    assert QUERY_PATH.is_file()


def test_daily_join_reconciles_purchase_events_and_revenue():
    """The daily aggregate join must preserve purchase totals."""
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE events (
            user_id TEXT,
            timestamp TEXT,
            event_name TEXT,
            price REAL,
            quantity REAL
        )
        """
    )
    connection.executemany(
        """
        INSERT INTO events (user_id, timestamp, event_name, price, quantity)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("u1", "2026-01-01 09:00:00", "app_open", None, None),
            ("u1", "2026-01-01 09:05:00", "purchase", 10.0, 2),
            ("u2", "2026-01-02 10:00:00", "view_product", None, None),
            ("u2", "2026-01-02 10:05:00", "purchase", 5.0, 3),
            ("u3", "2026-01-03 11:00:00", "app_open", None, None),
        ],
    )

    cookbook = (
        ROOT / "sql" / "advanced_sql_cookbook.sql"
    ).read_text(encoding="utf-8")
    marker = "-- 6. Daily engagement joined to daily purchase metrics."
    query = cookbook.split(marker, 1)[1]
    query = query[query.index("WITH daily_activity AS"):].strip()

    try:
        daily_rows = connection.execute(query).fetchall()
        assert len(daily_rows) == 3

        # Columns: date, total events, active users, purchases,
        # purchasing users, purchase-event revenue.
        assert daily_rows[0][3:] == (1, 1, 20.0)
        assert daily_rows[1][3:] == (1, 1, 15.0)
        assert daily_rows[2][3:] == (0, 0, 0.0)

        raw_count, raw_revenue = connection.execute(
            """
            SELECT COUNT(*), SUM(price * quantity)
            FROM events
            WHERE event_name = 'purchase'
            """
        ).fetchone()
        assert sum(row[3] for row in daily_rows) == raw_count
        assert round(sum(row[5] for row in daily_rows), 2) == raw_revenue
    finally:
        connection.close()

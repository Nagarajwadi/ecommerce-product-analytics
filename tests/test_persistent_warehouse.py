import json
import sqlite3

import pandas as pd
import pytest

from src.persistent_warehouse import (
    SCHEMA_VERSION,
    get_checkpoint,
    initialize_warehouse,
    persist_batch,
)


@pytest.fixture
def connection():
    conn = sqlite3.connect(":memory:")
    initialize_warehouse(conn)
    try:
        yield conn
    finally:
        conn.close()


def sample_events():
    return pd.DataFrame(
        [
            {
                "user_id": "u1",
                "session_id": "s1",
                "event_name": "app_open",
                "timestamp": "2026-01-01 10:00:00",
                "payload": "keep-this",
            },
            {
                "user_id": "u2",
                "session_id": "s2",
                "event_name": "purchase",
                "timestamp": "2026-01-01 10:05:00",
                "payload": "also-keep",
            },
        ]
    )


def create_v1_database(connection):
    """Create a small legacy v1 schema for migration tests."""
    connection.executescript(
        """
        CREATE TABLE warehouse_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        INSERT INTO warehouse_metadata (key, value)
        VALUES ('schema_version', '1');

        CREATE TABLE ingestion_batches (
            batch_id TEXT PRIMARY KEY,
            content_sha256 TEXT NOT NULL,
            row_count INTEGER NOT NULL CHECK (row_count >= 0),
            completed_at TEXT NOT NULL
        );

        CREATE TABLE raw_event_batches (
            batch_id TEXT NOT NULL,
            row_number INTEGER NOT NULL CHECK (row_number >= 0),
            event_json TEXT NOT NULL,
            PRIMARY KEY (batch_id, row_number),
            FOREIGN KEY (batch_id)
                REFERENCES ingestion_batches(batch_id)
                ON DELETE CASCADE
        );

        INSERT INTO ingestion_batches
            (batch_id, content_sha256, row_count, completed_at)
        VALUES
            ('batch-z', 'hash-z', 1, '2026-01-01T00:00:00.000Z'),
            ('batch-a', 'hash-a', 1, '2026-01-01T00:00:00.000Z');

        INSERT INTO raw_event_batches (batch_id, row_number, event_json)
        VALUES
            ('batch-z', 0, '{"event_name":"app_open"}'),
            ('batch-a', 0, '{"event_name":"purchase"}');
        """
    )


def test_initialize_creates_schema_and_is_safe_to_repeat(connection):
    initialize_warehouse(connection)
    initialize_warehouse(connection)

    version = connection.execute(
        "SELECT value FROM warehouse_metadata WHERE key = 'schema_version'"
    ).fetchone()[0]

    assert version == str(SCHEMA_VERSION)
    columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(ingestion_batches)"
        ).fetchall()
    }
    assert "sequence_number" in columns


def test_persist_batch_stores_rows_and_checkpoint_atomically(connection):
    events = sample_events()

    result = persist_batch(connection, "batch-001", events)

    assert result["status"] == "persisted"
    assert result["row_count"] == 2
    assert result["sequence_number"] == 1

    stored = connection.execute(
        """
        SELECT row_number, event_json
        FROM raw_event_batches
        WHERE batch_id = ?
        ORDER BY row_number
        """,
        ("batch-001",),
    ).fetchall()

    assert len(stored) == 2
    assert json.loads(stored[0][1])["payload"] == "keep-this"
    assert json.loads(stored[1][1])["event_name"] == "purchase"

    checkpoint = get_checkpoint(connection)
    assert checkpoint["batch_id"] == "batch-001"
    assert checkpoint["row_count"] == 2
    assert checkpoint["sequence_number"] == 1


def test_replaying_same_batch_id_and_content_is_idempotent(connection):
    events = sample_events()

    first = persist_batch(connection, "batch-001", events)
    second = persist_batch(connection, "batch-001", events)

    assert first["status"] == "persisted"
    assert second["status"] == "already_completed"
    assert connection.execute(
        "SELECT COUNT(*) FROM ingestion_batches"
    ).fetchone()[0] == 1
    assert connection.execute(
        "SELECT COUNT(*) FROM raw_event_batches"
    ).fetchone()[0] == 2


def test_reusing_batch_id_with_different_content_fails(connection):
    persist_batch(connection, "batch-001", sample_events())
    changed = sample_events()
    changed.loc[0, "payload"] = "different-content"

    with pytest.raises(ValueError, match="different content"):
        persist_batch(connection, "batch-001", changed)

    assert connection.execute(
        "SELECT COUNT(*) FROM raw_event_batches"
    ).fetchone()[0] == 2


def test_failed_batch_insert_rolls_back_ledger_and_rows(connection):
    events = sample_events()

    connection.execute(
        """
        CREATE TRIGGER fail_second_row
        BEFORE INSERT ON raw_event_batches
        WHEN NEW.row_number = 1
        BEGIN
            SELECT RAISE(ABORT, 'simulated insert failure');
        END;
        """
    )

    with pytest.raises(
        sqlite3.IntegrityError, match="simulated insert failure"
    ):
        persist_batch(connection, "batch-failed", events)

    assert connection.execute(
        "SELECT COUNT(*) FROM ingestion_batches WHERE batch_id = 'batch-failed'"
    ).fetchone()[0] == 0
    assert connection.execute(
        "SELECT COUNT(*) FROM raw_event_batches WHERE batch_id = 'batch-failed'"
    ).fetchone()[0] == 0
    assert get_checkpoint(connection) is None


def test_empty_batch_can_be_persisted_and_replayed(connection):
    empty = pd.DataFrame(columns=["user_id", "event_name"])

    first = persist_batch(connection, "empty-batch", empty)
    second = persist_batch(connection, "empty-batch", empty)

    assert first["status"] == "persisted"
    assert first["row_count"] == 0
    assert second["status"] == "already_completed"


def test_batch_id_must_be_nonempty(connection):
    with pytest.raises(ValueError, match="non-empty string"):
        persist_batch(connection, " ", sample_events())


def test_duplicate_column_names_are_rejected(connection):
    events = pd.DataFrame([["u1", "u2"]], columns=["user_id", "user_id"])

    with pytest.raises(ValueError, match="unique column names"):
        persist_batch(connection, "batch-001", events)


def test_batch_and_checkpoint_survive_connection_reopen(tmp_path):
    database_path = tmp_path / "warehouse_test.sqlite"

    first_connection = sqlite3.connect(database_path)
    initialize_warehouse(first_connection)
    result = persist_batch(
        first_connection,
        "batch-durable-001",
        sample_events(),
    )
    assert result["status"] == "persisted"
    first_connection.close()

    second_connection = sqlite3.connect(database_path)
    try:
        checkpoint = get_checkpoint(second_connection)
        assert checkpoint is not None
        assert checkpoint["batch_id"] == "batch-durable-001"
        assert checkpoint["row_count"] == 2
        assert checkpoint["sequence_number"] == 1

        replay = persist_batch(
            second_connection,
            "batch-durable-001",
            sample_events(),
        )
        assert replay["status"] == "already_completed"
        assert second_connection.execute(
            "SELECT COUNT(*) FROM raw_event_batches"
        ).fetchone()[0] == 2
    finally:
        second_connection.close()


def test_v1_schema_migrates_and_preserves_existing_batches():
    connection = sqlite3.connect(":memory:")
    try:
        create_v1_database(connection)

        initialize_warehouse(connection)

        version = connection.execute(
            "SELECT value FROM warehouse_metadata WHERE key = 'schema_version'"
        ).fetchone()[0]
        assert version == str(SCHEMA_VERSION)

        batches = connection.execute(
            """
            SELECT batch_id, sequence_number
            FROM ingestion_batches
            ORDER BY sequence_number
            """
        ).fetchall()
        # Equal timestamps are ordered deterministically by batch_id.
        assert batches == [("batch-a", 1), ("batch-z", 2)]

        assert connection.execute(
            "SELECT COUNT(*) FROM raw_event_batches"
        ).fetchone()[0] == 2

        checkpoint = get_checkpoint(connection)
        assert checkpoint["batch_id"] == "batch-z"
        assert checkpoint["sequence_number"] == 2
    finally:
        connection.close()


def test_checkpoint_uses_sequence_not_timestamp_or_batch_id(connection):
    persist_batch(connection, "z-first", sample_events())
    persist_batch(connection, "a-second", sample_events().iloc[:1])

    # Simulate identical timestamps; the sequence remains authoritative.
    connection.execute(
        "UPDATE ingestion_batches SET completed_at = '2026-01-01T00:00:00.000Z'"
    )

    checkpoint = get_checkpoint(connection)
    assert checkpoint["batch_id"] == "a-second"
    assert checkpoint["sequence_number"] == 2


@pytest.mark.parametrize("bad_version", ["not-a-number", "99"])
def test_invalid_or_unsupported_schema_version_fails(bad_version):
    connection = sqlite3.connect(":memory:")
    try:
        initialize_warehouse(connection)
        connection.execute(
            "UPDATE warehouse_metadata SET value = ? WHERE key = 'schema_version'",
            (bad_version,),
        )
        connection.commit()

        with pytest.raises(ValueError, match="schema version"):
            initialize_warehouse(connection)

        stored_version = connection.execute(
            "SELECT value FROM warehouse_metadata WHERE key = 'schema_version'"
        ).fetchone()[0]
        assert stored_version == bad_version
    finally:
        connection.close()


def test_failed_v1_migration_rolls_back_schema_changes():
    connection = sqlite3.connect(":memory:")
    try:
        create_v1_database(connection)

        # Force the schema-version update to fail after the migration work.
        connection.execute(
            """
            CREATE TRIGGER fail_schema_version_update
            BEFORE UPDATE ON warehouse_metadata
            WHEN NEW.key = 'schema_version'
            BEGIN
                SELECT RAISE(ABORT, 'simulated migration failure');
            END;
            """
        )
        connection.commit()

        with pytest.raises(
            sqlite3.IntegrityError, match="simulated migration failure"
        ):
            initialize_warehouse(connection)

        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(ingestion_batches)"
            ).fetchall()
        }
        assert "sequence_number" not in columns

        version = connection.execute(
            "SELECT value FROM warehouse_metadata WHERE key = 'schema_version'"
        ).fetchone()[0]
        assert version == "1"

        assert connection.execute(
            "SELECT COUNT(*) FROM ingestion_batches"
        ).fetchone()[0] == 2
    finally:
        connection.close()

def test_initialize_rejects_active_transaction_without_rolling_it_back(
    connection,
):
    connection.execute(
        "CREATE TABLE caller_work (value TEXT)"
    )
    connection.commit()

    connection.execute("BEGIN")
    connection.execute(
        "INSERT INTO caller_work (value) VALUES ('preserve-me')"
    )

    with pytest.raises(RuntimeError, match="no active transaction"):
        initialize_warehouse(connection)

    assert connection.in_transaction
    assert connection.execute(
        "SELECT value FROM caller_work"
    ).fetchone()[0] == "preserve-me"

    connection.rollback()


def test_persist_batch_rejects_active_transaction_without_rolling_it_back(
    connection,
):
    connection.execute(
        "CREATE TABLE caller_work (value TEXT)"
    )
    connection.commit()

    connection.execute("BEGIN")
    connection.execute(
        "INSERT INTO caller_work (value) VALUES ('preserve-me')"
    )

    with pytest.raises(RuntimeError, match="no active transaction"):
        persist_batch(connection, "batch-guard-test", sample_events())

    assert connection.in_transaction
    assert connection.execute(
        "SELECT value FROM caller_work"
    ).fetchone()[0] == "preserve-me"
    assert connection.execute(
        """
        SELECT COUNT(*) FROM ingestion_batches
        WHERE batch_id = 'batch-guard-test'
        """
    ).fetchone()[0] == 0

    connection.rollback()

def test_v2_schema_missing_sequence_column_is_rejected_without_data_loss():
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(
            """
            CREATE TABLE warehouse_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            INSERT INTO warehouse_metadata (key, value)
            VALUES ('schema_version', '2');

            CREATE TABLE ingestion_batches (
                batch_id TEXT PRIMARY KEY,
                content_sha256 TEXT NOT NULL,
                row_count INTEGER NOT NULL CHECK (row_count >= 0),
                completed_at TEXT NOT NULL
            );

            CREATE TABLE raw_event_batches (
                batch_id TEXT NOT NULL,
                row_number INTEGER NOT NULL CHECK (row_number >= 0),
                event_json TEXT NOT NULL,
                PRIMARY KEY (batch_id, row_number),
                FOREIGN KEY (batch_id)
                    REFERENCES ingestion_batches(batch_id)
                    ON DELETE CASCADE
            );

            INSERT INTO ingestion_batches
                (batch_id, content_sha256, row_count, completed_at)
            VALUES
                ('preserve-batch', 'known-hash', 1, '2026-01-01T00:00:00.000Z');

            INSERT INTO raw_event_batches (batch_id, row_number, event_json)
            VALUES ('preserve-batch', 0, '{"event_name":"app_open"}');
            """
        )
        connection.commit()

        with pytest.raises(ValueError, match="schema"):
            initialize_warehouse(connection)

        assert connection.execute(
            "SELECT COUNT(*) FROM ingestion_batches WHERE batch_id = 'preserve-batch'"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM raw_event_batches WHERE batch_id = 'preserve-batch'"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT value FROM warehouse_metadata WHERE key = 'schema_version'"
        ).fetchone()[0] == "2"
    finally:
        connection.close()

def test_v2_schema_missing_foreign_key_is_rejected_without_data_loss():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript(
            """
            CREATE TABLE warehouse_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            INSERT INTO warehouse_metadata (key, value)
            VALUES ('schema_version', '2');

            CREATE TABLE ingestion_batches (
                batch_id TEXT PRIMARY KEY,
                content_sha256 TEXT NOT NULL,
                row_count INTEGER NOT NULL CHECK (row_count >= 0),
                completed_at TEXT NOT NULL,
                sequence_number INTEGER
            );

            CREATE UNIQUE INDEX uq_ingestion_sequence
                ON ingestion_batches(sequence_number);

            -- Intentionally omit the required foreign key.
            CREATE TABLE raw_event_batches (
                batch_id TEXT NOT NULL,
                row_number INTEGER NOT NULL CHECK (row_number >= 0),
                event_json TEXT NOT NULL,
                PRIMARY KEY (batch_id, row_number)
            );

            INSERT INTO ingestion_batches
                (batch_id, content_sha256, row_count,
                 completed_at, sequence_number)
            VALUES
                ('preserve-batch', 'known-hash', 1,
                 '2026-01-01T00:00:00.000Z', 1);

            INSERT INTO raw_event_batches
                (batch_id, row_number, event_json)
            VALUES
                ('preserve-batch', 0, '{"event_name":"app_open"}');
            """
        )
        connection.commit()

        with pytest.raises(ValueError, match="ON DELETE CASCADE"):
            initialize_warehouse(connection)

        # Initialization must reject the schema without deleting data.
        assert connection.execute(
            """
            SELECT content_sha256, row_count, sequence_number
            FROM ingestion_batches
            WHERE batch_id = 'preserve-batch'
            """
        ).fetchone() == ("known-hash", 1, 1)

        assert connection.execute(
            """
            SELECT event_json
            FROM raw_event_batches
            WHERE batch_id = 'preserve-batch' AND row_number = 0
            """
        ).fetchone() == ('{"event_name":"app_open"}',)

        assert connection.execute(
            "SELECT value FROM warehouse_metadata "
            "WHERE key = 'schema_version'"
        ).fetchone()[0] == "2"

    finally:
        connection.close()


def test_v2_schema_missing_table_is_rejected_without_recreating_it():
    connection = sqlite3.connect(":memory:")

    try:
        initialize_warehouse(connection)

        persist_batch(
            connection,
            "preserve-batch",
            pd.DataFrame([{"event_name": "app_open"}]),
        )

        connection.execute("DROP TABLE raw_event_batches")
        connection.commit()

        with pytest.raises(ValueError, match="missing tables"):
            initialize_warehouse(connection)

        table = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'raw_event_batches'
            """
        ).fetchone()
        assert table is None

        assert connection.execute(
            """
            SELECT value FROM warehouse_metadata
            WHERE key = 'schema_version'
            """
        ).fetchone()[0] == str(SCHEMA_VERSION)

        assert connection.execute(
            """
            SELECT batch_id FROM ingestion_batches
            WHERE batch_id = 'preserve-batch'
            """
        ).fetchone()[0] == "preserve-batch"

    finally:
        connection.close()
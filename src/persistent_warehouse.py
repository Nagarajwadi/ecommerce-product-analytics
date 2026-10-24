"""SQLite persistence prototype for incremental analytics ingestion.

The caller supplies an explicit SQLite connection. This module never opens
a database path itself and never chooses the existing ShopFlow database.

Batch-level idempotency is based on batch IDs and content hashes. It does
not establish stable event-level identity across different batches.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any
import re
import pandas as pd


SCHEMA_VERSION = 2

def _validate_v2_schema(connection: sqlite3.Connection) -> None:
    """Reject incomplete v2 schemas without altering existing data."""
    required_columns = {
        "warehouse_metadata": {
            "key": {"notnull": False},
            "value": {"notnull": True},
        },
        "ingestion_batches": {
            "batch_id": {"notnull": False},
            "content_sha256": {"notnull": True},
            "row_count": {"notnull": True},
            "completed_at": {"notnull": True},
            "sequence_number": {"notnull": False},
        },
        "raw_event_batches": {
            "batch_id": {"notnull": True},
            "row_number": {"notnull": True},
            "event_json": {"notnull": True},
        },
    }

    expected_primary_keys = {
        "warehouse_metadata": ["key"],
        "ingestion_batches": ["batch_id"],
        "raw_event_batches": ["batch_id", "row_number"],
    }

    table_sql = {}

    for table_name, required in required_columns.items():
        info = connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        columns = {row[1]: row for row in info}
        missing = set(required) - set(columns)

        if missing:
            raise ValueError(
                f"Invalid warehouse schema: table {table_name!r} "
                f"is missing columns {sorted(missing)}."
            )

        for column_name, rules in required.items():
            if rules["notnull"] and not columns[column_name][3]:
                raise ValueError(
                    f"Invalid warehouse schema: "
                    f"{table_name}.{column_name} must be NOT NULL."
                )

        primary_key = [
            row[1]
            for row in sorted(info, key=lambda item: item[5])
            if row[5] > 0
        ]

        if primary_key != expected_primary_keys[table_name]:
            raise ValueError(
                f"Invalid warehouse schema: table {table_name!r} "
                f"must have primary key {expected_primary_keys[table_name]}."
            )

        definition = connection.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()

        if definition is None or definition[0] is None:
            raise ValueError(
                f"Invalid warehouse schema: definition for "
                f"table {table_name!r} is missing."
            )

        table_sql[table_name] = re.sub(
            r"\s+", "", definition[0]
        ).lower()

    # SQLite's PRAGMA table_info does not expose CHECK expressions.
    required_checks = {
        "ingestion_batches": "check(row_count>=0)",
        "raw_event_batches": "check(row_number>=0)",
    }

    for table_name, expression in required_checks.items():
        if expression not in table_sql[table_name]:
            raise ValueError(
                f"Invalid warehouse schema: table {table_name!r} "
                f"must enforce {expression}."
            )

    # Require the event table to reference the batch ledger and cascade
    # deletions as specified by the schema.
    foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(raw_event_batches)"
    ).fetchall()

    valid_foreign_key = any(
        row[2] == "ingestion_batches"
        and row[3] == "batch_id"
        and row[4] == "batch_id"
        and row[6].upper() == "CASCADE"
        for row in foreign_keys
    )

    if not valid_foreign_key:
        raise ValueError(
            "Invalid warehouse schema: raw_event_batches must reference "
            "ingestion_batches(batch_id) with ON DELETE CASCADE."
        )

    indexes = connection.execute(
        "PRAGMA index_list(ingestion_batches)"
    ).fetchall()

    sequence_index_is_valid = False

    for index in indexes:
        index_name = index[1]
        is_unique = bool(index[2])
        is_partial = bool(index[4]) if len(index) > 4 else False

        index_columns = [
            row[2]
            for row in connection.execute(
                f'PRAGMA index_info("{index_name.replace(chr(34), chr(34) * 2)}")'
            ).fetchall()
        ]

        if (
            is_unique
            and not is_partial
            and index_columns == ["sequence_number"]
        ):
            sequence_index_is_valid = True
            break

    if not sequence_index_is_valid:
        raise ValueError(
            "Invalid warehouse schema: a unique index on "
            "sequence_number is required."
        )

    invalid_sequences = connection.execute(
        """
        SELECT
            COUNT(*) - COUNT(sequence_number),
            COUNT(DISTINCT sequence_number)
        FROM ingestion_batches
        """
    ).fetchone()

    total_batches = connection.execute(
        "SELECT COUNT(*) FROM ingestion_batches"
    ).fetchone()[0]

    if (
        invalid_sequences[0] != 0
        or invalid_sequences[1] != total_batches
    ):
        raise ValueError(
            "Invalid warehouse schema: sequence_number values "
            "must be non-null and unique."
        )

def _canonical_value(value: Any) -> Any:
    """Convert common pandas/numpy values into JSON-safe values."""
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _batch_payload(events: pd.DataFrame) -> tuple[str, str]:
    """Return a deterministic JSON representation and SHA-256 hash."""
    rows = [
        [_canonical_value(value) for value in row]
        for row in events.itertuples(index=False, name=None)
    ]
    payload = json.dumps(
        {"columns": list(events.columns), "rows": rows},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return payload, hashlib.sha256(payload.encode("utf-8")).hexdigest()


def initialize_warehouse(connection: sqlite3.Connection) -> None:
    """Create or migrate the prototype schema without deleting stored data."""
    if connection.in_transaction:
        raise RuntimeError(
            "initialize_warehouse() requires a connection with no active transaction."
        )
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        connection.execute("BEGIN IMMEDIATE")
        existing_tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                """
            ).fetchall()
        }

        required_tables = {
            "warehouse_metadata",
            "ingestion_batches",
            "raw_event_batches",
        }

        if existing_tables:
            missing_tables = required_tables - existing_tables
            if missing_tables:
                raise ValueError(
                    "Invalid warehouse schema: existing database is "
                    f"missing tables {sorted(missing_tables)}."
                )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS warehouse_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_batches (
                batch_id TEXT PRIMARY KEY,
                content_sha256 TEXT NOT NULL,
                row_count INTEGER NOT NULL CHECK (row_count >= 0),
                completed_at TEXT NOT NULL DEFAULT (
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                )
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_event_batches (
                batch_id TEXT NOT NULL,
                row_number INTEGER NOT NULL CHECK (row_number >= 0),
                event_json TEXT NOT NULL,
                PRIMARY KEY (batch_id, row_number),
                FOREIGN KEY (batch_id)
                    REFERENCES ingestion_batches(batch_id)
                    ON DELETE CASCADE
            )
            """
        )

        version_row = connection.execute(
            "SELECT value FROM warehouse_metadata WHERE key = 'schema_version'"
        ).fetchone()

        if version_row is None:
            # A database with batch tables but no version marker is treated as
            # legacy v1 unless its sequence column already exists.
            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(ingestion_batches)"
                ).fetchall()
            }
            if "sequence_number" not in columns:
                _migrate_v1_to_v2(connection)

            connection.execute(
                """
                INSERT INTO warehouse_metadata (key, value)
                VALUES ('schema_version', ?)
                """,
                (str(SCHEMA_VERSION),),
            )
        else:
            raw_version = version_row[0]
            try:
                version = int(raw_version)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid warehouse schema version {raw_version!r}."
                ) from exc

            if version == 1:
                _migrate_v1_to_v2(connection)
                connection.execute(
                    """
                    UPDATE warehouse_metadata
                    SET value = ?
                    WHERE key = 'schema_version'
                    """,
                    (str(SCHEMA_VERSION),),
                )
            elif version != SCHEMA_VERSION:
                raise ValueError(
                    f"Unsupported warehouse schema version {raw_version!r}; "
                    f"expected 1 or {SCHEMA_VERSION}."
                )

        _validate_v2_schema(connection)
        connection.commit()
    except Exception:
        if connection.in_transaction:
            connection.rollback()
        raise


def _migrate_v1_to_v2(connection: sqlite3.Connection) -> None:
    """Add a durable sequence to legacy batches in deterministic order."""
    columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(ingestion_batches)"
        ).fetchall()
    }

    if "sequence_number" not in columns:
        connection.execute(
            "ALTER TABLE ingestion_batches ADD COLUMN sequence_number INTEGER"
        )

    legacy_batches = connection.execute(
        """
        SELECT batch_id
        FROM ingestion_batches
        ORDER BY completed_at ASC, batch_id ASC
        """
    ).fetchall()

    for sequence_number, (batch_id,) in enumerate(legacy_batches, start=1):
        connection.execute(
            """
            UPDATE ingestion_batches
            SET sequence_number = ?
            WHERE batch_id = ?
            """,
            (sequence_number, batch_id),
        )

    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
            idx_ingestion_batches_sequence
        ON ingestion_batches(sequence_number)
        """
    )


def persist_batch(
    connection: sqlite3.Connection,
    batch_id: str,
    events: pd.DataFrame,
) -> dict[str, Any]:
    """Persist a batch and checkpoint atomically.

    Replaying an identical batch ID and payload is a no-op. Reusing a batch
    ID for different content raises ValueError. The caller should pass
    validated rows; validation and event-level deduplication are separate.
    """
    if connection.in_transaction:
        raise RuntimeError(
            "persist_batch() requires a connection with no active transaction."
        )
    if not isinstance(batch_id, str) or not batch_id.strip():
        raise ValueError("batch_id must be a non-empty string.")

    if not isinstance(events, pd.DataFrame):
        raise TypeError("events must be a pandas DataFrame.")

    if not events.columns.is_unique:
        raise ValueError("events must have unique column names.")

    _, content_hash = _batch_payload(events)
    columns = list(events.columns)
    rows = [
        {
            column: _canonical_value(value)
            for column, value in zip(columns, row)
        }
        for row in events.itertuples(index=False, name=None)
    ]

    try:
        # Acquire the write reservation before checking for an existing batch.
        connection.execute("BEGIN IMMEDIATE")

        existing = connection.execute(
            """
            SELECT content_sha256, row_count
            FROM ingestion_batches
            WHERE batch_id = ?
            """,
            (batch_id,),
        ).fetchone()

        if existing is not None:
            if existing[0] != content_hash or existing[1] != len(events):
                raise ValueError(
                    f"Batch ID {batch_id!r} already exists with different content."
                )

            connection.commit()
            return {
                "batch_id": batch_id,
                "row_count": len(events),
                "status": "already_completed",
                "content_sha256": content_hash,
            }

        sequence_number = connection.execute(
            """
            SELECT COALESCE(MAX(sequence_number), 0) + 1
            FROM ingestion_batches
            """
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO ingestion_batches (
                batch_id, content_sha256, row_count, sequence_number
            )
            VALUES (?, ?, ?, ?)
            """,
            (batch_id, content_hash, len(events), sequence_number),
        )

        connection.executemany(
            """
            INSERT INTO raw_event_batches (batch_id, row_number, event_json)
            VALUES (?, ?, ?)
            """,
            [
                (
                    batch_id,
                    row_number,
                    json.dumps(
                        row,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                        default=str,
                    ),
                )
                for row_number, row in enumerate(rows)
            ],
        )

        connection.commit()
    except Exception:
        if connection.in_transaction:
            connection.rollback()
        raise

    return {
        "batch_id": batch_id,
        "row_count": len(events),
        "status": "persisted",
        "content_sha256": content_hash,
        "sequence_number": sequence_number,
    }


def get_checkpoint(connection: sqlite3.Connection) -> dict[str, Any] | None:
    """Return the most recently committed batch by durable sequence number."""
    row = connection.execute(
        """
        SELECT batch_id, row_count, content_sha256, completed_at, sequence_number
        FROM ingestion_batches
        ORDER BY sequence_number DESC
        LIMIT 1
        """
    ).fetchone()

    if row is None:
        return None

    return {
        "batch_id": row[0],
        "row_count": row[1],
        "content_sha256": row[2],
        "completed_at": row[3],
        "sequence_number": row[4],
    }
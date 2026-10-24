# Warehouse Layers Prototype

## Scope

`src/warehouse_layers.py` is an in-memory prototype of the three logical layers. It does not read or write files, create database tables, or modify the existing SQLite database.

## Contracts

- **Raw:** deep copy of the supplied source DataFrame; preserves source values for comparison.
- **Staging:** applies the current ETL schema/event checks, timestamp conversion, exact-row deduplication, categorical trimming, sorting, and data-quality validation.
- **Analytics daily events:** event counts grouped by event date and event name.
- **Analytics sessions:** one summary row per observed `session_id`, with first user ID, start/end timestamps, event count, and elapsed duration.

## Important limitations

- The current schema has no stable event identifier, so exact-row deduplication is not a substitute for event-key deduplication.
- Session grouping assumes `session_id` identifies a session globally; validate that assumption before production use.
- Session duration is elapsed time between first and last observed event, not a claim about inactivity timeout or full session length.
- The event date uses the timezone represented by the parsed timestamps. Define a canonical reporting timezone before production reporting.
- These are DataFrame outputs only. Persistence, incremental loading, idempotency, late-arriving-event handling, and source-to-target reconciliation remain future work.

## Test

Run `python -m pytest tests/test_warehouse_layers.py -q`. Tests use a small in-memory fixture and do not touch project data files or the SQLite database.

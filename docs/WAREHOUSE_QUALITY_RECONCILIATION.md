# Warehouse Quality and Reconciliation

## Purpose

`src/warehouse_quality.py` checks that the in-memory warehouse outputs agree with each other. It performs no file or database I/O.

## Checks

- Daily analytics event counts sum to the number of staging rows.
- Session-level event counts sum to the number of staging rows.
- Session summary rows equal the number of distinct session IDs in staging.
- Staging row count does not exceed raw row count (the current prototype can remove exact duplicates).

The function returns a compact count report when checks pass and raises `ValueError` with a mismatch description when they fail.

## Limits

These checks establish internal count consistency, not full business correctness. They do not prove that event IDs are unique, that session IDs are globally unique, or that the source data is complete. The source schema currently has no stable event identifier. No persisted tables or existing SQLite data are changed.

## Test

Run `python -m pytest tests/test_warehouse_quality.py -q`, then `python -m pytest -q`.

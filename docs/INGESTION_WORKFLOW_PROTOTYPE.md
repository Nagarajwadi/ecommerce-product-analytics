# In-Memory Ingestion Workflow Prototype

## Purpose

`src/ingestion_workflow.py` composes the record-classification and incremental-loading prototypes into one batch workflow. It is an in-memory design exercise and performs no file or database I/O.

## Workflow

1. Require the existing and incoming DataFrames to have identical ordered columns.
2. Validate incoming rows using `classify_event_batch`.
3. Keep invalid rows in a separate rejected DataFrame with reason codes.
4. Apply the existing composite-fingerprint deduplication only to valid rows.
5. Return the combined in-memory event DataFrame, newly accepted rows, rejected rows, and reconciliation counts.

## Reconciliation

The workflow checks both equations:

- `received_rows = rejected_rows + duplicates_excluded + newly_accepted_rows`
- `result_rows = existing_rows + newly_accepted_rows`

It also checks that `valid_rows = duplicates_excluded + newly_accepted_rows`. If a reconciliation equation fails, the workflow raises an error rather than returning a successful report.

## Important identity limitation

The current incremental loader uses a SHA-256 fingerprint of selected event fields. This is not a stable source event ID. Two legitimate events that are identical across those fields can be treated as duplicates. The report exposes this limitation. A production implementation should use a stable event ID and explicitly distinguish replayed IDs from same-ID/different-payload conflicts, as described in `docs/INGESTION_CONTRACT.md`.

## Safety boundaries

- No CSV reads or writes.
- No SQLite reads or writes.
- No Supabase or other external persistence.
- Input DataFrames are copied and must remain unchanged.
- This prototype does not implement durable quarantine, retry, late-arriving-event backfills, alerts, or recovery.

## Tests

Run the focused tests:

```bash
python -m pytest tests/test_ingestion_workflow.py -q
```

Then run the complete test suite:

```bash
python -m pytest -q
```

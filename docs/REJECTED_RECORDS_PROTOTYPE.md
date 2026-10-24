# Rejected-Record Handling Prototype

## Scope

`src/rejected_records.py` classifies a supplied DataFrame in memory. It does not read or write files or databases.

## Behavior

- Requires the configured columns to exist; a missing column fails the batch contract immediately.
- Checks required fields for null or blank values.
- Validates timestamps against the current documented format `%Y-%m-%d %H:%M:%S`.
- Checks event names against the allowed event set.
- Accumulates deterministic reason codes per rejected row.
- Preserves original source values in the rejected output and does not mutate the input.
- Reconciles `received_rows = accepted_rows + rejected_rows`.

## Duplicates versus invalid records

Duplicate/replay detection is intentionally separate. Identical valid rows are not rejected by this validator merely because they are identical. A later identity step must classify replayed IDs, same-ID/different-payload conflicts, and uncertain legacy fingerprints according to `docs/INGESTION_CONTRACT.md`.

## Limitations

This is a validation prototype, not a durable quarantine service. It does not persist rejected payloads, apply schema-version rules, enforce stable event IDs, or implement retries, alerts, retention, or operational recovery. The strict timestamp format must be adjusted if supported upstream formats change.

## Test

Run `python -m pytest tests/test_rejected_records.py -q`, then `python -m pytest -q`.

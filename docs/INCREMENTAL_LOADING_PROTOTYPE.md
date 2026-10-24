# Incremental Loading Prototype

## Scope

`src/incremental_loading.py` is an in-memory demonstration of accepting unseen rows from an incoming batch. It performs no file or database I/O and does not mutate caller-owned DataFrames.

## Identity strategy and limitation

The prototype computes a SHA-256 fingerprint from the configured composite of the available event columns. This makes repeat processing deterministic for the selected fields, but it is **not a stable source event ID**. Two legitimate events that happen to match across every selected field can collide and one may be excluded. Therefore, this behavior is appropriate only as a prototype for demonstrating batch idempotency, not as a production event-identity contract.

Before production use, prefer a stable event identifier generated at event collection time. If that is unavailable, the business must explicitly accept and document the risk of a composite-key strategy, including which columns define identity and which event types can legitimately repeat.

## Current behavior

- Existing records are retained.
- Incoming fingerprints already present in existing data are excluded.
- Repeated fingerprints within the same incoming batch are accepted once.
- A reconciliation report gives incoming, accepted, excluded, existing, and resulting row counts.
- Missing identity columns or incompatible column layouts raise `ValueError`.

## Not included

No persistence, watermark tracking, late-arriving-event policy, schema evolution, transaction management, or rejected-record quarantine is implemented. Do not treat this as production-ready incremental ingestion.

## Test

Run `python -m pytest tests/test_incremental_loading.py -q`, then `python -m pytest -q`.

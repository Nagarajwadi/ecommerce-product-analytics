# Event Identity and Ingestion Contract

## Status

**Design proposal only.** This document does not change the generated event schema, raw CSV, processed CSV, SQLite database, or production services. The current incremental loader remains an in-memory prototype and is not production-ready.

## 1. Event identity

### Preferred contract for newly collected events

Add a required `event_id` assigned once by the event producer when the event is created. It must be:
- Unique per logical event across users, sessions, event types, and time.
- Stable across retries, network replays, batch exports, and reprocessing.
- Preserved unchanged through raw, staging, and analytics layers.
- Validated as non-null and unique within each accepted dataset.

A retry must reuse the original `event_id`; it must not generate a new ID. UUID/ULID are possible formats, but the producer and ingestion service must agree on one format and generation point before implementation.

### Existing historical events

The current event schema does not contain a stable event ID. A hash of the current fields is only a composite fingerprint. Two legitimate events can share all those values, so it cannot safely establish true event identity. Do not silently promote the prototype fingerprint to a production primary key or delete historical rows based on it.

Before a migration, choose and document a backfill policy. A generated ID assigned to each historical row can identify that row going forward, but cannot identify whether two historical rows are retries of the same logical event. Preserve source rows and report this ambiguity instead of guessing.

## 2. Raw, staging, accepted, and rejected records

- **Raw input:** preserve each received batch unchanged, with a batch/run identifier and ingestion timestamp supplied by the ingestion process.
- **Staging:** validate schema and normalize fields without losing the raw source representation.
- **Accepted:** records that pass validation and identity checks.
- **Rejected/quarantined:** invalid records with a reason code, source batch/run ID, and enough original payload to investigate. Do not silently discard them.
- **Reconciliation:** report received = accepted + rejected, with duplicates reported separately and definitions made explicit. If duplicate deliveries are included in received, show both gross received and unique candidate counts so totals remain interpretable.

## 3. Idempotency

For events with `event_id`:
- A new ID is eligible for insertion.
- An existing ID with the same canonical payload is a replay; count it as a duplicate and do not insert another event.
- An existing ID with a different payload is an identity conflict. Quarantine it and alert/report the conflict; do not overwrite the earlier event automatically.
- Enforce uniqueness at the persistence layer as well as in application logic when persistence is eventually approved.

The current in-memory fingerprint prototype is suitable for demonstrating repeat-batch behavior only. It does not implement this contract.

## 4. Late-arriving and out-of-order events

Use event time for product analytics and ingestion time for pipeline operations. Do not assume the largest timestamp already seen means all earlier events have arrived.

Initial policy proposal:
- Accept valid late events within a configurable lookback window and recompute affected date/session aggregates.
- Track a high-water mark for operational progress, but replay a lookback interval rather than reading only timestamps greater than the last maximum.
- Route events older than the normal lookback to a late-event path for explicit review/backfill; do not silently discard them.
- Make reruns idempotent by `event_id`, and record the batch/run boundaries and counts.

The lookback duration and handling of very late events are business decisions; no duration is set in this design.

## 5. Timestamp contract

- Require a parseable event timestamp.
- For production, require timezone-aware timestamps or define an explicit source timezone and conversion rule.
- Store/compare normalized timestamps consistently (prefer UTC for event instants) and define a separate reporting timezone for daily metrics.
- Invalid or ambiguous timestamps must be rejected with a reason; they must not be coerced to null and then silently lost.
- Test supported timestamp formats explicitly rather than relying on pandas inference.

## 6. Schema and validation

Before persistence is introduced, specify:
- Required and nullable fields by event type.
- Accepted event names and categorical values.
- Numeric ranges and when price/quantity are expected to be absent versus required.
- Schema version and policy for added/renamed columns.
- Uniqueness, referential-integrity, and source-to-target reconciliation checks.

## 7. Implementation gates

Do not connect this prototype to the existing SQLite database or production Supabase until all of these are reviewed:
1. Stable `event_id` generation point and format agreed.
2. Historical-event backfill policy agreed.
3. Duplicate replay versus same-ID/different-payload conflict behavior tested.
4. Late-event lookback and backfill policy agreed.
5. Rejected-record retention and reconciliation semantics agreed.
6. Persistence design has a separate, isolated test database and explicit migration/recovery plan.
7. Tests pass and changes are reviewed before any merge or deployment.

## Scope boundary

This is a contract proposal, not an implemented ingestion pipeline. It makes no writes and changes no existing data.

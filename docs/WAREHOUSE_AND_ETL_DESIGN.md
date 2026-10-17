# Analytics Warehouse and ETL Design

## Current state

ShopFlow currently uses a synthetic event CSV, a cleaned event CSV, and a SQLite `events` table. This document specifies a next-step logical model; it does not execute DDL or mutate any database.

## Grain and logical star schema

| Model | Grain | Candidate key | Purpose |
|---|---|---|---|
| `fact_event` | One row per observed event | `event_id` (add to source if stable) | Event-level behavior |
| `fact_session` | One row per user session | `session_id` if globally unique; otherwise composite | Session engagement and conversion |
| `fact_order` | One row per purchase/order | Requires stable order identifier; do not assume event_id equals order_id | Revenue and purchasing |
| `dim_user` | One row per user | `user_id` | User/device/acquisition attributes, with history if needed |
| `dim_product` | One row per product | `product_id` | Category and product attributes |
| `dim_date` | One row per calendar date | `date_key` | Calendar rollups |

### Important modeling caveats

- Confirm the actual source columns and key uniqueness before building tables.
- A purchase event is not necessarily a unique order. A stable order ID is needed for reliable order-level metrics.
- Device and acquisition attributes can change over time; decide whether to snapshot them on the fact or use slowly changing dimensions.
- Keep event timestamps in a consistent timezone and define event-date derivation explicitly.
- Do not call first observed event "signup"; it is only first observed activity unless a signup timestamp exists.

## Layered pipeline

1. **Raw/landing:** immutable source extract plus ingestion timestamp and source file/batch identifier.
2. **Staging:** parse timestamps, standardize types, normalize event names, and quarantine malformed records.
3. **Analytics:** conformed dimensions and facts at documented grains.
4. **Marts:** funnel, cohort, channel, revenue and experimentation outputs.

## Incremental-load contract

- Use a stable source event ID or documented composite key for idempotent upserts.
- Track a high-water mark using a reliable ingestion timestamp; allow a lookback window for late events.
- Deduplicate deterministically and quarantine conflicting duplicate keys rather than silently choosing a row.
- Reconcile raw, accepted, rejected, and loaded counts per batch.
- Make each batch rerunnable without duplicating facts.
- Keep schema changes explicit and tested.

## Data-quality tests

- Required columns and types are present.
- Event identifiers are unique at the declared grain.
- `user_id`, `event_name`, and timestamps are non-null.
- Event names belong to an accepted set.
- Quantity and price are nonnegative where applicable.
- Dimension keys resolve for all fact rows or use an explicit unknown member.
- Daily event counts and purchase revenue reconcile between source and target within documented rules.
- Freshness and rejected-row thresholds are monitored.

## Safe implementation sequence

1. Inspect source schema and existing database without writes.
2. Prototype the model against a disposable copy or a new database path.
3. Add transformation tests and reconciliation tests.
4. Compare mart metrics with existing trusted SQL results.
5. Review migration and rollback plan before any database changes.

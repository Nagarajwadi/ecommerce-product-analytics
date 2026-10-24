# Analytics Metric Dictionary and Data Lineage

## Purpose

This document defines the current event data grain, keys, core metrics, and lineage for the ShopFlow synthetic analytics project. It describes the existing implementation and recommended contracts; it does not change or migrate the SQLite database.

## Source schema and grain

The source event dataset contains these columns:

`user_id`, `timestamp`, `session_id`, `event_name`, `product_id`, `category`, `price`, `quantity`, `device`, `country`, `traffic_source`, and `experiment_group`.

**Current grain:** one row per recorded event in the generated event stream. The schema does not currently include a stable `event_id` or `order_id`.

| Field | Current meaning | Key / quality notes |
|---|---|---|
| `user_id` | User associated with the event | Used to count unique users; required by current ETL checks |
| `timestamp` | Event time | Parsed to datetime; timezone contract should be explicitly defined |
| `session_id` | Session associated with the event | Used for ordered session funnels and distinct-session engagement; confirm global uniqueness before treating it as a key |
| `event_name` | Event type | Accepted values: `app_open`, `search`, `view_product`, `add_to_cart`, `checkout_start`, `purchase` |
| `product_id` | Product associated with the event, when present | Nullable for events that do not refer to a product |
| `category` | Product category, when present | Confirm consistency against a product dimension before modeling |
| `price` | Event-associated product price | Revenue calculation currently multiplies price by quantity for purchase events; currency and price semantics should be documented |
| `quantity` | Event-associated quantity | Current ETL rejects values <= 0 when non-null |
| `device` | Device value recorded on the event | Can vary across events for the same user; segment SQL uses the earliest observed event's value |
| `country` | Country value recorded on the event | May change or be missing; define event-time versus user-profile semantics |
| `traffic_source` | Traffic source recorded on the event | Segment SQL uses the earliest observed event's value; not validated campaign attribution |
| `experiment_group` | Experiment assignment group recorded on the event | Validate assignment stability, exposure, and missingness before causal interpretation |

## Metric definitions

| Metric | Definition | Grain and caveats |
|---|---|---|
| Total events | Count of rows in the event table | Event-level; sensitive to duplicate or repeated events |
| Active/observed users | Distinct non-null `user_id` values in the selected event set | Does not necessarily mean signed-up or active within a standard product analytics definition |
| Purchasers | Distinct users with at least one `purchase` event | User-level; a purchase event is not guaranteed to equal an order |
| User purchase conversion | Distinct purchasers divided by distinct observed users in the same defined population | Specify population and observation window for comparisons |
| Purchase-event count | Number of rows with `event_name = 'purchase'` | Event count, not verified order count |
| Event-associated revenue | Sum of `price * quantity` over purchase-event rows | Requires confirmation that price and quantity represent purchase-line values and that currency is consistent |
| Revenue per purchaser | Event-associated revenue divided by distinct purchasers | User-level denominator; depends on the revenue definition above |
| Sequential funnel conversion | Sessions reaching a stage in the defined event order divided by sessions reaching the prior stage | Session-level; stage events must occur in order within the same session |
| Sequential funnel drop-off | Prior-stage sessions minus sessions reaching the next ordered stage | Session-level; report count and rate together |
| D1/D7/D30 exact-day retention | Users active on exactly day 1/7/30 after first observed activity divided by users with enough observation time | First observed activity is not signup; use maturity-eligible denominators |
| Device/source conversion | Purchasers divided by users assigned to a device/source from their earliest observed event | Descriptive user-level segmentation, not causal effect or validated attribution |
| Engagement conversion | Users with a purchase divided by users grouped by distinct observed session count | Descriptive association; observation-window length and reverse causality can bias comparisons |

## Current data lineage

```text
data/raw/raw_events.csv
        |
        v
etl/etl_pipeline.py
  - schema and event-name checks
  - timestamp parsing
  - exact-row deduplication
  - categorical trimming
  - required-field / price / quantity checks
        |
        v
data/processed/clean_events.csv
        |
        v
sql/setup_database.py
  - loads cleaned CSV into SQLite table: events
        |
        +--> sql/sequential_funnel.sql
        +--> sql/segment_conversion.sql
        +--> sql/engagement_conversion.sql
        +--> sql/retention_cohorts.sql
        |
        v
dashboard/app.py
  - displays funnel, segmentation, retention, revenue and experiment summaries
  - analytic SQL queries use read-only SQLite connections
```

**Operational warning:** `sql/setup_database.py` loads the `events` table with `if_exists="replace"`. Do not run it against the existing local database as a routine validation step; it can replace the current table. Keep validation read-only or use a disposable copy/new path.

## Known gaps and recommended contracts

1. **Stable event identity:** add or derive a documented stable event key before implementing reliable incremental upserts. A composite key must be validated against actual data and source guarantees.
2. **Order identity:** add a stable order identifier if true order count, order-level average order value, refunds, or order deduplication are required. Do not infer an order ID from `session_id` or event row position.
3. **Timezone:** define the source timezone and whether reporting dates use UTC or a business timezone.
4. **Event-specific required fields:** specify which event types require `product_id`, `price`, or `quantity`, rather than assuming these are required for every event.
5. **Experiment integrity:** verify one assignment per user, eligible population, exposure event, analysis window, and sample-ratio mismatch before interpreting lift causally.
6. **Incremental lineage:** record batch ID, ingestion timestamp, source filename, accepted/rejected row counts, and load status in a future production pipeline.
7. **Reconciliation:** compare raw, accepted, rejected, and loaded row counts; reconcile purchase-event revenue using documented null and currency rules.

## Safe validation

- Use synthetic in-memory fixtures for unit tests.
- Query the existing SQLite database with a read-only connection.
- Do not regenerate source data or replace the `events` table during documentation or validation.
- Keep all development on `product-analytics-skillset-roadmap` until review and tests pass.

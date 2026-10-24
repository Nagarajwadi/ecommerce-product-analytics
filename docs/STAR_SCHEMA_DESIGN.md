# Logical Star Schema Design

## Status and safety

This is a proposed logical model for the ShopFlow synthetic event dataset. It is documentation only: no DDL has been executed and no database has been migrated. Validate candidate keys and source semantics before implementing physical tables.

## Source facts and limitations

The current source event fields are `user_id`, `timestamp`, `session_id`, `event_name`, `product_id`, `category`, `price`, `quantity`, `device`, `country`, `traffic_source`, and `experiment_group`. There is no stable `event_id` or verified `order_id` in the current schema.

## Proposed model

### Fact and dimension grains

| Model | Grain | Candidate key | Main measures / attributes | Key caveat |
|---|---|---|---|---|
| `fact_event` | One row per source event | Stable `event_id`; not currently present | event timestamp, event type, quantity, price, event-level context | Add/validate stable event identity before incremental upserts |
| `fact_session` | One row per session | `session_id` only if globally unique; otherwise composite key | start/end timestamps, event count, stage flags, session duration | Define sessionization and treatment of missing IDs/timeouts |
| `fact_purchase_event` | One row per purchase event | Stable event key | event-associated revenue, product, quantity | Not an order fact unless source confirms each purchase event maps to an order |
| `dim_user` | One row per user for current-state view | `user_id` | user attributes and known signup metadata, if available | Device/source may change and are currently event attributes |
| `dim_product` | One row per product | `product_id` | category, product attributes | Current event table has category but product dimension source should be validated |
| `dim_date` | One row per calendar date | `date_key` | day, week, month, quarter, year | Choose reporting timezone before deriving date keys |
| `dim_device` (optional) | One row per normalized device value | `device_key` | canonical device label | Useful only if standardization/mapping is needed |
| `dim_traffic_source` (optional) | One row per normalized source value | `traffic_source_key` | canonical source label | Does not replace campaign ID or attribution rules |

A true `fact_order` should be added only when a stable order identifier and order semantics are available. Do not infer orders from session IDs or purchase-event row counts.

## Relationships

- `fact_event.user_id` references `dim_user.user_id` when the user is known.
- `fact_event.product_id` references `dim_product.product_id` when the event relates to a product.
- `fact_event.event_date_key` references `dim_date.date_key` after the reporting timezone is fixed.
- `fact_session` may link to a user dimension and session start date; it should not replace event-level detail.
- Optional device and traffic-source dimensions can be referenced by surrogate keys if standardized dimensions are introduced. Preserve event-time values when they can vary within a user's journey.

## Metric ownership

| Metric family | Preferred source model | Definition note |
|---|---|---|
| Event volume and event sequence | `fact_event` | Count source events at event grain |
| Ordered funnel | `fact_event` grouped by session | Require ordered stage timestamps within one session |
| Session engagement | `fact_session` | Distinct sessions depend on stable session identity |
| User conversion | User-level aggregate over `fact_event` | Define eligible population and observation window |
| Purchase-event revenue | `fact_purchase_event` or purchase rows in `fact_event` | Validate price/quantity and currency semantics |
| Order count / order AOV | `fact_order` | Not reliable until order ID and order semantics exist |
| Cohort retention | `fact_event` plus user cohort date | Current first-observed activity is not signup date |

## Implementation sequence

1. Profile source columns and key uniqueness using read-only queries.
2. Define and validate event identity and session identity.
3. Implement transformations against a disposable fixture or a new database path, never by replacing the existing local database.
4. Add tests for uniqueness, foreign-key resolution, null handling, accepted values, and reconciliation.
5. Compare output counts and metric values with existing validated SQL.
6. Only then propose physical DDL and a migration/rollback plan.

## Acceptance criteria

- Every model has an explicit grain and documented key.
- Keys are validated against source guarantees rather than assumed from column names.
- User-, session-, event-, and order-level measures are not mixed.
- Unknown/missing dimension values have a defined policy.
- Metric definitions reconcile to source data under documented rules.
- Existing local SQLite data remains untouched during design and testing.

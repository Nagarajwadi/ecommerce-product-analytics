# Advanced SQL and Hive: Query Cookbook

## Purpose and scope

This guide documents advanced SQL examples for the ShopFlow synthetic
e-commerce event dataset. The examples support portfolio learning and are
not evidence of real business performance.

The local application uses SQLite. Selected Hive query logic was executed
successfully on Apache Hive 4.0.0 using an isolated synthetic ORC test table.
The external-table setup, S3 storage configuration, partition registration,
and production-scale execution have not been validated. Confirm syntax,
timestamp behavior, partition pruning, data types, and execution plans in
the intended environment before production use.

## Query cookbook

| File | Business question or technique | Interpretation notes |
|---|---|---|
| `sql/category_performance.sql` | Which categories have the most product views, cart events, purchases, purchasing users, and purchase-event revenue? | Event counts are not unique users. A user may purchase in multiple categories. |
| `sql/advanced_sql_cookbook.sql`, query 1 | How many users have performed each funnel event? | Event-presence flags do not prove event ordering or strict funnel conversion. |
| `sql/advanced_sql_cookbook.sql`, query 2 | What is daily purchase-event revenue and its rolling seven-row total? | The window operates over daily rows; missing calendar dates must be filled if a true seven-calendar-day window is required. |
| `sql/advanced_sql_cookbook.sql`, query 3 | How do users, purchasers, purchaser rate, and revenue vary by traffic source? | Purchaser rate is based on distinct users represented in each source group; validate attribution rules before treating it as channel effectiveness. |
| `sql/advanced_sql_cookbook.sql`, query 4 | What is each user's latest observed event? | Resolve ties on timestamps with a stable secondary sort key if deterministic tie-breaking is required. |
| `sql/advanced_sql_cookbook.sql`, query 5 | How many sessions does each user have, and how engaged are those sessions? | Validate whether `session_id` is globally unique; grouping by both session and user avoids assuming global uniqueness. |
| `sql/advanced_sql_cookbook.sql`, query 6 | How do daily activity and active users compare with purchases and revenue? | Both CTEs aggregate to one row per date before joining, avoiding raw-event row multiplication. |
| `sql/hive_product_analytics.sql` | How might channel and rolling-revenue analyses run over partitioned Hive data? | Examples require a configured Hive catalog and correctly populated date partitions. |

## Running the SQLite examples

From the repository root, with the project's Python environment active:

```bash
python sql/run_query.py category_performance.sql
```

The runner executes a SQL file as one query. Because the advanced cookbook
contains multiple independent statements, run its individual query blocks
separately rather than passing the entire cookbook to the runner.

The project database is an existing local artifact. Do not regenerate,
overwrite, or use it as a disposable test database. Run automated SQL tests
against an in-memory or temporary SQLite database.

## Reproducible validation and current evidence

The category query has a focused test module at
`tests/test_category_performance_sql.py`. It exercises the query against an
isolated in-memory fixture, including event counts, revenue arithmetic,
category overlap among purchasing users, and exclusion of uncategorized
purchases.

A read-only reconciliation of the current local synthetic dataset produced:

- 133,785 total events in the database.
- 4,770 purchase events with a category.
- 3,756 distinct purchasing users across those categorized purchases.
- 30,207,026.10 in purchase-event revenue across those categorized purchases.
- Ten categories in the category query output.

The daily join example returned 182 daily rows. Its daily purchase-event count
and revenue reconciled to the raw purchase-event query: 4,770 purchase events
and 30,207,026.10 in revenue. These figures describe the current synthetic
dataset and may change if the data changes. The currency denomination is not
specified here.

Category-level distinct purchasing-user counts are not additive: a user who
purchases in multiple categories appears once in each relevant category.
Therefore, summing those category-level counts can exceed the overall distinct
purchasing-user count.

### Query-plan observations

SQLite `EXPLAIN QUERY PLAN` for the category query reported use of
`idx_events_event_name`, plus temporary B-trees for grouping, distinct counts,
and sorting. This is evidence of the current plan, not proof that a new index
would improve performance.

Before adding an index, compare representative query latency and query plans
on a stable dataset. Account for the extra storage and write costs of indexes.
Re-check plans after meaningful changes in data volume, distribution, or
query predicates.


### Controlled index comparison

A controlled SQLite experiment compared the purchase-event aggregation query
on two separate in-memory copies of the current database. One copy retained
`idx_events_event_name`; the other had that index dropped. Both returned
4,770 purchase events, and `EXPLAIN QUERY PLAN` confirmed an index search in
the indexed copy and a full table scan in the unindexed copy.

| Configuration | Median runtime | Minimum runtime | Query plan |
|---|---:|---:|---|
| With `idx_events_event_name` | 0.3616 ms | 0.3497 ms | Covering index search |
| Without `idx_events_event_name` | 8.0144 ms | 6.8620 ms | Full table scan |

The observed median was approximately 22.16 times higher without the index
for this query and dataset. Measurements used 101 timed executions per
configuration after warm-up. The source database was opened read-only, and
the index removal occurred only in a separate in-memory copy.

These measurements are environment- and dataset-specific. They demonstrate
the value of this existing index for this particular selective aggregation;
they do not establish a general performance improvement for other queries or
larger workloads. Re-benchmark after material changes to data or environment.

## Join safety and metric definitions

- Aggregate each input to the intended join grain before joining when joining
  facts that can have multiple rows per key.
- Document the grain and expected cardinality for each join.
- Use `LEFT JOIN` when dates or entities in the left-hand result must remain
  visible without a matching row in the right-hand result.
- Apply `COALESCE` only when zero is the correct business interpretation of a
  missing aggregate; do not use it to conceal missing or invalid source data.
- Define revenue consistently as `price * quantity` on purchase events in
  these examples. A purchase event is not necessarily a distinct order.
- Distinguish event counts, distinct users, sessions, and orders in labels,
  documentation, and portfolio explanations.

## Query plans and scan reduction

For SQLite, inspect a representative query using:

```sql
EXPLAIN QUERY PLAN
SELECT event_name, COUNT(*)
FROM events
WHERE event_name = 'purchase'
GROUP BY event_name;
```

Read the output for full table scans, index searches, and temporary B-trees.
A scan is not automatically a defect: it may be appropriate for small tables
or queries reading most rows. Benchmark before and after changes and verify
that results remain equivalent.

For Hive, use `EXPLAIN` on the target engine and inspect partition pruning,
input scans, shuffle/reduce stages, and join strategies. The output and
optimization behavior differ from SQLite.

## Partitioning and incremental processing strategy

For a large event warehouse:

1. Derive and persist a documented event-date or ingestion-date partition
   column using a defined timezone.
2. Store analytical data in a columnar format such as Parquet where supported.
3. Filter directly on the partition column for bounded date-range queries.
4. Track a reliable ingestion watermark and process a lookback window to
   capture late-arriving events.
5. Make ingestion idempotent with a stable event ID or a documented,
   collision-resistant composite key.
6. Reconcile raw, accepted, rejected, and loaded records for each batch.
7. Reprocess affected partitions when late data or corrections change
   historical aggregates.
8. Compact small files and monitor partition skew when supported by the
   chosen platform.
9. Test retries, duplicate delivery, late arrivals, schema changes, and
   recovery before using the strategy in production.

Partitioning should follow actual query patterns and volume. Too many tiny
partitions or files can increase metadata and planning overhead. This project
does not currently demonstrate a production-scale distributed warehouse.

## SQLite and Hive dialect differences

| Concern | SQLite examples | Hive-oriented guidance |
|---|---|---|
| Date extraction | `date(timestamp)` | Use compatible date functions or a persisted partition column; verify timestamp type and timezone semantics. |
| Boolean aggregation | Expressions such as `MAX(event_name = 'purchase')` | Prefer explicit `CASE WHEN ... THEN 1 ELSE 0 END` where boolean-expression behavior differs. |
| Partition pruning | SQLite indexes and predicates | Filter directly on the partition column, for example `event_date`, using correctly formatted boundaries. |
| Query-plan inspection | `EXPLAIN QUERY PLAN` | Use Hive `EXPLAIN`; stages and output are engine-specific. |
| Distinct counts | `COUNT(DISTINCT user_id)` | Exact distinct counts may be expensive; approximate functions alter the precision contract and are engine/version-specific. |
| Window functions | SQLite window syntax | Verify supported Hive version and window semantics; `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` means seven rows, not necessarily seven calendar days. |
| Storage | Existing local SQLite database | Hive table DDL, catalog, file location, storage format, and permissions must be configured for the target environment. |

## Limitations and next validation steps

- The dataset is synthetic; results should not be presented as real customer
  behavior or commercial outcomes.
- The category query has focused automated tests; the entire cookbook does
  not yet have automated per-query tests.
- Two selected Hive query patterns passed on Apache Hive 4.0.0 using a small
  synthetic ORC table. External S3 table setup, partition pruning, and
  production-scale execution remain unvalidated.
- No production-scale benchmark demonstrates that an index, partitioning
  scheme, or distributed execution strategy improves runtime.
- Validate all query outputs, join cardinality, timestamp handling, and
  dialect-specific behavior before promoting these examples beyond the
  learning and portfolio context.


### Hive engine validation (Apache Hive 4.0.0)

Selected query logic was executed through Beeline against a disposable
Apache Hive 4.0.0 container using a small synthetic ORC table. No project
database or customer data was used.

- **Daily channel metrics:** passed. Four date/source groups returned the
  expected distinct-user counts, purchaser counts, and purchase-event revenue.
- **Rolling revenue:** passed. Daily revenue was 10.00, 40.00, and 39.00;
  rolling results were 10.00, 50.00, and 89.00.
- The missing January 3 row illustrates that a `ROWS` window counts available
  rows, not necessarily seven consecutive calendar days.
- The external S3 table DDL, partition pruning, and production-scale
  performance have not been validated.
- The dataset is synthetic and does not establish real business outcomes.

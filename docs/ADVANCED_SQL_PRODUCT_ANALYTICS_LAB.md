# Skill 1 — Advanced SQL for Product Analytics

## Goal

Build interview-ready SQL skills by answering realistic ShopFlow business questions with correct, testable queries. This is a learning task only: work on the `skill-1-advanced-sql` branch. Do not modify or merge into `main` until the lab is reviewed and validated.

**Data boundary:** use the existing synthetic ShopFlow data. Do not regenerate, overwrite, or commit the SQLite database. Keep all new SQL, tests, and notes in source-controlled text files.

## Before you start

1. Confirm branch and working tree:
   ```bash
   git switch skill-1-advanced-sql
   git status --short --branch
   ```
2. Inspect the actual database schema before writing queries:
   ```bash
   sqlite3 data/product_analytics.db ".tables"
   sqlite3 data/product_analytics.db ".schema"
   ```
   If the database path differs in your environment, locate it without modifying it.
3. Create a new file `sql/advanced_sql_lab.sql` for the exercises and `tests/test_advanced_sql_lab.py` for checks. Reuse the project’s real table and column names; do not assume the raw CSV and warehouse schema are identical.
4. For every query, add a short comment stating the business question, metric definition, grain, and any exclusions.

## Learning sequence

### Task 1 — Establish the grain and validate the data

**Business question:** What is one row in the event table, and can we trust the key fields used by later analyses?

Write read-only queries to:
- Count events, distinct users, and distinct sessions.
- Count events by event name.
- Find nulls in key fields and duplicate event rows using the available columns.
- Check whether timestamps parse and fall within a sensible range.
- Compare the observed counts with the project’s documented synthetic baseline, explaining any expected difference between raw events and transformed tables.

**Deliverable:** queries plus a brief note explaining event grain versus user/session grain.

**Acceptance checks:** counts are labelled with their grain; duplicate checks do not delete data; no query changes the database.

### Task 2 — CTEs and conversion funnels

**Business question:** Where do users drop out between product discovery and purchase?

Use CTEs to:
1. Define the eligible user population.
2. Compute user-level flags for product view, add-to-cart, checkout, and purchase.
3. Aggregate users at each funnel step.
4. Calculate step-to-step conversion and overall conversion with safe division.

Be explicit about whether the funnel is sequential by timestamp or merely based on whether a user ever had each event. If you implement sequential ordering, verify the event sequence using timestamps and state how ties are handled.

**Deliverable:** one readable CTE-based funnel query and a small results table.

**Acceptance checks:** each user is counted once per step; rates have documented denominators; zero denominators do not cause errors; the query does not silently imply sequence if it only checks event existence.

### Task 3 — Window functions

Answer these business questions with window functions:
- What is each user's first observed event and first observed activity date?
- What was the previous event in each session, and how much time elapsed since it?
- What is each user's event number within a session?
- Which products/categories rank highest by purchase count or revenue, and what is each category's share of total revenue?
- How does daily revenue compare with the previous day and a 7-day rolling average?

Use `ROW_NUMBER()`, `LAG()`, and a suitable aggregate window frame. Use deterministic tie-breakers where possible. If the data lacks a stable event ID, document how equal timestamps are handled rather than claiming deterministic ordering.

**Acceptance checks:** partition keys match the intended grain; ordering is explicit; rolling windows have a defined frame; first rows with no previous value are handled as NULL rather than incorrectly as zero.

### Task 4 — Cohort retention

**Business question:** Do users acquired in earlier observed-activity cohorts return in subsequent periods?

1. Define each user's cohort as their **first observed activity date** because the event export does not provide a reliable signup date.
2. Aggregate each user's activity to a daily or weekly period.
3. Calculate cohort size and active users by cohort age (day/week 0, 1, 2, …).
4. Calculate retention as active users in a cohort-age period divided by the original cohort size.
5. Present a cohort matrix and state how incomplete recent cohorts are treated.

**Acceptance checks:** each user belongs to one cohort; cohort age cannot be negative; period-0 retention is explained; do not call first observed activity “signup”; do not interpret missing future periods as zero retention.

### Task 5 — Revenue and ranking analysis

**Business question:** Which categories and products contribute most to revenue, and is revenue concentrated?

Calculate revenue using the documented available fields. First inspect whether the event table records price and quantity on every event; avoid summing view-event values as sales. Define a purchase event and revenue formula explicitly. Then use:
- CTEs to isolate purchase records.
- Window ranking such as `RANK()` or `DENSE_RANK()`.
- A running cumulative revenue share by ranked product/category.

**Acceptance checks:** revenue is counted only from qualifying purchase records; currency and null handling are explicit; ties are preserved where appropriate; totals reconcile to a simpler independent aggregate query.

### Task 6 — Query optimization

**Business question:** Can the same result be produced more efficiently without changing its meaning?

Choose one non-trivial query from Tasks 2–5:
1. Record the baseline query and result.
2. Run `EXPLAIN QUERY PLAN` in SQLite.
3. Identify scans, joins, repeated expressions, or sorts that may be expensive.
4. Make one measured change at a time (for example, filtering earlier, simplifying a CTE, or testing a relevant index in an isolated temporary copy).
5. Compare the result set before and after optimization.
6. Record plan differences and timing methodology.

**Safety:** do not add indexes to or otherwise mutate the project's committed database for this exercise. If testing an index, use a disposable copy or an in-memory database. Do not claim a query is faster based only on a different-looking query plan.

**Acceptance checks:** result equivalence is verified; optimization rationale is evidence-based; the original database remains unchanged.

### Task 7 — Regression tests

Create tests in `tests/test_advanced_sql_lab.py`. Prefer a tiny in-memory SQLite fixture with a handful of users, sessions, and events, including edge cases:
- A user with no purchase.
- A user who skips an intermediate funnel step.
- Two events with the same timestamp.
- A cohort with activity in week 0 and week 2 but not week 1.
- A product/category tie in ranking.
- NULL price or quantity on a non-purchase event.
- A zero-row/empty input case.

Tests should verify metric definitions and expected results, not merely that SQL executes. For example:
- Each user is counted at most once per funnel step.
- Funnel denominators are correct.
- A missing prior event returns NULL for `LAG`.
- Retention denominator remains the original cohort size.
- Revenue excludes non-purchase events.
- Optimized and baseline queries return the same ordered rows.

Run:
```bash
PYTHONPATH=. python -m pytest -q tests/test_advanced_sql_lab.py
PYTHONPATH=. python -m pytest -q
git diff --check
git status --short
```

Do not weaken or rewrite existing tests to make the lab pass.

## Suggested file layout

- `sql/advanced_sql_lab.sql` — labelled, read-only SQL solutions.
- `tests/test_advanced_sql_lab.py` — isolated in-memory regression tests.
- `docs/ADVANCED_SQL_LAB_NOTES.md` — metric definitions, findings, query plans, and caveats.

## Definition of done

- [ ] Actual table schema inspected and recorded.
- [ ] CTE funnel query with documented grain and denominators.
- [ ] Window-function exercises completed.
- [ ] Cohort retention matrix uses first-observed activity, not inferred signup.
- [ ] Purchase-only revenue and ranking query reconciles to an independent total.
- [ ] One query optimized with before/after plan and result comparison.
- [ ] Edge-case regression tests pass.
- [ ] Full existing test suite passes; `git diff --check` is clean.
- [ ] No database files or generated data were changed.
- [ ] Changes reviewed on `skill-1-advanced-sql` before considering any PR to `main`.

## Business questions to answer in your final notes

1. Which funnel step has the largest absolute and percentage drop-off, and what denominator did you use?
2. Which categories contribute the most purchase revenue?
3. How does retention vary by first-observed-activity cohort?
4. What behavioral pattern appears in session event sequences?
5. What changed in the query plan, and what evidence supports the optimization?
6. What limitations prevent these synthetic results from being treated as real customer evidence?

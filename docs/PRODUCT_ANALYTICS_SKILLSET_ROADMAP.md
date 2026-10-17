# Product Analytics Skillset Roadmap

This roadmap extends the ShopFlow synthetic e-commerce analytics project. Work is developed on the `product-analytics-skillset-roadmap` branch; merge into `main` only after review and local/CI validation.

## Phase 1 — Experimentation and statistics

- [x] Define a proposed product question, primary metric, null/alternative hypotheses, and guardrails (`docs/EXPERIMENT_PREANALYSIS_PLAN.md`; design only, not a launched experiment).
- [x] Add tested assignment-integrity checks, SRM diagnostics, recorded-exposure reporting, and outcome-event counts; document limitations (`src/experiment_integrity.py`, `src/experimentation.py`, `tests/test_experiment_integrity.py`).
- [x] Define and test the primary user-level binary outcome and fixed seven-day, same-session attribution rule (`src/experiment_outcomes.py`, `tests/test_experiment_outcomes.py`; proposed design only).
- [ ] Finalize the business-relevant MDE and assess assignment, exposure, outcome completeness, attrition, guardrails, and experiment-readiness criteria before treating the design as launch-ready.
- [x] Calculate provisional user-level baseline conversion, sample-size scenarios, and approximate power using the fixed seven-day outcome (`src/experiment_outcomes.py`, `src/experimentation.py`; synthetic data only, business MDE not yet approved).
- [x] Report treatment/control rates, absolute and relative differences, confidence intervals, and p-values for the proposed cart-conversion outcome as exploratory synthetic-data analysis (`docs/EXPERIMENTATION_RESULTS.md`).
- [ ] Assess practical significance against a business-approved MDE and guardrails before making a product decision.
- [x] Add tested logistic regression adjustment with odds-ratio confidence intervals and document covariate timing, confounding, and synthetic-data limitations (`src/experimentation.py`, `tests/test_regression_adjustment.py`, `notebooks/04_experiment_diagnostics_regression.ipynb`, `docs/EXPERIMENTATION_RESULTS.md`).
- [x] Document peeking, multiple testing, selection bias, novelty effects, confounding, and limits of synthetic data (`docs/EXPERIMENTATION_PITFALLS.md`).
- [x] Deliver a reproducible experimentation notebook and tests for reusable statistical functions (`notebooks/05_experimentation_analysis.ipynb`, `tests/test_experiment_outcomes.py`, and `tests/test_experiment_planning.py`).

## Phase 2 — Funnels, cohorts, segmentation, and campaigns

- [x] Define funnel user/session grain and event ordering (ordered funnel uses session grain).
- [x] Add step-to-step conversion and drop-off SQL (`sql/sequential_funnel.sql`, covered by tests).
- [x] Add first-observed-activity retention cohorts with maturity-aware D1/D7/D30 rates (`sql/retention_cohorts.sql`, dashboard Retention page, and `tests/test_retention_cohorts.py`).
- [ ] Add signup-based retention cohorts after exporting and validating a user-level dataset with reliable signup dates. `src/generate_data.py` currently creates `signup_date` in memory but exports only event-level rows to `data/raw/raw_events.csv`; the existing event dataset therefore supports first-observed-activity cohorts only. Do not infer signup dates from `app_open` events.
- [x] Compare segments by device, acquisition source, and engagement (`sql/segment_conversion.sql`, `sql/engagement_conversion.sql`, dashboard Segmentation page).
- [x] Add campaign/experiment comparisons without implying causality from observational differences (`sql/ab_test_analysis.sql`, dashboard Experimentation page, `src/experimentation.py`, and `tests/test_experimentation.py`; synthetic-data limitations documented).
- [x] Deliver dashboard views and prioritized, evidence-linked recommendations (`dashboard/app.py`, `docs/PRODUCT_INSIGHTS_AND_RECOMMENDATIONS.md`).

## Phase 3 — Warehouse and ETL engineering

- [x] Document event grain, keys, metric definitions, and lineage (`docs/ANALYTICS_METRIC_DICTIONARY.md`, `docs/WAREHOUSE_AND_ETL_DESIGN.md`).
- [x] Design fact and dimension tables and a logical star schema (`docs/STAR_SCHEMA_DESIGN.md`; design only, physical migration deferred).
- [x] Add an in-memory raw/staging/analytics prototype and reusable transformations (`src/warehouse_layers.py`; no persistence).
- [x] Document the event identity and ingestion contract (`docs/INGESTION_CONTRACT.md`) and prototype in-memory incremental batch idempotency (`src/incremental_loading.py`). Stable source event IDs, production late-arriving-event handling, and persistence remain unfinished.
- [x] Orchestrate in-memory ingestion validation, rejected-record classification, duplicate filtering, and batch reconciliation (`src/ingestion_workflow.py`, `docs/INGESTION_WORKFLOW_PROTOTYPE.md`; covered by `tests/test_ingestion_workflow.py`). The composite fingerprint remains a prototype identity strategy, not a stable source event ID.
- [x] Test schema, nullability, accepted values, and core data-quality rules (`tests/test_etl_quality.py`). Explicit timestamp parsing for the documented `%Y-%m-%d %H:%M:%S` format is covered by regression tests. In-memory layer reconciliation is covered by `tests/test_warehouse_quality.py`. Production uniqueness, referential integrity, and persisted source-to-target reconciliation remain future work.
- [x] Document recovery and production run instructions in `docs/WAREHOUSE_RECOVERY_RUNBOOK.md`. Prototype limitations are documented in `docs/WAREHOUSE_LAYERS_PROTOTYPE.md`, `docs/WAREHOUSE_QUALITY_RECONCILIATION.md`, `docs/INCREMENTAL_LOADING_PROTOTYPE.md`, and `docs/INGESTION_CONTRACT.md`. Production-grade persistence, retries, and rollback remain unimplemented.

## Phase 4 — Advanced SQL and Hive

- [x] Provide business questions solved with joins, CTEs, conditional aggregation, and window functions (`sql/advanced_sql_cookbook.sql`, `sql/category_performance.sql`; SQLite tests use isolated databases).
- [x] Review query plans and compare indexed versus full-scan execution for a representative SQLite query; document measured results and scope in `docs/ADVANCED_SQL_AND_HIVE.md`.
- [x] Document partitioning and incremental processing strategies for large event tables in `docs/ADVANCED_SQL_AND_HIVE.md`; production-scale implementation is not claimed.
- [x] Validate selected Hive query patterns on Apache Hive 4.0.0 using an isolated synthetic ORC table and document dialect differences (`docs/ADVANCED_SQL_AND_HIVE.md`); external S3 setup, partition pruning, and production-scale execution remain unvalidated.
- [x] Deliver a query cookbook and validation notes (`docs/ADVANCED_SQL_AND_HIVE.md`; SQLite validation and selected Hive 4.0.0 query tests, with remaining limitations documented).

## Acceptance criteria

A phase is complete only when its implementation exists in the repository, outputs are reproducible, tests pass, business meaning and assumptions are documented, and the portfolio narrative distinguishes synthetic examples from real evidence.

## Safety and release rules

- Do not overwrite or regenerate an existing database as a side effect of analysis.
- Do not run database writes against production Supabase.
- Do not merge or deploy until changes have been reviewed and tests pass.
- Preserve user-local, uncommitted database changes; never stage broad path sets.

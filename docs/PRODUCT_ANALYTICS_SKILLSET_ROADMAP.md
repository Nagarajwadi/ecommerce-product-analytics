# Product Analytics Skillset Roadmap

This roadmap extends the ShopFlow synthetic e-commerce analytics project. Work is developed on the `product-analytics-skillset-roadmap` branch; merge into `main` only after review and local/CI validation.

## Phase 1 — Experimentation and statistics

- [x] Define a proposed product question, primary metric, null/alternative hypotheses, and guardrails (`docs/EXPERIMENT_PREANALYSIS_PLAN.md`; design only, not a launched experiment).
- [x] Add tested assignment-integrity checks, SRM diagnostics, recorded-exposure reporting, and outcome-event counts; document limitations (`src/experiment_integrity.py`, `src/experimentation.py`, `tests/test_experiment_integrity.py`).
- [ ] Validate the primary binary outcome definition and fixed attribution window; assess sample-size assumptions and experiment-readiness criteria.
- [ ] Calculate baseline conversion, minimum detectable effect, sample size, and statistical power.
- [ ] Report treatment/control rates, absolute and relative lift, confidence intervals, p-values, and practical significance.
- [x] Add tested logistic regression adjustment with odds-ratio confidence intervals and document covariate timing, confounding, and synthetic-data limitations (`src/experimentation.py`, `tests/test_regression_adjustment.py`, `notebooks/04_experiment_diagnostics_regression.ipynb`, `docs/EXPERIMENTATION_RESULTS.md`).
- [x] Document peeking, multiple testing, selection bias, novelty effects, confounding, and limits of synthetic data (`docs/EXPERIMENTATION_PITFALLS.md`).
- [ ] Deliver a reproducible notebook and tests for reusable statistical functions.

## Phase 2 — Funnels, cohorts, segmentation, and campaigns

- [x] Define funnel user/session grain and event ordering (ordered funnel uses session grain).
- [x] Add step-to-step conversion and drop-off SQL (`sql/sequential_funnel.sql`, covered by tests).
- [x] Add first-observed-activity retention cohorts with maturity-aware D1/D7/D30 rates (`sql/retention_cohorts.sql`, dashboard Retention page, and `tests/test_retention_cohorts.py`).
- [ ] Add signup-based retention cohorts after a reliable signup timestamp is available in the analysis dataset; current event data supports first-observed-activity cohorts only.
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
- [ ] Document recovery and production run instructions. Prototype limitations are documented in `docs/WAREHOUSE_LAYERS_PROTOTYPE.md`, `docs/WAREHOUSE_QUALITY_RECONCILIATION.md`, `docs/INCREMENTAL_LOADING_PROTOTYPE.md`, and `docs/INGESTION_CONTRACT.md`.

## Phase 4 — Advanced SQL and Hive

- [ ] Provide business questions solved with joins, CTEs, conditional aggregation, and window functions.
- [ ] Review query plans and reduce unnecessary scans.
- [ ] Document partitioning and incremental processing strategies for large event tables.
- [ ] Port selected analyses to Hive-compatible SQL, documenting dialect differences.
- [ ] Deliver a query cookbook and validation notes.

## Acceptance criteria

A phase is complete only when its implementation exists in the repository, outputs are reproducible, tests pass, business meaning and assumptions are documented, and the portfolio narrative distinguishes synthetic examples from real evidence.

## Safety and release rules

- Do not overwrite or regenerate an existing database as a side effect of analysis.
- Do not run database writes against production Supabase.
- Do not merge or deploy until changes have been reviewed and tests pass.
- Preserve user-local, uncommitted database changes; never stage broad path sets.

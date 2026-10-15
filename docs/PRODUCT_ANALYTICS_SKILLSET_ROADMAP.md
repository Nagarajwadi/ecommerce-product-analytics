# Product Analytics Skillset Roadmap

This roadmap extends the ShopFlow synthetic e-commerce analytics project. Work is developed on the `product-analytics-skillset-roadmap` branch; merge into `main` only after review and local/CI validation.

## Phase 1 — Experimentation and statistics

- [ ] Define a product question, primary metric, null/alternative hypotheses, and guardrails.
- [ ] Validate assignment balance, sample-ratio mismatch, exposure, and outcome definitions.
- [ ] Calculate baseline conversion, minimum detectable effect, sample size, and statistical power.
- [ ] Report treatment/control rates, absolute and relative lift, confidence intervals, p-values, and practical significance.
- [ ] Add regression adjustment and discuss confounding and assumptions.
- [ ] Document peeking, multiple testing, selection bias, novelty effects, and limits of synthetic data.
- [ ] Deliver a reproducible notebook and tests for reusable statistical functions.

## Phase 2 — Funnels, cohorts, segmentation, and campaigns

- [x] Define funnel user/session grain and event ordering (ordered funnel uses session grain).
- [x] Add step-to-step conversion and drop-off SQL (`sql/sequential_funnel.sql`, covered by tests).
- [ ] Add signup/activity retention cohorts and cohort-size-aware retention rates.
- [x] Compare segments by device, acquisition source, and engagement (`sql/segment_conversion.sql`, `sql/engagement_conversion.sql`, dashboard Segmentation page).
- [ ] Add campaign/experiment comparisons without implying causality from observational differences.
- [x] Deliver dashboard views and prioritized, evidence-linked recommendations (`dashboard/app.py`, `docs/PRODUCT_INSIGHTS_AND_RECOMMENDATIONS.md`).

## Phase 3 — Warehouse and ETL engineering

- [x] Document event grain, keys, metric definitions, and lineage (`docs/ANALYTICS_METRIC_DICTIONARY.md`, `docs/WAREHOUSE_AND_ETL_DESIGN.md`).
- [x] Design fact and dimension tables and a logical star schema (`docs/STAR_SCHEMA_DESIGN.md`; design only, physical migration deferred).
- [ ] Add raw/staging/analytics layers and reusable transformations.
- [ ] Add incremental-load design, idempotency, and late-arriving-event handling.
- [x] Test schema, nullability, accepted values, and core data-quality rules (`tests/test_etl_quality.py`, 11 tests). Uniqueness, referential integrity, and source-to-target reconciliation remain future work.
- [ ] Document recovery, run instructions, and pipeline limitations.

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

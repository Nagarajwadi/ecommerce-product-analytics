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

- [ ] Define funnel user/session grain and event ordering.
- [ ] Add step-to-step conversion and drop-off SQL.
- [ ] Add signup/activity retention cohorts and cohort-size-aware retention rates.
- [ ] Compare segments by device, acquisition source, and engagement.
- [ ] Add campaign/experiment comparisons without implying causality from observational differences.
- [ ] Deliver dashboard views and prioritized, evidence-linked recommendations.

## Phase 3 — Warehouse and ETL engineering

- [ ] Document event grain, keys, metric definitions, and lineage.
- [ ] Design fact and dimension tables and a star schema.
- [ ] Add raw/staging/analytics layers and reusable transformations.
- [ ] Add incremental-load design, idempotency, and late-arriving-event handling.
- [ ] Test schema, nullability, uniqueness, referential integrity, accepted values, and reconciliation.
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

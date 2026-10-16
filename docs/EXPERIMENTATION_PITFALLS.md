# Experimentation Pitfalls and Interpretation Guide

## Purpose

This guide documents common threats to valid product-experiment interpretation. The ShopFlow dataset is synthetic, so its results demonstrate analysis methods rather than establish effects for real customers.

## 1. Repeated peeking and stopping rules

**Risk:** Repeatedly checking ordinary fixed-horizon p-values and stopping as soon as a result becomes significant can inflate the false-positive rate.

**Recommended practice:**
- Define the target sample size, experiment duration, primary metric, and stopping rule before examining results.
- Do not treat repeated fixed-horizon significance checks as if only one test was performed.
- If continuous monitoring is required, use a suitable sequential-testing procedure and document it.
- Report deviations from the planned stopping rule.

## 2. Multiple testing

**Risk:** Testing many metrics, segments, or experiment variants increases the chance that at least one result appears significant by chance.

**Recommended practice:**
- Pre-specify the primary metric and distinguish it from secondary and exploratory metrics.
- Define the family of hypotheses that will be interpreted together.
- Use an appropriate correction, such as Holm-Bonferroni, when controlling family-wise error across a set of tests.
- Report the unadjusted and adjusted results, where applicable, and avoid presenting exploratory discoveries as confirmatory evidence.

A correction does not repair biased selection, invalid assignment, or incorrect outcome definitions.

## 3. Selection bias

**Risk:** The analyzed population may differ systematically from the population eligible for the experiment. For example, analyzing only users who completed a later funnel step can condition the analysis on behavior affected by treatment.

**Recommended practice:**
- Define eligibility and the randomization unit before launch.
- Analyze users according to their assigned group when using an intention-to-treat design.
- Document exclusions and missing outcomes, including whether they differ by assignment group.
- Avoid conditioning the primary analysis on post-assignment actions unless the estimand and method explicitly justify it.

## 4. Novelty and time effects

**Risk:** An initial response to a new experience may weaken as users become familiar with it. Calendar effects, seasonality, or changes in traffic composition can also affect observed outcomes.

**Recommended practice:**
- Choose an observation window that captures the product behavior of interest.
- Consider whether the experiment spans relevant weekly or seasonal cycles.
- Inspect effects over time as a diagnostic, while respecting the pre-specified primary analysis.
- Treat post-hoc time-window or subgroup discoveries as exploratory unless appropriately planned and tested.

A changing effect over time is a hypothesis to investigate, not proof of a novelty effect.

## 5. Confounding and regression adjustment

**Risk:** In observational comparisons, differences between groups may reflect other factors associated with both group membership and outcomes. Regression adjustment cannot automatically remove unmeasured confounding or repair broken randomization.

**Recommended practice:**
- Verify the assignment mechanism and the timing of covariates.
- Use only justified pre-treatment covariates for conventional adjustment.
- Report the model specification, effect measure, confidence interval, and assumptions.
- Distinguish adjusted odds ratios from absolute percentage-point changes in conversion.

See the regression diagnostics in `notebooks/04_experiment_diagnostics_regression.ipynb` for the project's illustrative analysis.

## 6. Synthetic-data limitations

**Risk:** Generated data can demonstrate a workflow but cannot validate real customer behavior, production instrumentation, or the true business impact of a feature.

**Recommended practice:**
- Label dataset-derived figures and simulated examples as synthetic.
- Do not describe statistical significance in generated data as evidence of a real product effect.
- Verify event definitions, assignment and exposure logging, eligibility, observation windows, and data quality before applying the workflow to real experiments.
- Separate observed calculations from hypotheses and recommendations.

## Pre-analysis checklist

Before interpreting an experiment, confirm that:

- [ ] The product question, randomization unit, eligibility, and exposure definition are documented.
- [ ] The primary metric, outcome window, hypotheses, guardrails, sample size, and stopping rule are pre-specified.
- [ ] Assignment integrity, outcome completeness, and sample-ratio mismatch have been checked.
- [ ] The multiple-testing family and correction approach are documented.
- [ ] Exclusions, missing outcomes, and subgroup analyses are explained.
- [ ] Effect sizes and confidence intervals accompany p-values.
- [ ] Practical significance and guardrail outcomes inform the decision.
- [ ] Synthetic results are not presented as real customer evidence.

## Scope

This guide provides practical interpretation safeguards, not a complete statistical protocol. The appropriate analysis depends on the experiment design, estimand, data-generating process, and decision being made.
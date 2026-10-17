# ShopFlow Experimentation Results

## Scope and data status

These results were calculated from the project's local SQLite event table during the Product Analytics skillset exercise. The project dataset is synthetic. Treat all rates, p-values, coefficients, and diagnostics as demonstrations of the analysis workflow, not evidence about real customers or a verified live experiment.

The purchase-conversion analysis used one row per user for the binary outcome: whether the user had at least one `purchase` event. The experiment group was taken from the user's event records, and the analysis included users with a single distinct non-null experiment group. Database access was read-only. This purchase outcome is distinct from the view-conditioned cart-conversion outcome documented separately below; their rates and effect estimates should not be treated as interchangeable.

The event data does not record an explicit assignment timestamp. Consequently, these analyses cannot verify that events used as exposure anchors occurred after assignment. Assignment consistency checks alone do not establish that exposure timing, eligibility, or a real experiment's randomization process was valid.

## Observed conversion comparison

| Metric | Control | Treatment |
|---|---:|---:|
| Users | 4,949 | 5,051 |
| Users with at least one purchase | 1,691 | 2,065 |
| Purchase conversion | 34.17% | 40.88% |

- Absolute lift (treatment minus control): **+6.71 percentage points**.
- Relative lift: **+19.65%**.
- Two-sided pooled two-proportion z-test: **z = 6.93**, **p = 4.15e-12**.
- 95% unpooled Wald confidence interval for absolute lift: **+4.82 to +8.61 percentage points**.

The interval excludes zero and the test is statistically significant at alpha = 0.05 under the test assumptions. This does not establish causality: the data's assignment process, eligibility rules, exposure definition, and observation window must be verified before interpreting a real experiment.

## Assignment diagnostics

- Users observed in multiple experiment groups: **0**.
- Users with at least one event missing an assignment value: **0** in the notebook diagnostic.
- Observed assignment counts: **4,949 control**, **5,051 treatment**.
- For an expected 50/50 split, sample-ratio mismatch diagnostic: **chi-square = 1.0404**, **p = 0.3077**. This did not flag a mismatch at 0.05; a non-significant result does not prove randomization or logging was correct.
- Device mix was inspected by group. Traffic source and device can only be used as pre-treatment adjustment variables if their timing relative to assignment is confirmed.

## Planning example and interpretation limits

Notebook 03's separate teaching example uses a 34% baseline, a +2 percentage-point absolute minimum detectable effect, two-sided alpha = 0.05, and target power = 80%. Its normal-approximation calculation returns **8,927 users per group** (17,854 total). That is a planning calculation for the specified MDE, not the required sample size for every possible effect.

The notebook's illustrative fixed-horizon counts (1,000 per group; 34% versus 41%) are separate from the dataset-derived counts above. Statistical significance is not the same as practical significance; assess business value and guardrails before making a product decision.


Notebook 04's adjusted logistic regression estimates a treatment coefficient of **+0.2905 log-odds** (standard error **0.0416**), corresponding to an adjusted odds ratio of **1.337** with a model-based **95% confidence interval of 1.232–1.451** and a treatment-coefficient p-value of **2.81 × 10⁻¹²**. This is a conditional association with purchase odds, not a percentage-point conversion lift. Device and traffic source are generated once per user before events in this synthetic dataset and are used as illustrative pre-treatment covariates. In a real experiment, verify covariate timing and assignment design before adjustment. Regression does not eliminate unmeasured confounding or repair experiment-design problems. All results are synthetic teaching examples, not evidence about actual customers.

The Holm-Bonferroni example is illustrative and uses pre-specified example p-values (0.01, 0.04, 0.03), adjusted to (0.03, 0.06, 0.06). It is not a set of observed product hypotheses.

For the proposed product-page experiment design and pre-analysis rules, see [`EXPERIMENT_PREANALYSIS_PLAN.md`](EXPERIMENT_PREANALYSIS_PLAN.md). This is a proposed plan, not a record of a launched experiment.

## Before interpreting a real experiment

1. Write down the product question, primary metric, randomization unit, eligibility/exposure definition, observation window, null and alternative hypotheses, and guardrail metrics.
2. Verify assignment and exposure logs, outcome completeness, one-group-per-user consistency, and the planned allocation ratio.
3. Pre-specify the sample size, MDE, stopping rule, and multiple-testing family; do not repeatedly peek at fixed-horizon p-values.
4. Confirm covariates are pre-treatment before using them for balance checks or regression adjustment.
5. Report absolute and relative lift, confidence intervals, p-values, practical significance, and guardrail outcomes together.
6. Disclose selection bias, novelty effects, possible confounding, and that synthetic results are not real customer evidence.
For expanded explanations and a reusable pre-analysis checklist, see
[`EXPERIMENTATION_PITFALLS.md`](EXPERIMENTATION_PITFALLS.md).

## Reproducibility and safety

- Notebook 03 and Notebook 04 were executed successfully with `jupyter nbconvert --execute`.
- Earlier validation record: the automated test suite passed **28 tests**.
- Current roadmap-branch validation: the full automated test suite passed **187 tests** (`PYTHONPATH=. python -m pytest -q`).
- The retention cohort test file passed: **2 tests** in the separate validation run.
- Notebook 04 opens `data/product_analytics.db` using SQLite read-only mode. No database writes are required for this analysis.
- Executed notebooks were written to `/tmp`; generated outputs were not written back into the tracked notebook files.

## Proposed product-page cart-conversion outcome

This is a separate exploratory analysis from the purchase-conversion results above. It applies the proposed primary outcome in `EXPERIMENT_PREANALYSIS_PLAN.md` to the synthetic event dataset: each user is eligible after a qualifying product view, and converts if at least one `add_to_cart` occurs at or after the first qualifying view in the same session, within the inclusive seven-day observation window. Users without a qualifying view are reported separately; users with conflicting experiment assignments are excluded.

This is a view-conditioned comparison, not an intention-to-treat estimate. Because treatment may affect whether a user views a product, conditioning eligibility on a product view can introduce selection bias. The data also lacks an explicit assignment timestamp, so it cannot establish that the first recorded view occurred after assignment. The reported difference, confidence interval, and p-value are exploratory descriptions of synthetic data, not a causal treatment-effect estimate.

| Metric | Control | Treatment |
|---|---:|---:|
| Assigned users | 4,949 | 5,051 |
| Eligible users with a qualifying product view | 4,841 | 4,949 |
| Users who added to cart under the outcome rule | 1,422 | 1,586 |
| User-level cart-conversion rate | 29.37% | 32.05% |
| Assigned users without a qualifying view | 108 | 102 |

- Absolute difference (treatment minus control): **+2.673 percentage points**.
- Relative difference versus control: **+9.10%**.
- Exploratory two-sided pooled two-proportion z-test: **z = 2.8659**, **p = 0.004158**.
- 95% unpooled Wald confidence interval for the absolute difference: **+0.846 to +4.499 percentage points**.
- Users with conflicting experiment assignments excluded: **0**.

The test is statistically significant at alpha = 0.05 under its assumptions, and the approximate confidence interval excludes zero. However, this dataset is synthetic, and these calculations do not establish a causal treatment effect or a verified experiment result. The z-test assumes independent units and a valid fixed-horizon design; the confidence interval uses an unpooled Wald approximation. The business-relevant MDE has not been approved, and practical significance and launch readiness remain unresolved. Do not interpret the result as a product launch recommendation.

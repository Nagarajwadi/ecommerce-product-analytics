# Product-Page Clarity Experiment: Pre-Analysis Plan

## Status and scope

Status: Proposed design; not launched or validated.

This plan describes a hypothetical randomized experiment for the ShopFlow
synthetic e-commerce project. Existing synthetic results do not demonstrate
that this treatment was implemented or that it caused an improvement.

## 1. Product question

Does clearer product information increase the proportion of eligible
users who add an item to the cart after a qualifying product view?

## 2. Proposed treatment

- Control: existing product-page experience.
- Treatment: a product-information section with clearer price,
  availability, and delivery information.
- Keep other page elements unchanged where practical.
- Record the assigned variant and qualifying exposure explicitly.

## 3. Population, assignment, and exposure

- Eligibility: define eligible users and supported products before launch.
- Randomization unit: user.
- Allocation: 50/50 treatment and control, unless a justified alternative
  is specified before launch.
- Exposure: the first qualifying product-page view after assignment.
- Observation window: seven days after the user's first qualifying product view; the endpoint is inclusive. This is the proposed fixed attribution window for the tested helper.
- Persist assignment across sessions to prevent variant switching.
- Exclude users only according to pre-specified eligibility and data-quality
  rules; report exclusions by assigned group.

The current synthetic dataset does not establish that these conditions
were met in a real experiment.

## 4. Primary metric

User-level product-view-to-add-to-cart conversion. This is an exploratory, view-conditioned metric for the synthetic dataset, not an intention-to-treat (ITT) estimate.

- Randomization unit: user.
- Eligibility: a consistently assigned user with at least one valid `view_product` event in the available event data.
- Exposure anchor: the user's earliest recorded `view_product` event. The dataset does not contain an explicit assignment timestamp, so the implementation cannot verify that this view occurred after assignment.
- Numerator: eligible users with at least one `add_to_cart` event that occurs at or after that first view, in the same session, and no later than seven days after the view. The seven-day endpoint is inclusive.
- Denominator: eligible users with a qualifying product view, reported separately for control and treatment.
- Deduplication: each user contributes at most one conversion per assigned group, regardless of repeated view or cart events.
- Users without a qualifying view are reported separately and are not counted as non-converters in the eligible-user conversion rate.
- Users with conflicting experiment-group assignments are excluded from the group comparison and reported separately.
- Analysis: compare treatment and control rates and report the absolute difference in percentage points with a 95% confidence interval. Treat the comparison as descriptive and exploratory.

Because eligibility is conditioned on a product view, the comparison may be affected by selection bias if treatment changes the probability of viewing a product. It should not be interpreted as the causal effect of assignment. A future real experiment should pre-specify an appropriate all-assigned-users intention-to-treat outcome and observation window, with view-conditioned conversion retained as a secondary diagnostic if useful.

The reusable implementation is `src/experiment_outcomes.py`; its tests are in `tests/test_experiment_outcomes.py`. This is a proposed outcome contract for the synthetic project, not evidence that a real experiment implemented the assignment, exposure, or measurement correctly.

## 5. Hypotheses

Let pT and pC denote the primary-metric rates in treatment and control.

- Null hypothesis: pT - pC = 0.
- Alternative hypothesis: pT - pC != 0.
- Significance level: two-sided alpha = 0.05, unless changed and justified
  before launch.

## 6. Guardrails

Report at least:

- Purchase conversion.
- Checkout-to-purchase conversion.
- Product-page performance and error rate.

Define each metric's denominator, attribution window, and acceptable
non-inferiority margin before launch. Do not treat a non-significant
guardrail test as proof that no harm occurred.

## 7. Sample size and power

Before launch, specify:

- Baseline primary-metric rate from a suitable pre-experiment period.
- Minimum detectable absolute effect that would matter to the business.
- Two-sided alpha and target power.
- Expected allocation, exclusions, and data loss.
- The planned method for inference given user-level randomization.

### Provisional calculation using the implemented user-level outcome

A read-only analysis of `data/processed/clean_events.csv` used the tested
helper in `src/experiment_outcomes.py`. The primary outcome is user-level
product-view-to-add-to-cart conversion: at least one add-to-cart event after
the user's earliest product view, in that same session, within the inclusive
seven-day window.

Observed synthetic-data summary:

- Control: 1,422 / 4,841 eligible users converted (29.3741%).
- Treatment: 1,586 / 4,949 eligible users converted (32.0469%).
- Observed absolute difference: approximately +2.67 percentage points.
- Users assigned to control / treatment: 4,949 / 5,051.
- Users without a qualifying product view: 108 control and 102 treatment.
- Users excluded for conflicting group assignments: 0.

These rates and the observed difference are descriptive only. The synthetic
dataset does not establish a valid randomized experiment or a causal effect.

For provisional planning, the observed control rate (approximately 29.37%)
was used as the baseline, with two-sided alpha = 0.05, target power = 80%,
equal group sizes, independent users, and the project's two-proportion normal
approximation:

| Illustrative absolute MDE | Required per group | Required total |
| --- | ---: | ---: |
| 2 percentage points | 8,299 | 16,598 |
| 5 percentage points | 1,363 | 2,726 |

At the current eligible group sizes, the approximate power is 57-58% for a
2-percentage-point effect and about 99.96% for a 5-percentage-point effect.
These are planning approximations, not retrospective evidence that the
synthetic treatment worked.

Neither MDE is approved as the business decision threshold. Choose it based
on product impact, implementation cost, and the smallest improvement worth
detecting. Before launch, also establish the randomized-user denominator,
assignment and exposure logging, outcome completeness, expected attrition,
guardrail margins, and the final inference method. Recalculate sample size
after these choices are documented.

The calculation assumes a fixed-horizon design and independent randomized
users. The synthetic data does not validate treatment implementation,
exposure, or real customer behavior.

## 8. Stopping rule and multiplicity

Use a pre-specified fixed sample size and observation window. Do not repeatedly
check ordinary fixed-horizon p-values and stop when significance appears.
If interim decisions are required, select a valid sequential design in advance.

Designate the primary metric as the confirmatory outcome. Treat additional
metrics and subgroup analyses as secondary or exploratory, and pre-specify
any multiple-testing correction for confirmatory families.

## 9. Decision criteria

Consider shipping only if:

1. The primary estimate is directionally favorable and its uncertainty is
   consistent with a meaningful benefit under the pre-specified test.
2. The estimated effect meets the pre-specified practical-value threshold.
3. Guardrails remain within their pre-specified acceptable margins.
4. Assignment, exposure, outcome logging, and data quality pass review.

If evidence is inconclusive, do not claim success. Investigate data quality,
review the confidence interval, and plan a new test only with a justified
design.

## 10. Reporting and limitations

Report group sizes, conversion rates, absolute and relative differences,
confidence intervals, p-values, guardrails, exclusions, and deviations from
the plan.

The project's existing data is synthetic. It can demonstrate analysis
workflows, but it cannot establish real customer behavior or validate this
hypothetical treatment. The experiment must be implemented and measured
before any causal conclusion is drawn.

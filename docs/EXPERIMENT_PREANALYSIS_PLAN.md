# Product-Page Clarity Experiment: Pre-Analysis Plan

## Status and scope

Status: Proposed design; not launched or validated.

This plan describes a hypothetical randomized experiment for the ShopFlow
synthetic e-commerce project. Existing synthetic results do not demonstrate
that this treatment was implemented or that it caused an improvement.

## 1. Product question

Does clearer product information increase the proportion of eligible
product-view sessions that add an item to the cart?

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
- Observation window: start at the first qualifying exposure and use a pre-specified, fixed follow-up duration. Define the duration before launch.
- Persist assignment across sessions to prevent variant switching.
- Exclude users only according to pre-specified eligibility and data-quality
  rules; report exclusions by assigned group.

The current synthetic dataset does not establish that these conditions
were met in a real experiment.

## 4. Primary metric

Session-level product-view-to-add-to-cart conversion.

- Denominator: eligible sessions with a qualifying product-view event.
- Numerator: those sessions with a qualifying add-to-cart event after the
  first qualifying product view.
- Attribution window: define and freeze the window before launch.
- Deduplication: count each eligible session at most once in the numerator.
- Analysis: compare treatment and control rates and report the absolute
  difference in percentage points with a 95% confidence interval.

Because sessions from the same user may be correlated, inference must account
for user-level randomization. Prefer a pre-specified user-level outcome, such
as whether a user has at least one qualifying view-to-cart session during the
fixed follow-up window. If session-level conversion remains primary, use an
appropriate user-clustered inference method. Choose one approach before launch.

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

### Illustrative calculation using synthetic data

A provisional user-level calculation was performed using the existing synthetic
event data:

- Baseline: 6,728 / 9,790 users = 68.7232%.
- Illustrative treatment target: 73.7232%.
- Minimum detectable absolute effect: 5 percentage points.
- Significance level: two-sided alpha = 0.05.
- Target power: 80%.
- Allocation: 50% control and 50% treatment.
- Approximate requirement: 1,286 users per arm, or 2,572 users total,
  using the project's independent two-proportion normal approximation.

This estimate is provisional, not a finalized experiment target. The baseline
includes users with eligible product-view sessions and does not establish
the correct denominator for all eligible randomized users in a future
experiment. Eligibility, exposure, outcome attribution, and any expected
attrition must be finalized before adopting the sample-size target.

The calculation assumes independent randomized users, a fixed-horizon design,
and complete outcome measurement. The synthetic data does not validate that
the proposed treatment was implemented or exposed correctly.


Calculate and document the required sample size before examining treatment
outcomes. The existing notebook's sample-size example is illustrative and
must not automatically be reused without checking its assumptions.

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

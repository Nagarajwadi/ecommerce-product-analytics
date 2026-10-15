# Product Insights and Recommendations

## Purpose and scope

This report summarizes findings from the ShopFlow synthetic e-commerce product analytics dataset. The figures below describe the generated dataset; they are not evidence about real customers or a live product. The report separates observed metrics from hypotheses and recommended validation.

## Executive summary

1. **Product-view to cart is the largest observed sequential funnel drop-off.** In the session-level ordered funnel, 38,377 sessions reached product view and 11,729 advanced to add to cart. Step conversion was 30.56%, with 26,648 sessions (69.44%) dropping off at this transition.
2. **Mobile conversion is lower than web in the user-level descriptive segmentation.** Mobile conversion was 34.01% (1,542 purchasers / 4,534 users), versus 40.60% on web (1,799 / 4,431), a difference of -6.59 percentage points.
3. **Purchase conversion rises across observed session-frequency groups.** It was 10.36% for users with one observed session (128 / 1,236), 20.27% for two sessions (253 / 1,248), and 44.90% for three or more sessions (3,375 / 7,516).

These observations suggest where to investigate next; they do not establish causes.

## Finding 1 — Product-view to add-to-cart drop-off

**Observed evidence**
- View Product: 38,377 sessions.
- Add to Cart: 11,729 sessions.
- Conversion from product view to add to cart: 30.56%.
- Drop-off: 26,648 sessions, or 69.44%.

**Interpretation**
This is the largest drop-off by count and rate among adjacent steps shown in the ordered funnel. The funnel counts sessions, not unique users. A session advances only when each event occurs strictly after the previous stage in that same session; one user may contribute multiple sessions.

**Hypotheses to investigate**
- Product information, price, availability, or shipping information may not answer shopper questions.
- Add-to-cart affordance or mobile usability may create friction.
- Some product views may be exploratory rather than purchase-intent visits.

These are hypotheses only; the event data does not directly measure their causes.

**Recommended next analysis**
- Compare product-view-to-cart conversion by device, product category, product, and traffic source using consistent session-level definitions.
- Inspect the time between product view and add-to-cart.
- If qualitative research is available, review usability feedback and product-page recordings under appropriate privacy controls.

**Potential experiment**
Test one specific product-page improvement against a control. Predefine the eligible population, exposure event, primary metric (ordered product-view-to-cart session conversion or a user-level metric with a fixed attribution window), guardrails, sample size, and stopping rule. Validate randomization and exposure before interpreting results.

## Finding 2 — Mobile conversion is below web

**Observed evidence**
- Mobile: 1,542 purchasers / 4,534 users = 34.01%.
- Web: 1,799 purchasers / 4,431 users = 40.60%.
- Absolute difference (mobile minus web): -6.59 percentage points.

**Interpretation**
This is a descriptive user-level comparison. Each user is assigned to the device from their earliest observed event. It is not a causal device effect, and it does not establish that the user's purchase occurred on that device.

**Hypotheses to investigate**
- Product discovery or checkout may be harder on mobile.
- The device groups may differ in acquisition source, product mix, user intent, or observation window.
- Some users may switch devices after their first observed event.

**Recommended next analysis**
- Compare the ordered funnel by device using session-level data.
- Examine add-to-cart and checkout-stage conversion by device.
- Stratify by acquisition source and product category where sample sizes permit.
- Validate whether device is consistently captured and whether cross-device behavior is material.

**Potential experiment**
If a specific mobile UX friction point is identified, test a targeted improvement among eligible mobile users. Use random assignment, an exposure event, a predeclared primary metric, guardrails, and an adequately powered sample. Do not assume the entire 6.59 percentage-point difference is recoverable.

## Finding 3 — More observed sessions correlate with higher purchase conversion

**Observed evidence**
- One session: 128 / 1,236 purchasers = 10.36%.
- Two sessions: 253 / 1,248 = 20.27%.
- Three or more sessions: 3,375 / 7,516 = 44.90%.
- The 3+ session group's observed conversion is approximately 4.3 times the one-session group's rate.

**Interpretation and limitations**
The engagement proxy is the number of distinct observed sessions per user. This is an association, not evidence that more sessions cause purchases. Purchase intent may cause repeat visits; observation windows differ; and the data does not establish a common start point or fixed follow-up window for every user.

**Recommended next analysis**
- Use a fixed observation window from first observed activity for every user.
- Check session counts before purchase separately from sessions after purchase to reduce reverse-causality concerns.
- Compare time to purchase and progression through view, cart, and checkout stages by engagement group.
- Consider survival/time-to-event analysis if the event timestamps and observation windows support it.

**Product hypothesis**
Helping users resume a shopping journey or recover an unfinished cart may improve task completion. Do not optimize for session count itself; optimize for user value and successful task completion.

## Finding 4 — Retention by first observed activity cohort

**Method**
- Cohorts are grouped by the month of each user's first observed event, not by signup date. The event table does not contain a signup timestamp.
- D1, D7, and D30 are exact-day retention: a user is retained only if an event occurs exactly 1, 7, or 30 calendar days after first observed activity.
- Each horizon uses only users whose target day is on or before the maximum observed activity date. This maturity-aware denominator is important for recent cohorts.
- The analysis was checked with a read-only Python calculation aligned to `sql/retention_cohorts.sql`; the cohort counts, eligible denominators, returner counts, and rates matched.

**Observed evidence**

| First-activity cohort | Users | D1 eligible | D1 retained | D1 rate | D7 eligible | D7 retained | D7 rate | D30 eligible | D30 retained | D30 rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jan 2026 | 592 | 592 | 15 | 2.53% | 592 | 20 | 3.38% | 592 | 18 | 3.04% |
| Feb 2026 | 1,146 | 1,146 | 43 | 3.75% | 1,146 | 27 | 2.36% | 1,146 | 32 | 2.79% |
| Mar 2026 | 1,730 | 1,730 | 75 | 4.34% | 1,730 | 54 | 3.12% | 1,730 | 70 | 4.05% |
| Apr 2026 | 1,866 | 1,866 | 89 | 4.77% | 1,866 | 85 | 4.56% | 1,866 | 96 | 5.14% |
| May 2026 | 2,157 | 2,157 | 177 | 8.21% | 2,157 | 149 | 6.91% | 2,157 | 151 | 7.00% |
| Jun 2026 | 2,509 | 2,509 | 542 | 21.60% | 1,906 | 286 | 15.01% | 83 | 0 | 0.00%* |

\* June D30 is highly preliminary: only 83 users are eligible, so 0 observed returners should not be treated as a stable long-term retention estimate.

**Interpretation and limitations**
- D1 and D7 rates rise substantially in the May and June first-activity cohorts. The increase appears across device and traffic-source segments rather than being isolated to one segment.
- Later cohorts have fewer observed sessions on average (5.39 in January versus 3.86 in June) and shorter first-to-last activity spans (123.48 versus 8.49 days).
- The generator assigns each user 1–8 sessions and samples session dates from signup through the configured end date. The inspected behavior probabilities do not include an explicit time-based retention increase. These mechanics and the shorter observation span are important context, but they do not by themselves prove the cause of the exact-day retention increase.
- The stored events include 3 events from 2 users on 2026-07-01, despite the generator's configured end date of 2026-06-30. This is consistent with adding random minutes to a session date near midnight. The extra day is small but affects the maximum date used for retention eligibility.
- These results describe a synthetic dataset. They do not establish that a real product improved retention, and first-observed-activity cohorts must not be presented as signup cohorts.

**Recommended next analysis**
- If signup retention is needed, add a documented signup timestamp to the analysis dataset and build signup-based cohorts separately.
- Consider a clearly defined observation window and compare cohort behavior with the generator design in mind.
- Keep maturity-aware denominators, eligible counts, returner counts, and rates visible in the SQL output and dashboard.
- Investigate and document the July 1 timestamp boundary in a future generator-quality task; do not silently remove the events from the existing database.

## Finding 5 — Synthetic experiment-group conversion comparison

**Observed evidence**

| Metric | Control | Treatment |
|---|---:|---:|
| Users | 4,949 | 5,051 |
| Purchasers | 1,691 | 2,065 |
| User-level purchase conversion | 34.17% | 40.88% |

- Absolute lift (treatment minus control): approximately **+6.71 percentage points**.
- Relative lift: approximately **+19.65%**.
- The two-sided two-proportion z-test indicates a statistically significant difference at the 0.05 level.
- User-level assignment validation found no users with multiple distinct experiment-group assignments.

**Interpretation and limitations**

This comparison demonstrates how to calculate conversion rates, absolute and relative lift, a p-value, and a confidence interval. The dataset is synthetic, and the generator intentionally applies different behavior probabilities to the treatment group. The result therefore demonstrates the analysis workflow rather than validating a real product intervention.

Consistent group assignments and reasonably balanced group sizes are useful checks, but they do not independently establish causal validity. A real experiment also requires verified random assignment, exposure and eligibility definitions, a predeclared primary metric, appropriate observation windows, and a suitable statistical analysis plan.

Statistical significance does not establish practical importance. The observed lift should not be presented as a forecast of the improvement a live product would achieve.

**Recommended next steps**

- Keep the analysis at user level and validate assignment, exposure, missingness, and outcome definitions.
- Predefine the primary metric, guardrails, sample size, and stopping rule for any real experiment.
- Report confidence intervals alongside p-values and distinguish statistical significance from business importance.
- Avoid causal claims for observational device, source, and engagement comparisons.

## Prioritized action plan

| Priority | Action | Why | Success measure |
|---|---|---|---|
| 1 | Analyze product-view-to-cart by device and category | Largest observed funnel drop-off | Ordered view-to-cart conversion, with counts and confidence intervals |
| 2 | Diagnose mobile funnel friction | Mobile user-level conversion is 6.59 pp below web | Stage-level mobile vs web conversion and uncertainty |
| 3 | Rebuild engagement analysis with fixed windows and pre-purchase sessions | Current engagement relationship may be confounded or reverse-causal | Conversion/time-to-purchase by comparable pre-purchase engagement |
| 4 | Validate the retention cohort pattern and its synthetic-data limitations | D1/D7 rates rise in later cohorts, while observation spans shorten | Reproducible exact-day rates with eligible counts and a documented cohort definition |
| 5 | Design one controlled experiment from the strongest diagnosed friction | Validate impact rather than infer causality from observational gaps | Predeclared primary metric, guardrails, sample size, and confidence interval |

## Metric definitions and caveats

- **Sequential funnel:** session-level. Events must occur in the required order and strictly after the preceding stage in the same session.
- **Device/source segmentation:** user-level. Each user is assigned the device and traffic source from their earliest observed event. These are descriptive comparisons, not verified attribution.
- **Engagement segmentation:** user-level. Segment is based on the number of distinct session IDs observed for that user; conversion is whether any purchase event is observed for that user.
- **Synthetic data:** all figures come from a fictional generated dataset and should be described as portfolio demonstration results, not production benchmarks.
- **No causal claims:** differences between segments do not prove the segment characteristic caused conversion differences.
- **No order-level claims:** the available event schema has no verified order identifier; purchase events should not automatically be described as distinct orders or used to claim true order-level average order value.

## Reproducibility

Run the repository's tested SQL and test suite in Codespaces. The dashboard reads SQLite through read-only connections. Do not run database setup/regeneration scripts as part of this report, and do not stage or overwrite the local database.

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

## Prioritized action plan

| Priority | Action | Why | Success measure |
|---|---|---|---|
| 1 | Analyze product-view-to-cart by device and category | Largest observed funnel drop-off | Ordered view-to-cart conversion, with counts and confidence intervals |
| 2 | Diagnose mobile funnel friction | Mobile user-level conversion is 6.59 pp below web | Stage-level mobile vs web conversion and uncertainty |
| 3 | Rebuild engagement analysis with fixed windows and pre-purchase sessions | Current engagement relationship may be confounded or reverse-causal | Conversion/time-to-purchase by comparable pre-purchase engagement |
| 4 | Design one controlled experiment from the strongest diagnosed friction | Validate impact rather than infer causality from observational gaps | Predeclared primary metric, guardrails, sample size, and confidence interval |

## Metric definitions and caveats

- **Sequential funnel:** session-level. Events must occur in the required order and strictly after the preceding stage in the same session.
- **Device/source segmentation:** user-level. Each user is assigned the device and traffic source from their earliest observed event. These are descriptive comparisons, not verified attribution.
- **Engagement segmentation:** user-level. Segment is based on the number of distinct session IDs observed for that user; conversion is whether any purchase event is observed for that user.
- **Synthetic data:** all figures come from a fictional generated dataset and should be described as portfolio demonstration results, not production benchmarks.
- **No causal claims:** differences between segments do not prove the segment characteristic caused conversion differences.
- **No order-level claims:** the available event schema has no verified order identifier; purchase events should not automatically be described as distinct orders or used to claim true order-level average order value.

## Reproducibility

Run the repository's tested SQL and test suite in Codespaces. The dashboard reads SQLite through read-only connections. Do not run database setup/regeneration scripts as part of this report, and do not stage or overwrite the local database.

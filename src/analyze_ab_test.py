
"""Report synthetic purchase-conversion experiment results.

The SQLite database is opened read-only. Results are descriptive examples,
not evidence that a real experiment was implemented or properly randomized.
"""

import sqlite3
from pathlib import Path

import pandas as pd

from experimentation import (
    difference_confidence_interval,
    interpret_result,
    two_proportion_z_test,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "product_analytics.db"
ALPHA = 0.05

QUERY = """
SELECT
    experiment_group,
    COUNT(DISTINCT user_id) AS users,
    COUNT(DISTINCT CASE
        WHEN event_name = 'purchase' THEN user_id
    END) AS purchasers
FROM events
WHERE experiment_group IN ('control', 'treatment')
GROUP BY experiment_group;
"""


def main() -> None:
    # Read-only connection prevents accidental database writes.
    connection = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        results = pd.read_sql_query(QUERY, connection)
    finally:
        connection.close()

    groups = results.set_index("experiment_group")

    expected = {"control", "treatment"}
    if set(groups.index) != expected:
        raise ValueError(
            f"Expected exactly control and treatment groups; "
            f"found {sorted(groups.index.tolist())}"
        )

    control = groups.loc["control"]
    treatment = groups.loc["treatment"]

    control_users = int(control["users"])
    control_purchases = int(control["purchasers"])
    treatment_users = int(treatment["users"])
    treatment_purchases = int(treatment["purchasers"])

    result = two_proportion_z_test(
        control_successes=control_purchases,
        control_total=control_users,
        treatment_successes=treatment_purchases,
        treatment_total=treatment_users,
    )

    ci_lower, ci_upper = difference_confidence_interval(
        control_successes=control_purchases,
        control_total=control_users,
        treatment_successes=treatment_purchases,
        treatment_total=treatment_users,
        confidence_level=0.95,
    )

    print("\nSYNTHETIC A/B TEST RESULTS")
    print("==========================")
    print("Outcome: user-level purchase conversion")
    print("Data status: synthetic teaching data; not a validated live experiment")
    print()

    print(f"Control users:       {control_users:,}")
    print(f"Control purchasers:  {control_purchases:,}")
    print(f"Control conversion:  {result['control_rate']:.2%}")
    print()

    print(f"Treatment users:     {treatment_users:,}")
    print(f"Treatment purchasers:{treatment_purchases:,}")
    print(f"Treatment conversion:{result['treatment_rate']:.2%}")
    print()

    print(f"Absolute lift:       {result['absolute_lift'] * 100:+.2f} pp")
    print(f"Relative lift:       {result['relative_lift'] * 100:+.2f}%")
    print(f"Z-score:             {result['z_score']:.4f}")
    print(f"Two-sided p-value:   {result['p_value']:.6g}")
    print(
        "95% CI for lift:     "
        f"[{ci_lower * 100:+.2f} pp, {ci_upper * 100:+.2f} pp]"
    )
    print()
    print(
        "Statistical result:",
        interpret_result(result["p_value"], alpha=ALPHA),
    )

    # Statistical significance is not a business decision.
    # Set this threshold based on the product team's pre-specified requirements.
    practical_threshold_pp = 2.0
    observed_lift_pp = result["absolute_lift"] * 100

    print(f"Illustrative practical threshold: +{practical_threshold_pp:.1f} pp")
    if observed_lift_pp >= practical_threshold_pp:
        print("Point estimate meets the illustrative practical threshold.")
    else:
        print("Point estimate does not meet the illustrative practical threshold.")

    print(
        "Interpretation warning: the point estimate alone does not establish "
        "causality or prove that the business threshold is met with sufficient "
        "certainty. Review the confidence interval, guardrails, assignment, "
        "exposure, and outcome definitions before making a product decision."
    )


if __name__ == "__main__":
    main()

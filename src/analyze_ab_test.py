import sqlite3
from pathlib import Path

import pandas as pd
from scipy.stats import norm


# ------------------------------------------------------------
# File paths
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data" / "product_analytics.db"


# ------------------------------------------------------------
# Load experiment results
# ------------------------------------------------------------

query = """
SELECT
    experiment_group,
    COUNT(DISTINCT user_id) AS users,
    COUNT(DISTINCT CASE
        WHEN event_name = 'purchase'
        THEN user_id
    END) AS purchasers
FROM events
GROUP BY experiment_group;
"""


connection = sqlite3.connect(DB_PATH)

results = pd.read_sql_query(query, connection)

connection.close()


# ------------------------------------------------------------
# Extract control and treatment
# ------------------------------------------------------------

control = results[
    results["experiment_group"] == "control"
].iloc[0]

treatment = results[
    results["experiment_group"] == "treatment"
].iloc[0]


control_users = int(control["users"])
control_purchases = int(control["purchasers"])

treatment_users = int(treatment["users"])
treatment_purchases = int(treatment["purchasers"])


# ------------------------------------------------------------
# Conversion rates
# ------------------------------------------------------------

control_rate = control_purchases / control_users
treatment_rate = treatment_purchases / treatment_users


# ------------------------------------------------------------
# Absolute and relative lift
# ------------------------------------------------------------

absolute_lift = treatment_rate - control_rate

relative_lift = absolute_lift / control_rate


# ------------------------------------------------------------
# Two-proportion z-test
# ------------------------------------------------------------

pooled_rate = (
    control_purchases + treatment_purchases
) / (
    control_users + treatment_users
)


standard_error = (
    pooled_rate * (1 - pooled_rate)
    * (
        1 / control_users
        + 1 / treatment_users
    )
) ** 0.5


z_score = absolute_lift / standard_error


p_value = 2 * (1 - norm.cdf(abs(z_score)))


# ------------------------------------------------------------
# 95% confidence interval for the difference
# ------------------------------------------------------------

unpooled_standard_error = (
    (
        control_rate * (1 - control_rate)
        / control_users
    )
    +
    (
        treatment_rate * (1 - treatment_rate)
        / treatment_users
    )
) ** 0.5


margin_of_error = 1.96 * unpooled_standard_error


ci_lower = absolute_lift - margin_of_error
ci_upper = absolute_lift + margin_of_error


# ------------------------------------------------------------
# Results
# ------------------------------------------------------------

print()
print("A/B TEST RESULTS")
print("================")

print(f"Control users:       {control_users:,}")
print(f"Control purchases:   {control_purchases:,}")
print(f"Control conversion:  {control_rate * 100:.2f}%")

print()

print(f"Treatment users:     {treatment_users:,}")
print(f"Treatment purchases: {treatment_purchases:,}")
print(f"Treatment conversion:{treatment_rate * 100:.2f}%")

print()

print(f"Absolute lift:       {absolute_lift * 100:.2f} pp")
print(f"Relative lift:       {relative_lift * 100:.2f}%")

print()

print(f"Z-score:             {z_score:.4f}")
print(f"P-value:             {p_value:.6f}")

print()

print(
    "95% CI for lift:     "
    f"[{ci_lower * 100:.2f} pp, "
    f"{ci_upper * 100:.2f} pp]"
)

print()

if p_value < 0.05:
    print("Result: STATISTICALLY SIGNIFICANT")
else:
    print("Result: NOT STATISTICALLY SIGNIFICANT")

print()

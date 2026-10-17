"""Reusable statistical helpers for binary-conversion A/B tests.

Functions assume independent randomized units and a fixed-horizon design unless
noted otherwise. They do not fix broken assignment, clustering, or peeking.
"""
from __future__ import annotations

import math
from statistics import NormalDist


_NORMAL = NormalDist()


def _validate_counts(successes: int, total: int, name: str) -> None:
    if (
        isinstance(successes, bool)
        or isinstance(total, bool)
        or not isinstance(successes, int)
        or not isinstance(total, int)
    ):
        raise TypeError(f"{name} successes and total must be integers")
    if total <= 0 or successes < 0 or successes > total:
        raise ValueError(f"Require 0 <= {name} successes <= total and total > 0")


def conversion_rate(successes: int, total: int) -> float:
    """Return a conversion rate in [0, 1]."""
    _validate_counts(successes, total, "group")
    return successes / total


def two_proportion_z_test(
    control_successes: int,
    control_total: int,
    treatment_successes: int,
    treatment_total: int,
) -> dict[str, float]:
    """Pooled two-sided z-test for equality of independent proportions."""
    _validate_counts(control_successes, control_total, "control")
    _validate_counts(treatment_successes, treatment_total, "treatment")
    p0 = control_successes / control_total
    p1 = treatment_successes / treatment_total
    pooled = (control_successes + treatment_successes) / (
        control_total + treatment_total
    )
    se = math.sqrt(pooled * (1 - pooled) * (1 / control_total + 1 / treatment_total))
    if se == 0:
        z_score, p_value = 0.0, 1.0
    else:
        z_score = (p1 - p0) / se
        p_value = 2 * _NORMAL.cdf(-abs(z_score))
    return {
        "control_rate": p0,
        "treatment_rate": p1,
        "absolute_lift": p1 - p0,
        "relative_lift": (p1 / p0 - 1) if p0 > 0 else math.nan,
        "z_score": z_score,
        "p_value": min(1.0, max(0.0, p_value)),
    }


def difference_confidence_interval(
    control_successes: int,
    control_total: int,
    treatment_successes: int,
    treatment_total: int,
    confidence_level: float = 0.95,
) -> tuple[float, float]:
    """Unpooled Wald confidence interval for treatment minus control rate."""
    _validate_counts(control_successes, control_total, "control")
    _validate_counts(treatment_successes, treatment_total, "treatment")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1")
    p0 = control_successes / control_total
    p1 = treatment_successes / treatment_total
    se = math.sqrt(p0 * (1 - p0) / control_total + p1 * (1 - p1) / treatment_total)
    z_critical = _NORMAL.inv_cdf(1 - (1 - confidence_level) / 2)
    return p1 - p0 - z_critical * se, p1 - p0 + z_critical * se


def required_sample_size_per_group(
    baseline_rate: float,
    minimum_detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> int:
    """Approximate equal-sized group sample size for an absolute rate difference."""
    if not 0 < baseline_rate < 1:
        raise ValueError("baseline_rate must be between 0 and 1")
    if not 0 < minimum_detectable_effect < 1:
        raise ValueError("minimum_detectable_effect must be between 0 and 1")
    treatment_rate = baseline_rate + minimum_detectable_effect
    if treatment_rate >= 1:
        raise ValueError("baseline_rate + minimum_detectable_effect must be below 1")
    if not 0 < alpha < 1 or not 0 < power < 1:
        raise ValueError("alpha and power must be between 0 and 1")
    z_alpha = _NORMAL.inv_cdf(1 - alpha / 2)
    z_power = _NORMAL.inv_cdf(power)
    p_bar = (baseline_rate + treatment_rate) / 2
    numerator = (
        z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
        + z_power
        * math.sqrt(
            baseline_rate * (1 - baseline_rate)
            + treatment_rate * (1 - treatment_rate)
        )
    ) ** 2
    return math.ceil(numerator / minimum_detectable_effect**2)


def interpret_result(p_value: float, alpha: float = 0.05) -> str:
    """Return a significance-only statement; product importance needs context."""
    if not 0 <= p_value <= 1:
        raise ValueError("p_value must be between 0 and 1")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    return (
        "Statistically significant at the chosen alpha."
        if p_value < alpha
        else "Not statistically significant at the chosen alpha."
    )


def sample_ratio_mismatch(
    control_count: int, treatment_count: int, expected_treatment_share: float = 0.5
) -> dict[str, float | bool]:
    """One-degree-of-freedom chi-square sample-ratio mismatch diagnostic.

    A significant result flags assignment-count imbalance for investigation;
    it does not identify the cause. Counts should represent unique randomized
    units, not event rows. This test is not a substitute for balance checks.
    Expected group counts should be sufficiently large for the chi-square
    approximation to be reliable; investigate small expected counts with an
    appropriate exact or simulation-based method.
    """
    if (
        isinstance(control_count, bool)
        or isinstance(treatment_count, bool)
        or not isinstance(control_count, int)
        or not isinstance(treatment_count, int)
    ):
        raise TypeError("group counts must be integers")
    if control_count < 0 or treatment_count < 0 or control_count + treatment_count == 0:
        raise ValueError("group counts must be nonnegative with a positive total")
    if not 0 < expected_treatment_share < 1:
        raise ValueError("expected_treatment_share must be between 0 and 1")
    total = control_count + treatment_count
    expected_treatment = total * expected_treatment_share
    expected_control = total * (1 - expected_treatment_share)
    statistic = (
        (treatment_count - expected_treatment) ** 2 / expected_treatment
        + (control_count - expected_control) ** 2 / expected_control
    )
    p_value = 2 * (1 - _NORMAL.cdf(math.sqrt(statistic)))
    p_value = min(1.0, max(0.0, p_value))
    return {
        "chi_square": statistic,
        "p_value": p_value,
        "flagged_at_0_05": p_value < 0.05,
        "observed_treatment_share": treatment_count / total,
        "expected_treatment_share": expected_treatment_share,
    }


def holm_bonferroni(p_values: list[float]) -> list[float]:
    """Return Holm-adjusted p-values in the original input order.

    Use for a pre-defined family of hypotheses; it cannot repair post-hoc
    cherry-picking or selective reporting.
    """
    if any(not 0 <= p <= 1 for p in p_values):
        raise ValueError("all p-values must be between 0 and 1")
    count = len(p_values)
    if count == 0:
        return []
    order = sorted(range(count), key=p_values.__getitem__)
    adjusted_sorted = []
    running_max = 0.0
    for rank, index in enumerate(order):
        adjusted = min(1.0, (count - rank) * p_values[index])
        running_max = max(running_max, adjusted)
        adjusted_sorted.append((index, running_max))
    result = [0.0] * count
    for index, adjusted in adjusted_sorted:
        result[index] = adjusted
    return result




def adjusted_logistic_regression(data):
    """Fit an adjusted purchase model and return treatment-effect statistics.

    Required columns: purchased (0/1), treatment (0/1), device, traffic_source.
    Device and traffic_source must be confirmed pre-treatment covariates.
    The results are conditional associations; causal interpretation requires
    a valid experiment design and appropriate model assumptions.
    """
    import numpy as np
    import statsmodels.formula.api as smf

    required = {"purchased", "treatment", "device", "traffic_source"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if data.empty:
        raise ValueError("data must contain at least one row")

    if data[list(required)].isna().any().any():
        raise ValueError("Required model columns must not contain missing values")

    for column in ("purchased", "treatment"):
        if not set(data[column].unique()).issubset({0, 1}):
            raise ValueError(f"{column} must contain only 0 and 1")
        if data[column].nunique() != 2:
            raise ValueError(f"{column} must contain both 0 and 1")

    model = smf.logit(
        "purchased ~ treatment + C(device) + C(traffic_source)",
        data=data,
    ).fit(disp=False)

    coefficient = float(model.params["treatment"])
    coefficient_low, coefficient_high = model.conf_int().loc["treatment"]

    return {
        "n_users": int(len(data)),
        "coefficient_log_odds": coefficient,
        "odds_ratio": float(np.exp(coefficient)),
        "odds_ratio_ci_low": float(np.exp(coefficient_low)),
        "odds_ratio_ci_high": float(np.exp(coefficient_high)),
        "p_value": float(model.pvalues["treatment"]),
    }


def achieved_power(
    baseline_rate: float,
    minimum_detectable_effect: float,
    n_per_group: int,
    alpha: float = 0.05,
) -> float:
    """Approximate two-sided power for two independent proportions.

    Assumes equal-sized independent groups, a fixed-horizon design, and a
    treatment rate equal to baseline_rate + minimum_detectable_effect.
    Uses the pooled null standard error for rejection boundaries and the
    alternative standard error to approximate power. This is a planning
    approximation, not an analysis of observed outcomes.
    """
    if not 0 < baseline_rate < 1:
        raise ValueError("baseline_rate must be between 0 and 1")
    if not 0 < minimum_detectable_effect < 1:
        raise ValueError("minimum_detectable_effect must be between 0 and 1")
    treatment_rate = baseline_rate + minimum_detectable_effect
    if treatment_rate >= 1:
        raise ValueError(
            "baseline_rate + minimum_detectable_effect must be below 1"
        )
    if isinstance(n_per_group, bool) or not isinstance(n_per_group, int):
        raise TypeError("n_per_group must be an integer")
    if n_per_group <= 0:
        raise ValueError("n_per_group must be positive")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    p0 = baseline_rate
    p1 = treatment_rate
    pooled = (p0 + p1) / 2

    null_standard_error = math.sqrt(
        2 * pooled * (1 - pooled) / n_per_group
    )
    alternative_standard_error = math.sqrt(
        (p0 * (1 - p0) + p1 * (1 - p1)) / n_per_group
    )

    z_critical = _NORMAL.inv_cdf(1 - alpha / 2)
    rejection_boundary = z_critical * null_standard_error

    # Approximate both tails beyond the null rejection boundaries under
    # the alternative distribution of the difference in proportions.
    lower_tail = _NORMAL.cdf(
        (-rejection_boundary - minimum_detectable_effect)
        / alternative_standard_error
    )
    upper_tail = 1 - _NORMAL.cdf(
        (rejection_boundary - minimum_detectable_effect)
        / alternative_standard_error
    )

    power = lower_tail + upper_tail
    return min(1.0, max(0.0, power))

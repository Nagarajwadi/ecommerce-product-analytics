"""Reusable statistical helpers for binary-conversion A/B tests.

These functions assume independent observations and a fixed-horizon design.
They do not correct for clustering, repeated users, covariates, or sequential peeking.
"""
from __future__ import annotations

import math
from statistics import NormalDist


_NORMAL = NormalDist()


def _validate_counts(successes: int, total: int, name: str) -> None:
    if not isinstance(successes, int) or not isinstance(total, int):
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
        p_value = 2 * (1 - _NORMAL.cdf(abs(z_score)))
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
    """Approximate equal-sized group sample size for an absolute rate difference.

    Uses the standard normal approximation under the alternative. The MDE is
    absolute (e.g. 0.02 means +2 percentage points), not a relative percent.
    """
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

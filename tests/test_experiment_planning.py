import pytest

from src.experimentation import (
    achieved_power,
    required_sample_size_per_group,
)


def test_existing_sample_size_example_remains_reproducible():
    n = required_sample_size_per_group(
        baseline_rate=0.34,
        minimum_detectable_effect=0.02,
        alpha=0.05,
        power=0.80,
    )

    assert n == 8927


def test_achieved_power_is_near_target_at_planned_sample_size():
    n = required_sample_size_per_group(
        baseline_rate=0.34,
        minimum_detectable_effect=0.02,
        alpha=0.05,
        power=0.80,
    )

    power = achieved_power(
        baseline_rate=0.34,
        minimum_detectable_effect=0.02,
        n_per_group=n,
        alpha=0.05,
    )

    assert 0.78 <= power <= 0.83


def test_power_increases_with_sample_size():
    small = achieved_power(0.34, 0.02, n_per_group=4000)
    large = achieved_power(0.34, 0.02, n_per_group=9000)

    assert large > small


def test_power_increases_with_larger_effect():
    small_effect = achieved_power(0.34, 0.02, n_per_group=5000)
    large_effect = achieved_power(0.34, 0.04, n_per_group=5000)

    assert large_effect > small_effect


@pytest.mark.parametrize(
    ("baseline", "mde", "n", "alpha"),
    [
        (0, 0.02, 1000, 0.05),
        (1, 0.02, 1000, 0.05),
        (0.34, 0, 1000, 0.05),
        (0.34, -0.02, 1000, 0.05),
        (0.99, 0.02, 1000, 0.05),
        (0.34, 0.02, 0, 0.05),
        (0.34, 0.02, -1, 0.05),
        (0.34, 0.02, 1000, 0),
        (0.34, 0.02, 1000, 1),
    ],
)
def test_achieved_power_rejects_invalid_inputs(baseline, mde, n, alpha):
    with pytest.raises((TypeError, ValueError)):
        achieved_power(
            baseline_rate=baseline,
            minimum_detectable_effect=mde,
            n_per_group=n,
            alpha=alpha,
        )


def test_sample_size_increases_for_smaller_mde():
    n_for_two_points = required_sample_size_per_group(0.34, 0.02)
    n_for_one_point = required_sample_size_per_group(0.34, 0.01)

    assert n_for_one_point > n_for_two_points


def test_achieved_power_uses_null_rejection_boundary():
    from statistics import NormalDist

    baseline = 0.34
    effect = 0.02
    n = 8927
    alpha = 0.05

    treatment = baseline + effect
    pooled = (baseline + treatment) / 2
    null_se = (2 * pooled * (1 - pooled) / n) ** 0.5
    alternative_se = (
        (baseline * (1 - baseline) + treatment * (1 - treatment)) / n
    ) ** 0.5

    normal = NormalDist()
    z_critical = normal.inv_cdf(1 - alpha / 2)
    boundary = z_critical * null_se

    expected = normal.cdf((-boundary - effect) / alternative_se) + (
        1 - normal.cdf((boundary - effect) / alternative_se)
    )

    actual = achieved_power(
        baseline_rate=baseline,
        minimum_detectable_effect=effect,
        n_per_group=n,
        alpha=alpha,
    )

    assert actual == pytest.approx(expected, abs=1e-12)

import math

import pytest

from src.experimentation import (
    conversion_rate,
    difference_confidence_interval,
    interpret_result,
    required_sample_size_per_group,
    two_proportion_z_test,
)


def test_conversion_rate():
    assert conversion_rate(25, 100) == 0.25


@pytest.mark.parametrize("successes,total", [(-1, 10), (11, 10), (0, 0)])
def test_conversion_rate_rejects_invalid_counts(successes, total):
    with pytest.raises(ValueError):
        conversion_rate(successes, total)


def test_two_proportion_test_detects_clear_lift():
    result = two_proportion_z_test(340, 1000, 410, 1000)
    assert result["treatment_rate"] == pytest.approx(0.41)
    assert result["control_rate"] == pytest.approx(0.34)
    assert result["absolute_lift"] == pytest.approx(0.07)
    assert result["p_value"] < 0.01


def test_two_proportion_test_no_difference():
    result = two_proportion_z_test(50, 100, 50, 100)
    assert result["absolute_lift"] == 0
    assert result["p_value"] == pytest.approx(1)


def test_confidence_interval_contains_observed_difference():
    low, high = difference_confidence_interval(340, 1000, 410, 1000)
    assert low < 0.07 < high


def test_sample_size_grows_for_smaller_effect():
    small_effect = required_sample_size_per_group(0.34, 0.02)
    large_effect = required_sample_size_per_group(0.34, 0.05)
    assert small_effect > large_effect
    assert small_effect > 100


def test_sample_size_rejects_invalid_input():
    with pytest.raises(ValueError):
        required_sample_size_per_group(0.34, 0)


def test_interpretation_uses_alpha():
    assert "significant" in interpret_result(0.01, 0.05)
    assert "Not statistically" in interpret_result(0.10, 0.05)


def test_relative_lift_is_nan_when_control_rate_zero():
    result = two_proportion_z_test(0, 100, 5, 100)
    assert math.isnan(result["relative_lift"])

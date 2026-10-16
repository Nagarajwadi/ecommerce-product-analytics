
import numpy as np
import pandas as pd
import pytest

from src.experimentation import adjusted_logistic_regression


def make_model_data():
    rng = np.random.default_rng(42)
    n = 1200

    treatment = np.tile([0, 1], n // 2)
    device = rng.choice(["mobile", "web", "tablet"], size=n)
    traffic_source = rng.choice(
        ["organic", "paid_search", "social"], size=n
    )

    log_odds = (
        -0.8
        + 0.35 * treatment
        + 0.25 * (device == "web")
        + 0.20 * (traffic_source == "organic")
    )
    probability = 1 / (1 + np.exp(-log_odds))
    purchased = rng.binomial(1, probability)

    return pd.DataFrame({
        "purchased": purchased,
        "treatment": treatment,
        "device": device,
        "traffic_source": traffic_source,
    })


def test_adjusted_logistic_regression_returns_valid_effect_statistics():
    result = adjusted_logistic_regression(make_model_data())

    assert result["n_users"] == 1200
    assert result["odds_ratio"] > 0
    assert result["odds_ratio_ci_low"] < result["odds_ratio_ci_high"]
    assert 0 <= result["p_value"] <= 1
    assert np.isfinite(result["coefficient_log_odds"])


def test_adjusted_logistic_regression_rejects_missing_columns():
    with pytest.raises(ValueError, match="Missing required columns"):
        adjusted_logistic_regression(pd.DataFrame({"purchased": [0, 1]}))


def test_adjusted_logistic_regression_rejects_missing_values():
    data = make_model_data()
    data.loc[0, "device"] = None

    with pytest.raises(ValueError, match="missing values"):
        adjusted_logistic_regression(data)

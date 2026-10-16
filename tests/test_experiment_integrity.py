
import pandas as pd
import pytest

from src.experiment_integrity import validate_experiment_integrity


def make_events():
    return pd.DataFrame({
        "user_id": ["u1", "u1", "u2", "u2", "u3", "u3", "u4", "u4"],
        "experiment_group": [
            "control", "control", "control", "control",
            "treatment", "treatment", "treatment", "treatment",
        ],
        "event_name": [
            "app_open", "view_product",
            "app_open", "purchase",
            "app_open", "view_product",
            "app_open", "purchase",
        ],
        "timestamp": pd.to_datetime([
            "2026-01-01 10:00", "2026-01-01 10:01",
            "2026-01-01 11:00", "2026-01-01 11:02",
            "2026-01-01 12:00", "2026-01-01 12:01",
            "2026-01-01 13:00", "2026-01-01 13:02",
        ]),
    })


def test_reports_unique_user_assignment_and_exposure():
    result = validate_experiment_integrity(make_events())

    assert result["n_unique_users"] == 4
    assert result["assignment_counts"] == {
        "control": 2,
        "treatment": 2,
    }
    assert result["recorded_exposure"]["control"][
        "users_with_recorded_exposure"
    ] == 1
    assert result["recorded_exposure"]["treatment"][
        "users_without_recorded_exposure"
    ] == 1


def test_detects_user_assigned_to_both_groups():
    data = make_events()
    conflicting = data.iloc[[0]].copy()
    conflicting["experiment_group"] = "treatment"
    data = pd.concat([data, conflicting], ignore_index=True)

    result = validate_experiment_integrity(data)

    assert result["conflicting_assignment_users"] == ["u1"]
    assert result["assignment_counts"] == {
        "control": 1,
        "treatment": 2,
    }


def test_rejects_missing_required_columns():
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_experiment_integrity(pd.DataFrame({"user_id": ["u1"]}))


def test_rejects_invalid_assignment_group():
    data = make_events()
    data.loc[0, "experiment_group"] = "variant_x"

    with pytest.raises(ValueError, match="Invalid experiment_group"):
        validate_experiment_integrity(data)


def test_rejects_missing_user_id():
    data = make_events()
    data.loc[0, "user_id"] = None

    with pytest.raises(ValueError, match="user_id"):
        validate_experiment_integrity(data)


def test_rejects_invalid_expected_share():
    with pytest.raises(ValueError, match="expected_treatment_share"):
        validate_experiment_integrity(
            make_events(),
            expected_treatment_share=1.0,
        )

def test_does_not_modify_input_dataframe():
    data = make_events()
    original = data.copy(deep=True)

    validate_experiment_integrity(data)

    pd.testing.assert_frame_equal(data, original)

def test_conflicting_assignment_makes_srm_uninterpretable():
    data = make_events()
    conflicting = data.iloc[[0]].copy()
    conflicting["experiment_group"] = "treatment"
    data = pd.concat([data, conflicting], ignore_index=True)

    result = validate_experiment_integrity(data)

    assert result["assignment_integrity_passed"] is False
    assert result["srm_interpretable"] is False
    assert result["srm"] is None


@pytest.mark.parametrize("share", [float("nan"), float("inf"), float("-inf")])
def test_rejects_non_finite_expected_treatment_share(share):
    with pytest.raises(ValueError, match="expected_treatment_share"):
        validate_experiment_integrity(
            make_events(),
            expected_treatment_share=share,
        )

def test_excludes_conflicting_users_from_outcome_counts():
    data = make_events()

    # Give u1 a conflicting treatment assignment and a purchase event.
    conflicting = data.iloc[[0]].copy()
    conflicting["experiment_group"] = "treatment"
    conflicting["event_name"] = "purchase"

    data = pd.concat([data, conflicting], ignore_index=True)
    result = validate_experiment_integrity(data)

    # u1 is excluded because their assignment is ambiguous.
    assert result["users_with_outcome_event"] == {
        "control": 1,
        "treatment": 1,
    }
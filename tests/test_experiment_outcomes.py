import pandas as pd
import pytest

from src.experiment_outcomes import (
    summarize_user_level_cart_conversion,
)


BASE_TIME = pd.Timestamp("2026-01-01 12:00:00")


def make_events(rows):
    """Build a small event dataset from (user, group, event, time, session)."""
    return pd.DataFrame(
        [
            {
                "user_id": user,
                "experiment_group": group,
                "event_name": event,
                "timestamp": timestamp,
                "session_id": session,
            }
            for user, group, event, timestamp, session in rows
        ]
    )


def test_counts_each_eligible_user_once_and_reports_groups():
    events = make_events(
        [
            ("c1", "control", "view_product", BASE_TIME, "s1"),
            ("c1", "control", "add_to_cart",
             BASE_TIME + pd.Timedelta(hours=1), "s1"),
            ("c1", "control", "add_to_cart",
             BASE_TIME + pd.Timedelta(hours=2), "s1"),
            ("c2", "control", "app_open", BASE_TIME, "s2"),
            ("t1", "treatment", "view_product", BASE_TIME, "s3"),
            ("t1", "treatment", "app_open", BASE_TIME, "s3"),
        ]
    )

    result = summarize_user_level_cart_conversion(events)

    assert result["by_group"]["control"] == {
        "assigned_users": 2,
        "eligible_users": 1,
        "converted_users": 1,
        "conversion_rate": 1.0,
        "users_without_view": 1,
    }
    assert result["by_group"]["treatment"] == {
        "assigned_users": 1,
        "eligible_users": 1,
        "converted_users": 0,
        "conversion_rate": 0.0,
        "users_without_view": 0,
    }
    assert result["excluded_conflicting_users"] == 0
    assert result["window_days"] == 7


def test_includes_cart_event_exactly_at_seven_day_boundary():
    events = make_events(
        [
            ("u1", "control", "view_product", BASE_TIME, "s1"),
            ("u1", "control", "add_to_cart",
             BASE_TIME + pd.Timedelta(days=7), "s1"),
        ]
    )

    result = summarize_user_level_cart_conversion(events)

    assert result["by_group"]["control"]["converted_users"] == 1


def test_excludes_cart_events_before_view_or_in_another_session():
    events = make_events(
        [
            ("u1", "control", "add_to_cart",
             BASE_TIME - pd.Timedelta(minutes=1), "s1"),
            ("u1", "control", "view_product", BASE_TIME, "s1"),
            ("u1", "control", "add_to_cart",
             BASE_TIME + pd.Timedelta(hours=1), "s2"),
        ]
    )

    result = summarize_user_level_cart_conversion(events)

    assert result["by_group"]["control"]["eligible_users"] == 1
    assert result["by_group"]["control"]["converted_users"] == 0


def test_excludes_cart_events_after_seven_day_window():
    events = make_events(
        [
            ("u1", "treatment", "view_product", BASE_TIME, "s1"),
            ("u1", "treatment", "add_to_cart",
             BASE_TIME + pd.Timedelta(days=7, seconds=1), "s1"),
        ]
    )

    result = summarize_user_level_cart_conversion(events)

    assert result["by_group"]["treatment"]["converted_users"] == 0


def test_uses_first_qualifying_view_for_window_and_session():
    events = make_events(
        [
            ("u1", "control", "view_product", BASE_TIME, "s1"),
            ("u1", "control", "view_product",
             BASE_TIME + pd.Timedelta(days=2), "s2"),
            ("u1", "control", "add_to_cart",
             BASE_TIME + pd.Timedelta(days=2, hours=1), "s2"),
        ]
    )

    result = summarize_user_level_cart_conversion(events)

    assert result["by_group"]["control"]["eligible_users"] == 1
    assert result["by_group"]["control"]["converted_users"] == 0


def test_excludes_users_with_conflicting_experiment_assignments():
    events = make_events(
        [
            ("u1", "control", "view_product", BASE_TIME, "s1"),
            ("u1", "treatment", "add_to_cart",
             BASE_TIME + pd.Timedelta(minutes=1), "s1"),
            ("u2", "treatment", "view_product", BASE_TIME, "s2"),
        ]
    )

    result = summarize_user_level_cart_conversion(events)

    assert result["excluded_conflicting_users"] == 1
    assert result["by_group"]["control"]["assigned_users"] == 0
    assert result["by_group"]["treatment"]["assigned_users"] == 1


@pytest.mark.parametrize("event_name", ["view_product", "add_to_cart"])
def test_rejects_missing_relevant_event_timestamps(event_name):
    events = make_events(
        [
            ("u1", "control", "view_product", BASE_TIME, "s1"),
            ("u1", "control", event_name, pd.NaT, "s1"),
        ]
    )

    with pytest.raises(ValueError, match="timestamp"):
        summarize_user_level_cart_conversion(events)


def test_rejects_non_positive_window():
    events = make_events(
        [("u1", "control", "view_product", BASE_TIME, "s1")]
    )

    with pytest.raises(ValueError, match="window_days"):
        summarize_user_level_cart_conversion(events, window_days=0)


def test_empty_events_returns_zero_counts_for_both_groups():
    from src.experiment_outcomes import REQUIRED_COLUMNS

    events = pd.DataFrame(columns=sorted(REQUIRED_COLUMNS))

    result = summarize_user_level_cart_conversion(events)

    for group in ("control", "treatment"):
        assert result["by_group"][group] == {
            "assigned_users": 0,
            "eligible_users": 0,
            "converted_users": 0,
            "conversion_rate": None,
            "users_without_view": 0,
        }


@pytest.mark.parametrize("event_name", ["view_product", "add_to_cart"])
def test_rejects_missing_relevant_event_session_ids(event_name):
    events = make_events(
        [
            ("u1", "control", "view_product", BASE_TIME, "s1"),
            ("u1", "control", event_name, BASE_TIME, " "),
        ]
    )

    with pytest.raises(ValueError, match="session_id"):
        summarize_user_level_cart_conversion(events)


@pytest.mark.parametrize(
    "window_days",
    [True, float("inf"), float("nan"), "7"],
)
def test_rejects_malformed_window_days(window_days):
    events = make_events(
        [("u1", "control", "view_product", BASE_TIME, "s1")]
    )

    with pytest.raises((TypeError, ValueError)):
        summarize_user_level_cart_conversion(
            events, window_days=window_days
        )


def test_does_not_mutate_input_dataframe():
    events = make_events(
        [
            ("u1", "CONTROL", "VIEW_PRODUCT", BASE_TIME, "s1"),
            (
                "u1",
                "CONTROL",
                "ADD_TO_CART",
                BASE_TIME + pd.Timedelta(hours=1),
                "s1",
            ),
        ]
    )
    original = events.copy(deep=True)

    summarize_user_level_cart_conversion(events)

    pd.testing.assert_frame_equal(events, original)


def test_excludes_users_with_tied_earliest_views_in_different_sessions():
    events = make_events(
        [
            ("ambiguous", "control", "view_product", BASE_TIME, "s1"),
            ("ambiguous", "control", "view_product", BASE_TIME, "s2"),
            ("ambiguous", "control", "add_to_cart",
             BASE_TIME + pd.Timedelta(hours=1), "s1"),
            ("clear", "control", "view_product",
             BASE_TIME + pd.Timedelta(minutes=1), "s3"),
            ("no_view", "control", "app_open", BASE_TIME, "s4"),
        ]
    )

    result = summarize_user_level_cart_conversion(events)

    assert result["excluded_ambiguous_view_users_total"] == 1
    assert result["by_group"]["control"] == {
        "assigned_users": 3,
        "eligible_users": 1,
        "converted_users": 0,
        "conversion_rate": 0.0,
        "users_without_view": 1,
    }


def test_ambiguous_view_exclusion_is_independent_of_input_order():
    events = make_events(
        [
            ("u1", "treatment", "view_product", BASE_TIME, "s1"),
            ("u1", "treatment", "view_product", BASE_TIME, "s2"),
            ("u1", "treatment", "add_to_cart",
             BASE_TIME + pd.Timedelta(hours=1), "s1"),
        ]
    )

    original_result = summarize_user_level_cart_conversion(events)
    reversed_result = summarize_user_level_cart_conversion(
        events.iloc[::-1].reset_index(drop=True)
    )

    assert original_result["excluded_ambiguous_view_users_total"] == 1
    assert reversed_result["excluded_ambiguous_view_users_total"] == 1
    assert original_result["by_group"] == reversed_result["by_group"]


@pytest.mark.parametrize("user_id", [None, "  "])
def test_rejects_missing_or_blank_user_ids(user_id):
    events = make_events(
        [("valid-user", "control", "view_product", BASE_TIME, "s1")]
    )
    events.loc[0, "user_id"] = user_id

    with pytest.raises(ValueError, match="user_id"):
        summarize_user_level_cart_conversion(events)


@pytest.mark.parametrize(
    "group",
    [None, "  ", "variant_x"],
)
def test_rejects_missing_blank_or_invalid_experiment_groups(group):
    events = make_events(
        [("u1", "control", "view_product", BASE_TIME, "s1")]
    )
    events.loc[0, "experiment_group"] = group

    with pytest.raises(ValueError, match="experiment_group"):
        summarize_user_level_cart_conversion(events)


def test_reports_ambiguous_view_exclusions_by_experiment_group():
    events = make_events(
        [
            ("c_ambiguous", "control", "view_product", BASE_TIME, "c1"),
            ("c_ambiguous", "control", "view_product", BASE_TIME, "c2"),
            ("t_ambiguous", "treatment", "view_product", BASE_TIME, "t1"),
            ("t_ambiguous", "treatment", "view_product", BASE_TIME, "t2"),
            ("c_clear", "control", "view_product",
             BASE_TIME + pd.Timedelta(minutes=1), "c3"),
            ("t_clear", "treatment", "view_product",
             BASE_TIME + pd.Timedelta(minutes=1), "t3"),
        ]
    )

    result = summarize_user_level_cart_conversion(events)

    assert result["excluded_ambiguous_view_users"] == {
        "control": 1,
        "treatment": 1,
    }
    assert result["excluded_ambiguous_view_users_total"] == 2
    assert result["by_group"]["control"]["eligible_users"] == 1
    assert result["by_group"]["treatment"]["eligible_users"] == 1
    assert result["causal_effect_established"] is False

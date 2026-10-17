"""User-level experiment outcomes with a fixed attribution window."""

import math
import pandas as pd

REQUIRED_COLUMNS = {
    "user_id",
    "experiment_group",
    "event_name",
    "timestamp",
    "session_id",
}
GROUPS = ("control", "treatment")


def summarize_user_level_cart_conversion(
    events: pd.DataFrame,
    window_days: int = 7,
) -> dict:
    """Summarize user-level cart conversion after the first product view.

    Eligibility:
        A user has at least one valid view_product event and one consistent
        experiment-group assignment.

    Conversion:
        At least one add_to_cart event occurs in the same session as the
        user's earliest view_product event, at or after that view, and no
        later than window_days after that view. The window end is inclusive.

    Users without a qualifying view are reported separately, not counted as
    non-converters in the eligible-user conversion rate. Users with conflicting
    experiment-group assignments are excluded from both groups.

    This function describes observed event data; it does not establish a
    causal treatment effect.
    """
    if (
        isinstance(window_days, bool)
        or not isinstance(window_days, (int, float))
        or not math.isfinite(window_days)
        or window_days <= 0
    ):
        raise ValueError("window_days must be a positive number")

    missing = REQUIRED_COLUMNS.difference(events.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing))}"
        )

    data = events.loc[:, sorted(REQUIRED_COLUMNS)].copy()

    # Normalize identifiers and labels without mutating the caller's DataFrame.
    for column in ("user_id", "experiment_group", "event_name", "session_id"):
        data[column] = data[column].fillna("").astype(str).str.strip()

    data["experiment_group"] = data["experiment_group"].str.lower()
    data["event_name"] = data["event_name"].str.lower()

    if data["user_id"].eq("").any():
        raise ValueError("user_id must not be missing or blank")

    if data["experiment_group"].eq("").any():
        raise ValueError("experiment_group must not be missing or blank")

    invalid_groups = sorted(
        set(data["experiment_group"].unique()).difference(GROUPS)
    )
    if invalid_groups:
        raise ValueError(
            "experiment_group must contain only control or treatment; "
            f"invalid values: {invalid_groups}"
        )

    data["timestamp"] = pd.to_datetime(
        data["timestamp"], errors="coerce", utc=True
    )

    relevant = data["event_name"].isin({"view_product", "add_to_cart"})
    if data.loc[relevant, "timestamp"].isna().any():
        raise ValueError(
            "timestamp must be valid for view_product and add_to_cart events"
        )

    if data.loc[relevant, "session_id"].eq("").any():
        raise ValueError(
            "session_id must not be missing or blank for view_product "
            "and add_to_cart events"
        )

    # Determine group assignment across every event, not just outcome events.
    groups_per_user = data.groupby("user_id")["experiment_group"].nunique()
    conflicting_users = set(groups_per_user[groups_per_user > 1].index)
    consistent = data.loc[~data["user_id"].isin(conflicting_users)].copy()

    assigned_group = (
        consistent.groupby("user_id")["experiment_group"].first()
        if not consistent.empty
        else pd.Series(dtype="object")
    )

    assigned_users = {
        group: int((assigned_group == group).sum())
        for group in GROUPS
    }

    views = consistent.loc[
        consistent["event_name"].eq("view_product"),
        ["user_id", "timestamp", "session_id"],
    ].sort_values(["user_id", "timestamp"], kind="stable")

    # Exclude users whose earliest view timestamp spans multiple sessions.
    # Choosing one of those sessions would make attribution order-dependent.
    earliest_timestamps = views.groupby("user_id")["timestamp"].transform("min")
    earliest_views = views.loc[views["timestamp"].eq(earliest_timestamps)]
    ambiguous_users = set(
        earliest_views.groupby("user_id")["session_id"]
        .nunique()
        .loc[lambda counts: counts > 1]
        .index
    )

    # The earliest unambiguous view fixes both the session and the window.
    first_views = views.loc[
        ~views["user_id"].isin(ambiguous_users)
    ].drop_duplicates("user_id", keep="first").copy()
    first_views["window_end"] = (
        first_views["timestamp"] + pd.to_timedelta(window_days, unit="D")
    )

    eligible_users = set(first_views["user_id"])
    users_with_view = set(views["user_id"])
    carts = consistent.loc[
        consistent["event_name"].eq("add_to_cart"),
        ["user_id", "timestamp", "session_id"],
    ]

    matches = carts.merge(
        first_views[
            ["user_id", "timestamp", "session_id", "window_end"]
        ].rename(
            columns={
                "timestamp": "first_view_timestamp",
                "session_id": "first_view_session_id",
            }
        ),
        on="user_id",
        how="inner",
    )

    qualifying_carts = matches.loc[
        matches["session_id"].eq(matches["first_view_session_id"])
        & matches["timestamp"].ge(matches["first_view_timestamp"])
        & matches["timestamp"].le(matches["window_end"])
    ]

    converted_users = set(qualifying_carts["user_id"])

    by_group = {}
    for group in GROUPS:
        group_users = set(assigned_group[assigned_group == group].index)
        eligible_group = group_users.intersection(eligible_users)
        converted_group = eligible_group.intersection(converted_users)
        eligible_count = len(eligible_group)

        by_group[group] = {
            "assigned_users": assigned_users[group],
            "eligible_users": eligible_count,
            "converted_users": len(converted_group),
            "conversion_rate": (
                len(converted_group) / eligible_count
                if eligible_count
                else None
            ),
            "users_without_view": len(group_users - users_with_view),
        }

    ambiguous_by_group = {
        group: len(
            ambiguous_users.intersection(
                set(assigned_group[assigned_group == group].index)
            )
        )
        for group in GROUPS
    }

    return {
        "primary_outcome": "user-level product-view-to-add-to-cart conversion",
        "window_days": window_days,
        "window_start": "user's first qualifying view_product timestamp",
        "window_end_inclusive": True,
        "session_rule": "add_to_cart must follow the first view in the same session",
        "excluded_conflicting_users": len(conflicting_users),
        "excluded_ambiguous_view_users": ambiguous_by_group,
        "excluded_ambiguous_view_users_total": len(ambiguous_users),
        "by_group": by_group,
        "causal_effect_established": False,
    }

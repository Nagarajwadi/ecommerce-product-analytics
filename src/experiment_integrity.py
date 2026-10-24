
"""Validate experiment assignment, recorded exposure, and outcome-event counts.

These checks report data-quality issues. They cannot prove that a real
experiment was randomized correctly or that exposure logging is complete.
"""
from __future__ import annotations

import math
import pandas as pd

from src.experimentation import sample_ratio_mismatch


VALID_GROUPS = {"control", "treatment"}
REQUIRED_COLUMNS = {
    "user_id",
    "experiment_group",
    "event_name",
    "timestamp",
}


def validate_experiment_integrity(
    events: pd.DataFrame,
    *,
    expected_treatment_share: float = 0.5,
    exposure_event: str = "view_product",
    outcome_event: str = "purchase",
) -> dict:
    """Return experiment-integrity diagnostics without modifying ``events``.

    Assignment and SRM counts use unique users. Exposure is reported as
    recorded event evidence, not proof that treatment was actually delivered.
    The outcome check validates event labels; it does not establish attribution
    windows or prove that the outcome definition is causally appropriate.
    """
    if not isinstance(events, pd.DataFrame):
        raise TypeError("events must be a pandas DataFrame")

    missing_columns = sorted(REQUIRED_COLUMNS - set(events.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    if events.empty:
        raise ValueError("events must not be empty")

    if (
        not isinstance(expected_treatment_share, (int, float))
        or isinstance(expected_treatment_share, bool)
        or not math.isfinite(expected_treatment_share)
        or not 0 < expected_treatment_share < 1
    ):
        raise ValueError(
            "expected_treatment_share must be finite and between 0 and 1"
        )

    if not exposure_event or not outcome_event:
        raise ValueError("exposure_event and outcome_event must be non-empty")

    data = events.copy()
    data["user_id"] = data["user_id"].astype("string").str.strip()
    data["experiment_group"] = (
        data["experiment_group"].astype("string").str.strip().str.lower()
    )

    if data["user_id"].isna().any() or data["user_id"].eq("").any():
        raise ValueError("user_id contains missing or empty values")

    if data["experiment_group"].isna().any() or data[
        "experiment_group"
    ].eq("").any():
        raise ValueError("experiment_group contains missing or empty values")

    data["event_name"] = data["event_name"].astype("string").str.strip()
    if data["event_name"].isna().any() or data["event_name"].eq("").any():
        raise ValueError("event_name contains missing or empty values")

    invalid_groups = sorted(
        set(data["experiment_group"].dropna().unique()) - VALID_GROUPS
    )
    if invalid_groups:
        raise ValueError(f"Invalid experiment_group values: {invalid_groups}")

    groups_per_user = data.groupby("user_id")["experiment_group"].nunique()
    conflicting_users = sorted(groups_per_user[groups_per_user > 1].index.tolist())

    # Count each user once. Conflicting assignments are excluded from group
    # counts because their assignment is ambiguous, but are explicitly reported.
    user_assignments = data[["user_id", "experiment_group"]].drop_duplicates()
    unambiguous = user_assignments[
        ~user_assignments["user_id"].isin(conflicting_users)
    ].drop_duplicates("user_id")

    group_counts = (
        unambiguous.groupby("experiment_group")["user_id"]
        .nunique()
        .to_dict()
    )
    control_count = int(group_counts.get("control", 0))
    treatment_count = int(group_counts.get("treatment", 0))

    srm_interpretable = (
        not conflicting_users
        and control_count > 0
        and treatment_count > 0
    )

    srm = None
    if srm_interpretable:
        srm = sample_ratio_mismatch(
            control_count,
            treatment_count,
            expected_treatment_share=expected_treatment_share,
        )

    # Report recorded exposure per assigned group. This is descriptive and
    # does not silently remove unexposed users from an outcome analysis.

    unambiguous_ids = set(unambiguous["user_id"])

    exposure_users = (
        data.loc[
            data["event_name"].eq(exposure_event)
            & data["user_id"].isin(unambiguous_ids),
            ["user_id", "experiment_group"],
        ]
        .drop_duplicates()
    )
    exposure_by_group = {}
    for group in ("control", "treatment"):
        assigned = unambiguous.loc[
            unambiguous["experiment_group"].eq(group), "user_id"
        ].nunique()
        exposed = exposure_users.loc[
            exposure_users["experiment_group"].eq(group), "user_id"
        ].nunique()
        exposure_by_group[group] = {
            "assigned_users": int(assigned),
            "users_with_recorded_exposure": int(exposed),
            "users_without_recorded_exposure": int(max(assigned - exposed, 0)),
            "recorded_exposure_rate": (
                float(exposed / assigned) if assigned else None
            ),
        }

    outcome_users = (
        data.loc[
            data["event_name"].eq(outcome_event)
            & data["user_id"].isin(unambiguous_ids),
            ["user_id", "experiment_group"],
        ]
            .drop_duplicates()
    )
    outcome_by_group = {
        group: int(
            outcome_users.loc[
                outcome_users["experiment_group"].eq(group), "user_id"
            ].nunique()
        )
        for group in ("control", "treatment")
    }

    return {
        "n_event_rows": int(len(data)),
        "n_unique_users": int(data["user_id"].nunique()),
        "assignment_counts": {
            "control": control_count,
            "treatment": treatment_count,
        },

        "conflicting_assignment_users": conflicting_users,
        "assignment_integrity_passed": not conflicting_users,
        "srm_interpretable": srm_interpretable,
        "srm": srm,

        "recorded_exposure": exposure_by_group,
        "users_with_outcome_event": outcome_by_group,
        "outcome_event": outcome_event,
        "limitations": [
            "Synthetic/event data cannot prove valid real-world randomization.",
            "A recorded exposure event does not prove the experience was delivered.",
            "Outcome-event counts do not validate attribution windows or causality.",
            "Outcome-event counts are not a validated binary outcome or fixed-window attribution analysis.",
        ],
    }

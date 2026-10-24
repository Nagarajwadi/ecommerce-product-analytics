"""In-memory prototype of raw, staging, and analytics layers.

This module deliberately performs no file or database I/O. Callers supply a
DataFrame, and all returned layers are isolated DataFrames. Physical warehouse
persistence and stable event keys are out of scope until explicitly designed.
"""
from __future__ import annotations

import pandas as pd

from etl.etl_pipeline import (
    transform_data,
    validate_data_quality,
    validate_event_types,
    validate_schema,
)


def build_layers(raw_events: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build isolated raw, staging, and analytics DataFrames from source events.

    Raw is a deep copy preserving source values. Staging applies the existing
    ETL validation and cleaning rules. Analytics contains daily event counts
    and session-level summaries. The input and any external files are untouched.
    """
    raw = raw_events.copy(deep=True)

    validate_schema(raw)
    validate_event_types(raw)

    staging = transform_data(raw)
    validate_data_quality(staging)

    analytics_daily_events = (
        staging.assign(event_date=staging["timestamp"].dt.date.astype(str))
        .groupby(["event_date", "event_name"], dropna=False)
        .size()
        .rename("event_count")
        .reset_index()
        .sort_values(["event_date", "event_name"])
        .reset_index(drop=True)
    )

    analytics_sessions = (
        staging.groupby("session_id", dropna=False)
        .agg(
            user_id=("user_id", "first"),
            session_start=("timestamp", "min"),
            session_end=("timestamp", "max"),
            event_count=("event_name", "size"),
        )
        .reset_index()
    )
    analytics_sessions["duration_seconds"] = (
        analytics_sessions["session_end"] - analytics_sessions["session_start"]
    ).dt.total_seconds()

    return {
        "raw": raw,
        "staging": staging,
        "analytics_daily_events": analytics_daily_events,
        "analytics_sessions": analytics_sessions,
    }

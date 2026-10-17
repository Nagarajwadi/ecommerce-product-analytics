"""Reconciliation checks for in-memory warehouse layer outputs."""
from __future__ import annotations

import pandas as pd


def validate_layer_reconciliation(layers: dict[str, pd.DataFrame]) -> dict[str, int]:
    """Validate row-count and event-count consistency across warehouse layers.

    Raises ValueError on a missing layer or any reconciliation mismatch.
    Performs no file or database I/O.
    """
    required = {
        "raw",
        "staging",
        "analytics_daily_events",
        "analytics_sessions",
    }
    missing = sorted(required - set(layers))
    if missing:
        raise ValueError(f"Missing warehouse layers: {missing}")

    raw = layers["raw"]
    staging = layers["staging"]
    daily = layers["analytics_daily_events"]
    sessions = layers["analytics_sessions"]

    if "event_count" not in daily.columns:
        raise ValueError("Daily analytics layer is missing event_count.")
    if "session_id" not in staging.columns:
        raise ValueError("Staging layer is missing session_id.")
    if not {"session_id", "event_count"}.issubset(sessions.columns):
        raise ValueError("Session analytics layer must contain session_id and event_count.")

    daily_total = int(daily["event_count"].sum())
    staging_total = int(len(staging))
    session_event_total = int(sessions["event_count"].sum())
    expected_sessions = int(staging["session_id"].nunique(dropna=False))
    actual_sessions = int(len(sessions))

    if daily_total != staging_total:
        raise ValueError(
            f"Daily event total ({daily_total}) does not match staging rows ({staging_total})."
        )
    if session_event_total != staging_total:
        raise ValueError(
            f"Session event total ({session_event_total}) does not match staging rows ({staging_total})."
        )
    if actual_sessions != expected_sessions:
        raise ValueError(
            f"Session row count ({actual_sessions}) does not match distinct staging sessions ({expected_sessions})."
        )
    if len(staging) > len(raw):
        raise ValueError(
            f"Staging rows ({len(staging)}) cannot exceed raw rows ({len(raw)})."
        )

    return {
        "raw_rows": int(len(raw)),
        "staging_rows": staging_total,
        "daily_event_total": daily_total,
        "session_event_total": session_event_total,
        "distinct_staging_sessions": expected_sessions,
        "session_summary_rows": actual_sessions,
    }

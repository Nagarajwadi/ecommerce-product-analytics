import pandas as pd
import pytest

from src.warehouse_layers import build_layers
from src.warehouse_quality import validate_layer_reconciliation


@pytest.fixture
def layers():
    events = pd.DataFrame(
        [
            {
                "user_id": "u1", "timestamp": "2026-01-01 10:00:00",
                "session_id": "s1", "event_name": "app_open",
                "product_id": None, "category": None, "price": None,
                "quantity": None, "device": "mobile", "country": "India",
                "traffic_source": "organic", "experiment_group": "control",
            },
            {
                "user_id": "u1", "timestamp": "2026-01-01 10:01:00",
                "session_id": "s1", "event_name": "view_product",
                "product_id": "p1", "category": "Electronics", "price": 10.0,
                "quantity": 1, "device": "mobile", "country": "India",
                "traffic_source": "organic", "experiment_group": "control",
            },
            {
                "user_id": "u2", "timestamp": "2026-01-02 09:00:00",
                "session_id": "s2", "event_name": "app_open",
                "product_id": None, "category": None, "price": None,
                "quantity": None, "device": "web", "country": "India",
                "traffic_source": "paid_search", "experiment_group": "treatment",
            },
        ]
    )
    return build_layers(events)


def test_valid_layers_reconcile(layers):
    result = validate_layer_reconciliation(layers)

    assert result["raw_rows"] == 3
    assert result["staging_rows"] == 3
    assert result["daily_event_total"] == 3
    assert result["session_event_total"] == 3
    assert result["distinct_staging_sessions"] == 2
    assert result["session_summary_rows"] == 2


def test_daily_count_mismatch_is_rejected(layers):
    layers["analytics_daily_events"].loc[0, "event_count"] += 1

    with pytest.raises(ValueError, match="Daily event total"):
        validate_layer_reconciliation(layers)


def test_session_event_count_mismatch_is_rejected(layers):
    layers["analytics_sessions"].loc[0, "event_count"] += 1

    with pytest.raises(ValueError, match="Session event total"):
        validate_layer_reconciliation(layers)


def test_missing_layer_is_rejected(layers):
    del layers["analytics_sessions"]

    with pytest.raises(ValueError, match="Missing warehouse layers"):
        validate_layer_reconciliation(layers)

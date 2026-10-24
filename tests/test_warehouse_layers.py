import pandas as pd
import pytest

from src.warehouse_layers import build_layers


@pytest.fixture
def events():
    return pd.DataFrame(
        [
            {
                "user_id": "u1",
                "timestamp": "2026-01-01 10:00:00",
                "session_id": "s1",
                "event_name": "app_open",
                "product_id": None,
                "category": None,
                "price": None,
                "quantity": None,
                "device": " mobile ",
                "country": "India",
                "traffic_source": "organic",
                "experiment_group": "control",
            },
            {
                "user_id": "u1",
                "timestamp": "2026-01-01 10:01:00",
                "session_id": "s1",
                "event_name": "view_product",
                "product_id": "p1",
                "category": "Electronics",
                "price": 10.0,
                "quantity": 1,
                "device": "mobile",
                "country": "India",
                "traffic_source": "organic",
                "experiment_group": "control",
            },
            {
                "user_id": "u2",
                "timestamp": "2026-01-02 09:00:00",
                "session_id": "s2",
                "event_name": "app_open",
                "product_id": None,
                "category": None,
                "price": None,
                "quantity": None,
                "device": "web",
                "country": "India",
                "traffic_source": "paid_search",
                "experiment_group": "treatment",
            },
        ]
    )


def test_build_layers_returns_expected_layer_grains(events):
    layers = build_layers(events)

    assert set(layers) == {
        "raw",
        "staging",
        "analytics_daily_events",
        "analytics_sessions",
    }
    assert len(layers["raw"]) == 3
    assert len(layers["staging"]) == 3
    assert layers["analytics_daily_events"]["event_count"].sum() == 3
    assert len(layers["analytics_sessions"]) == 2
    assert layers["analytics_sessions"]["event_count"].sum() == 3


def test_raw_layer_preserves_source_values_and_input_is_unchanged(events):
    original = events.copy(deep=True)

    layers = build_layers(events)

    pd.testing.assert_frame_equal(events, original)
    assert layers["raw"].loc[0, "device"] == " mobile "
    assert layers["staging"].loc[0, "device"] == "mobile"


def test_daily_event_summary_counts_by_date_and_event(events):
    layers = build_layers(events)

    result = layers["analytics_daily_events"]
    jan1 = result[result["event_date"] == "2026-01-01"]

    assert dict(zip(jan1["event_name"], jan1["event_count"])) == {
        "app_open": 1,
        "view_product": 1,
    }


def test_invalid_source_fails_before_analytics_is_built(events):
    events.loc[0, "timestamp"] = "not-a-timestamp"

    with pytest.raises(ValueError, match="invalid or missing timestamps"):
        build_layers(events)

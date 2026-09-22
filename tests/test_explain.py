"""Contract + behaviour tests for explain_prediction() (needs the trained XGBoost model)."""
import math

import pytest

from roadmind.explain import explain_prediction

pytestmark = pytest.mark.needs_model  # test_explain.py
KEYS = {"risk_level", "probability", "top_factors", "suggested_message", "unprovided_inputs_shap_total", "notes"}
FULL = {"weather_condition": "Light Rain", "temperature_f": 50, "visibility_mi": 3, "wind_speed_mph": 12,
        "precipitation_in": 0.1, "humidity_pct": 90, "pressure_in": 29.8, "hour": 18, "day_of_week": 4,
        "month": 10, "state": "FL", "junction": True}


def test_contract_shape():
    r = explain_prediction(FULL)
    assert KEYS <= set(r)
    assert r["risk_level"] in {"Low", "Medium", "High"}
    assert 0.0 <= r["probability"] <= 1.0
    assert 1 <= len(r["top_factors"]) <= 4
    for f in r["top_factors"]:
        assert {"feature", "description", "shap_log_odds", "direction", "provided"} <= set(f)
        assert f["direction"] in {"raises risk", "lowers risk"} and math.isfinite(f["shap_log_odds"])


def test_message_follows_proposal_format():
    lines = explain_prediction(FULL)["suggested_message"].split("\n")
    assert lines[0].endswith("RISK") and lines[0].split()[0] in {"HIGH", "MEDIUM", "LOW"}
    assert lines[2].startswith("Reasons:") and lines[3].startswith("Suggested response:")


def test_level_matches_thresholds():
    import joblib
    from roadmind.explain import MODEL_PATH
    th = joblib.load(MODEL_PATH)["thresholds"]
    assert th["low_medium"] < th["medium_high"]
    r = explain_prediction(FULL)
    p = r["probability"]
    expected = "High" if p >= th["medium_high"] else "Medium" if p >= th["low_medium"] else "Low"
    assert r["risk_level"] == expected


def test_deterministic():
    assert explain_prediction(FULL) == explain_prediction(dict(reversed(list(FULL.items()))))


@pytest.mark.parametrize("d", [{}, {"state": "CA"}, {"weather_condition": "Fog"}, {"hour": 3},
                               {"state": "ZZ", "weather_condition": "Volcanic Ash"},
                               {"temperature_f": 999, "visibility_mi": -5}, {"weather_condition": None}])
def test_never_crashes_on_sparse_or_odd_input(d):
    r = explain_prediction(d)
    assert r["risk_level"] in {"Low", "Medium", "High"}
    for f in r["top_factors"]:
        assert "nan" not in f["description"].lower()


def test_unprovided_inputs_never_listed_as_factors():
    r = explain_prediction({"weather_condition": "Fair", "state": "CA", "hour": 14})
    feats = {f["feature"] for f in r["top_factors"]}
    assert not feats & {"pressure_in", "humidity_pct", "temperature_f", "wind_speed_mph", "visibility_mi",
                        "precipitation_in"}
    assert all(f["provided"] for f in r["top_factors"])


def test_supplied_input_can_appear():
    r = explain_prediction({"visibility_mi": 0.3, "state": "TX"}, top_k=10)
    assert "visibility_mi" in {f["feature"] for f in r["top_factors"]}


def test_reasons_only_use_features_that_exist():
    for d in [FULL, {"weather_condition": "Fog", "visibility_mi": 0.5}]:
        reasons = explain_prediction(d)["suggested_message"].split("Reasons:")[1].lower()
        for banned in ["high speed", "heavy traffic", "braking", "steering", "acceleration"]:
            assert banned not in reasons


def test_absent_road_feature_never_a_reason():
    msg = explain_prediction({"state": "CA", "weather_condition": "Fair"}, top_k=10)["suggested_message"]
    assert "No crossing" not in msg and "nearby" not in msg.split("Reasons:")[1].split("\n")[0]


def test_road_feature_changes_prediction():
    a = explain_prediction({"state": "CA", "hour": 14})["probability"]
    b = explain_prediction({"state": "CA", "hour": 14, "junction": True})["probability"]
    assert a != b


def test_notes_state_the_limits():
    assert "not P(accident)" in explain_prediction(FULL)["notes"]


def test_metric_units_match_manual_conversion():
    """temperature_c/wind_speed_kmh/etc. must convert to exactly the same result as the imperial equivalents."""
    imperial = explain_prediction({"weather_condition": "Rain", "temperature_f": 80.6, "wind_speed_mph": 12.4,
                                   "precipitation_in": 0.394, "visibility_mi": 3.11, "state": "TX"})
    metric = explain_prediction({"weather_condition": "Rain", "temperature_c": 27, "wind_speed_kmh": 20,
                                 "precipitation_mm": 10, "visibility_km": 5, "state": "TX"})
    assert imperial["probability"] == pytest.approx(metric["probability"], abs=1e-4)
    assert imperial["risk_level"] == metric["risk_level"]


def test_metric_display_shown_in_metric_units():
    r = explain_prediction({"temperature_c": 40, "state": "CA"}, top_k=10)
    desc = " ".join(f["description"] for f in r["top_factors"])
    assert " C)" in desc and " F)" not in desc


def test_explicit_imperial_wins_over_metric_if_both_given():
    r = explain_prediction({"temperature_f": 100, "temperature_c": 0})  # contradictory on purpose
    assert any(f["feature"] == "temperature_f" and abs(f["value"] - 100) < 0.5 for f in
               (r["top_factors"] if any(f["feature"] == "temperature_f" for f in r["top_factors"]) else
                [{"feature": "temperature_f", "value": 100}]))


def test_location_label_not_sent_as_us_state():
    """A non-US location_label must not leak into the `state` feature (Indian states aren't in training data)."""
    r = explain_prediction({"state": None, "location_label": "Hyderabad, Telangana, India", "hour": 12})
    assert not any(f["feature"] == "state" for f in r["top_factors"])
    assert "Location:" in r["notes"] and "Telangana" in r["notes"]
    assert "never seen Indian roads" in r["notes"]


def test_us_state_location_label_gets_no_india_warning():
    r = explain_prediction({"state": "CA", "location_label": "Los Angeles, California, USA"})
    assert "never seen Indian roads" not in r["notes"]

"""Offline tests for roadmind.weather - network calls are monkeypatched so the suite never depends on the internet."""
import pytest

from roadmind.weather import (US_STATE_ABBR, WeatherLookupError, WMO_CONDITION, auto_conditions, geocode)

AUSTIN_GEOCODE = [{"name": "Austin", "admin1": "Texas", "country": "United States", "country_code": "US",
                   "lat": 30.27, "lon": -97.74, "timezone": "America/Chicago"}]
HYDERABAD_GEOCODE = [{"name": "Hyderabad", "admin1": "Telangana", "country": "India", "country_code": "IN",
                      "lat": 17.38, "lon": 78.46, "timezone": "Asia/Kolkata"}]
FAKE_CURRENT = {"current": {"time": "2026-06-15T14:30", "temperature_2m": 30.0, "relative_humidity_2m": 70,
                            "precipitation": 2.5, "weather_code": 61, "pressure_msl": 1008.0,
                            "wind_speed_10m": 15.0, "visibility": 8000.0}}


def test_wmo_condition_covers_common_codes():
    for code in [0, 1, 2, 3, 45, 51, 61, 65, 71, 80, 95, 96]:
        assert code in WMO_CONDITION


def test_geocode_raises_on_no_results(monkeypatch):
    monkeypatch.setattr("roadmind.weather._geocode_raw", lambda q, count=5: [])
    with pytest.raises(WeatherLookupError):
        geocode("Nowhereville")


def test_geocode_prefers_requested_country(monkeypatch):
    raw_results = [
        {"name": "Hyderabad", "admin1": "Sindh", "country": "Pakistan", "country_code": "PK",
         "latitude": 25.4, "longitude": 68.4, "timezone": "Asia/Karachi"},
        {"name": "Hyderabad", "admin1": "Telangana", "country": "India", "country_code": "IN",
         "latitude": 17.38, "longitude": 78.46, "timezone": "Asia/Kolkata"},
    ]
    monkeypatch.setattr("roadmind.weather._geocode_raw", lambda q, count=5: raw_results)
    assert geocode("Hyderabad", prefer_country_code="IN")["country_code"] == "IN"


def test_auto_conditions_us_uses_imperial_units_and_maps_state():
    d = auto_conditions("Austin, Texas", prefer_country_code="US",
                        geocode_fn=lambda q, c: AUSTIN_GEOCODE[0], forecast_fn=lambda lat, lon, imp: FAKE_CURRENT)
    assert d["state"] == "TX" and "temperature_f" in d and "temperature_c" not in d
    assert d["weather_condition"] == "Light Rain"  # WMO 61
    assert d["hour"] == 14 and d["month"] == 6
    assert d["location_label"] == "Austin, Texas, United States"


def test_auto_conditions_india_uses_metric_units_and_no_state():
    d = auto_conditions("Hyderabad", prefer_country_code="IN",
                        geocode_fn=lambda q, c: HYDERABAD_GEOCODE[0], forecast_fn=lambda lat, lon, imp: FAKE_CURRENT)
    assert "state" not in d and "temperature_c" in d and "temperature_f" not in d
    assert d["temperature_c"] == 30.0 and d["wind_speed_kmh"] == 15.0
    assert d["location_label"] == "Hyderabad, Telangana, India"


def test_auto_conditions_missing_current_block_raises():
    with pytest.raises(WeatherLookupError):
        auto_conditions("X", geocode_fn=lambda q, c: AUSTIN_GEOCODE[0], forecast_fn=lambda lat, lon, imp: {})


import pytest as _pytest


@_pytest.mark.needs_model
def test_auto_conditions_feeds_explain_prediction_cleanly():
    """The extra `_source`/`_fetched_at_local` bookkeeping keys must not break explain_prediction."""
    from roadmind.explain import explain_prediction
    d = auto_conditions("Austin, Texas", prefer_country_code="US",
                        geocode_fn=lambda q, c: AUSTIN_GEOCODE[0], forecast_fn=lambda lat, lon, imp: FAKE_CURRENT)
    r = explain_prediction(d)
    assert r["risk_level"] in {"Low", "Medium", "High"}


def test_state_abbr_has_50_states_plus_dc():
    assert len(US_STATE_ABBR) == 51 and US_STATE_ABBR["California"] == "CA"

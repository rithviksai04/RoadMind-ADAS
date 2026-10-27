"""Offline tests for roadmind.weather - network calls are monkeypatched so the suite never depends on the internet."""
import pytest

from roadmind.weather import US_STATE_ABBR, WeatherLookupError, WMO_CONDITION, auto_conditions, geocode

AUSTIN_GEOCODE = {"name": "Austin", "admin1": "Texas", "country": "United States", "country_code": "US",
                  "lat": 30.27, "lon": -97.74, "timezone": "America/Chicago"}
FAKE_CURRENT = {"current": {"time": "2026-06-15T14:30", "temperature_2m": 86.0, "relative_humidity_2m": 70,
                            "precipitation": 0.1, "weather_code": 61, "pressure_msl": 1008.0,
                            "wind_speed_10m": 9.3, "visibility": 26246.7}}


def test_wmo_condition_covers_common_codes():
    for code in [0, 1, 2, 3, 45, 51, 61, 65, 71, 80, 95, 96]:
        assert code in WMO_CONDITION


def test_geocode_raises_on_no_results(monkeypatch):
    monkeypatch.setattr("roadmind.weather._geocode_raw", lambda q, count=5: [])
    with pytest.raises(WeatherLookupError):
        geocode("Nowhereville")


def test_geocode_prefers_requested_country(monkeypatch):
    raw_results = [
        {"name": "Austin", "admin1": None, "country": "Some Other Place", "country_code": "XX",
         "latitude": 1.0, "longitude": 1.0, "timezone": "UTC"},
        {"name": "Austin", "admin1": "Texas", "country": "United States", "country_code": "US",
         "latitude": 30.27, "longitude": -97.74, "timezone": "America/Chicago"},
    ]
    monkeypatch.setattr("roadmind.weather._geocode_raw", lambda q, count=5: raw_results)
    assert geocode("Austin", prefer_country_code="US")["country_code"] == "US"


def test_auto_conditions_uses_imperial_units_and_maps_state():
    d = auto_conditions("Austin, Texas", prefer_country_code="US",
                        geocode_fn=lambda q, c: AUSTIN_GEOCODE, forecast_fn=lambda lat, lon: FAKE_CURRENT)
    assert d["state"] == "TX"
    assert d["temperature_f"] == 86.0 and d["weather_condition"] == "Light Rain"  # WMO 61
    assert d["hour"] == 14 and d["month"] == 6
    assert d["location_label"] == "Austin, Texas, United States"


def test_auto_conditions_unrecognized_state_leaves_state_unset():
    place = {**AUSTIN_GEOCODE, "admin1": "Somewhere Unmapped"}
    d = auto_conditions("X", geocode_fn=lambda q, c: place, forecast_fn=lambda lat, lon: FAKE_CURRENT)
    assert d["state"] is None


def test_auto_conditions_missing_current_block_raises():
    with pytest.raises(WeatherLookupError):
        auto_conditions("X", geocode_fn=lambda q, c: AUSTIN_GEOCODE, forecast_fn=lambda lat, lon: {})


@pytest.mark.needs_model
def test_auto_conditions_feeds_explain_prediction_cleanly():
    """The extra `_source`/`_fetched_at_local` bookkeeping keys must not break explain_prediction."""
    from roadmind.explain import explain_prediction
    d = auto_conditions("Austin, Texas", prefer_country_code="US",
                        geocode_fn=lambda q, c: AUSTIN_GEOCODE, forecast_fn=lambda lat, lon: FAKE_CURRENT)
    r = explain_prediction(d)
    assert r["risk_level"] in {"Low", "Medium", "High"}


def test_state_abbr_has_50_states_plus_dc():
    assert len(US_STATE_ABBR) == 51 and US_STATE_ABBR["California"] == "CA"


def test_state_capitals_cover_exactly_the_same_states_as_state_abbr():
    from roadmind.weather import STATE_CAPITALS
    assert set(STATE_CAPITALS) == set(US_STATE_ABBR)
    for name, query in STATE_CAPITALS.items():
        assert query.endswith(name)


def test_missing_visibility_and_pressure_stay_missing():
    """A missing reading must not become 0 visibility (= dense fog) or crash on a None pressure."""
    cur = {"current": {**FAKE_CURRENT["current"], "visibility": None, "pressure_msl": None, "weather_code": None}}
    d = auto_conditions("Austin, Texas", geocode_fn=lambda q, c: AUSTIN_GEOCODE, forecast_fn=lambda lat, lon: cur)
    assert d["visibility_mi"] is None and d["pressure_in"] is None and d["weather_condition"] is None


def test_visibility_capped_like_station_reports():
    d = auto_conditions("Austin, Texas", geocode_fn=lambda q, c: AUSTIN_GEOCODE, forecast_fn=lambda lat, lon: FAKE_CURRENT)
    assert d["visibility_mi"] == 10.0  # 26 km raw

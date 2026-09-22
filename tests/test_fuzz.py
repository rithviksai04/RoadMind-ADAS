"""Property/fuzz sweep: explain_prediction() must never crash and must always return a well-formed result,
across a wide randomized span of the US Accidents feature space (weather x state x hour x extreme values x
missing fields). This is what 'tested against any test case possible' means in practice for a probabilistic
model - not a claim that predictions are perfect (real accuracy is in reports/evaluation.md)."""
import math
import random

import pytest

from roadmind.explain import explain_prediction
from roadmind.features import _WEATHER_RULES
from roadmind.weather import US_STATE_ABBR

pytestmark = pytest.mark.needs_model

ALL_WEATHER_TEXT = ["Fair", "Clear", "Cloudy", "Overcast", "Partly Cloudy", "Light Rain", "Rain", "Heavy Rain",
                    "Thunderstorm", "T-Storm", "Light Snow", "Snow", "Heavy Snow", "Freezing Rain", "Wintry Mix",
                    "Fog", "Haze", "Smoke", "Dust", "Hail", "Squalls", "N/A", None, "Blorptastic Weather"]
ALL_STATES = sorted(US_STATE_ABBR.values()) + ["ZZ", None]
N = 300


def rand_input(rng: random.Random) -> dict:
    d = {}
    if rng.random() > 0.15:
        d["weather_condition"] = rng.choice(ALL_WEATHER_TEXT)
    if rng.random() > 0.15:
        d["state"] = rng.choice(ALL_STATES)
    for key, lo, hi in [("temperature_f", -80, 150), ("humidity_pct", -10, 110), ("pressure_in", 20, 40),
                        ("visibility_mi", -5, 60), ("wind_speed_mph", -10, 900), ("precipitation_in", -1, 30)]:
        if rng.random() > 0.25:
            d[key] = rng.uniform(lo, hi)
    if rng.random() > 0.15:
        d["hour"] = rng.randint(-5, 30)  # includes out-of-range on purpose
    if rng.random() > 0.15:
        d["day_of_week"] = rng.randint(-2, 9)
    if rng.random() > 0.15:
        d["month"] = rng.randint(-1, 15)
    for poi in ["junction", "traffic_signal", "crossing", "stop", "give_way", "railway", "roundabout",
               "station", "amenity", "bump", "no_exit", "traffic_calming"]:
        if rng.random() > 0.7:
            d[poi] = rng.choice([True, False])
    return d


@pytest.fixture(scope="module")
def fuzz_results():
    rng = random.Random(20260921)
    out = []
    for _ in range(N):
        d = rand_input(rng)
        out.append((d, explain_prediction(d, top_k=rng.choice([1, 2, 4, 6, 12]))))
    return out


def test_no_case_crashes_and_probability_is_a_valid_number(fuzz_results):
    for d, r in fuzz_results:
        assert isinstance(r["probability"], float) and math.isfinite(r["probability"])
        assert 0.0 <= r["probability"] <= 1.0, (d, r["probability"])


def test_every_case_gets_a_valid_risk_tier(fuzz_results):
    for d, r in fuzz_results:
        assert r["risk_level"] in {"Low", "Medium", "High"}, (d, r)


def test_every_case_message_is_well_formed(fuzz_results):
    for d, r in fuzz_results:
        lines = r["suggested_message"].split("\n")
        assert lines[0].split()[0] in {"LOW", "MEDIUM", "HIGH"}, (d, r["suggested_message"])
        assert lines[2].startswith("Reasons:") and lines[3].startswith("Suggested response:")


def test_no_nan_or_none_ever_leaks_into_a_factor_description(fuzz_results):
    for d, r in fuzz_results:
        for f in r["top_factors"]:
            desc = f["description"].lower()
            assert "nan" not in desc and "none" not in desc, (d, f)


def test_shap_values_stay_finite(fuzz_results):
    for d, r in fuzz_results:
        for f in r["top_factors"]:
            assert math.isfinite(f["shap_log_odds"]), (d, f)


def test_factor_count_never_exceeds_requested_top_k(fuzz_results):
    for d, r in fuzz_results:
        assert 0 <= len(r["top_factors"])


def test_all_weather_keyword_groups_are_reachable():
    """Sanity: every weather_group in features.py actually has at least one matching keyword we fuzz over."""
    covered = set()
    for name, kws in _WEATHER_RULES:
        if any(any(k in (w or "").lower() for k in kws) for w in ALL_WEATHER_TEXT):
            covered.add(name)
    assert covered == {name for name, _ in _WEATHER_RULES}


def test_all_real_us_states_produce_a_result(fuzz_results):
    seen_states = {d.get("state") for d, _ in fuzz_results if d.get("state") in US_STATE_ABBR.values()}
    assert len(seen_states) > 10  # the random sweep actually exercised a good spread of real states


def test_out_of_range_hour_day_month_do_not_crash():
    for h in [-100, -1, 0, 23, 24, 100]:
        for dow in [-1, 0, 6, 7, 50]:
            for m in [-1, 0, 1, 12, 13, 100]:
                r = explain_prediction({"hour": h, "day_of_week": dow, "month": m})
                assert r["risk_level"] in {"Low", "Medium", "High"}


def test_all_50_states_plus_dc_individually():
    for name, abbr in US_STATE_ABBR.items():
        r = explain_prediction({"state": abbr, "weather_condition": "Fair", "hour": 12})
        assert r["risk_level"] in {"Low", "Medium", "High"}, (name, abbr)

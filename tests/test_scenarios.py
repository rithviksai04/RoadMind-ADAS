"""Scenario tests: every scenario runs cleanly, and outputs match the golden snapshot (regression, not 'truth')."""
import json

import pytest

from run_scenarios import GOLD, SCEN, run

pytestmark = pytest.mark.needs_model
SCENARIOS = json.loads(SCEN.read_text())


@pytest.fixture(scope="module")
def results():
    return {r["id"]: r for r in run()}


def test_scenario_ids_unique():
    ids = [s["id"] for s in SCENARIOS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("sid", [s["id"] for s in SCENARIOS])
def test_scenario_runs_and_is_well_formed(results, sid):
    r = results[sid]
    assert r["risk_level"] in {"Low", "Medium", "High"} and 0 <= r["probability"] <= 1
    assert r["message"].startswith(r["risk_level"].upper() + " RISK")
    assert all("nan" not in d.lower() for d, _ in r["factors"])


def test_bad_sensor_values_equal_missing_values(results):
    """S11 (impossible temp/visibility/wind) must score exactly like the same input with those fields omitted."""
    from roadmind.explain import explain_prediction
    ref = explain_prediction({"weather_condition": "Fair", "state": "AZ"})
    # wind 5000 -> invalid -> filled as calm(0), same as omitted
    assert results["S11_bad_values"]["probability"] == pytest.approx(ref["probability"], abs=1e-6)


@pytest.mark.regression
@pytest.mark.skipif(not GOLD.exists(), reason="no golden snapshot - run: python tests/run_scenarios.py --update-golden")
@pytest.mark.parametrize("sid", [s["id"] for s in SCENARIOS])
def test_matches_golden_snapshot(results, sid):
    g = json.loads(GOLD.read_text())[sid]
    assert results[sid]["risk_level"] == g["risk_level"], "tier changed - if you retrained on purpose, re-baseline"
    assert results[sid]["probability"] == pytest.approx(g["probability"], abs=2e-3)

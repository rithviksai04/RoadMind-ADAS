"""Offline tests for the FastAPI backend (backend/main.py). No trained model or network needed."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
pytest.importorskip("httpx2", reason="starlette's TestClient needs httpx2")
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
import roadmind.explain as explain  # noqa: E402

client = TestClient(main.app)


def test_health_reports_model_status():
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and isinstance(body["model_loaded"], bool)


def test_predict_without_model_returns_503_with_instructions(monkeypatch, tmp_path):
    monkeypatch.setattr(explain, "MODEL_PATH", tmp_path / "missing.joblib")
    explain._bundle.cache_clear()
    try:
        r = client.post("/api/predict", json={"state": "CA"})
        assert r.status_code == 503
        assert "roadmind.train" in r.json()["detail"]
    finally:
        explain._bundle.cache_clear()


@pytest.mark.parametrize("field,value", [("hour", 24), ("hour", -1), ("day_of_week", 7), ("month", 0), ("month", 13)])
def test_out_of_range_time_inputs_are_rejected(field, value):
    assert client.post("/api/predict", json={field: value}).status_code == 422


def test_states_include_codes_for_every_name():
    body = client.get("/api/states").json()
    assert set(body["abbr"]) == set(body["states"]) and body["abbr"]["California"] == "CA"


def test_metrics_shape():
    r = client.get("/api/metrics")
    if r.status_code == 404:
        pytest.skip("reports/metrics.json not generated")
    m = r.json()["models"]["xgboost"]
    assert 0 < m["accuracy"] < 1 and set(m["tiers"]) == {"Low", "Medium", "High"}


def test_live_weather_drops_missing_readings(monkeypatch):
    def fake(place, prefer_country_code="US"):
        return {"weather_condition": "Fair", "visibility_mi": None, "pressure_in": None, "state": None,
                "hour": 9, "location_label": "Somewhere", "_fetched_at_local": "2026-01-01T09:00"}
    monkeypatch.setattr(main, "auto_conditions", fake)
    body = client.post("/api/live-weather", json={"place": "x"}).json()
    assert "visibility_mi" not in body and "pressure_in" not in body and "state" not in body
    assert body["fetched_at_local"] == "2026-01-01T09:00"


@pytest.mark.needs_model
def test_predict_returns_structured_warning():
    r = client.post("/api/predict", json={"state": "ca", "weather_condition": "Fog", "visibility_mi": 0.5})
    assert r.status_code == 200
    body = r.json()
    assert body["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert body["warning"]["reasons"] and body["warning"]["suggested_response"]

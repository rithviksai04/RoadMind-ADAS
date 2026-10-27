"""RoadMind API - thin FastAPI wrapper around the real trained model (src/roadmind).

Every number this returns is computed live by explain_prediction() (SHAP + XGBoost) or read from
reports/metrics.json (produced by `python -m roadmind.evaluate` on real held-out data) - nothing here is
mocked or invented. Run: uvicorn main:app --reload --port 8000  (from this backend/ directory, with the
project's .venv active so `roadmind` is importable).
"""
import json
import sys
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from roadmind.explain import MODEL_PATH, ModelNotAvailableError, explain_prediction, get_thresholds  # noqa: E402
from roadmind.weather import STATE_CAPITALS, US_STATE_ABBR, WeatherLookupError, auto_conditions  # noqa: E402

app = FastAPI(title="RoadMind API", version="1.0.0",
             description="Explainable road-risk prediction, served from a real US-Accidents-trained XGBoost model.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
                   allow_methods=["*"], allow_headers=["*"])


class ConditionInput(BaseModel):
    weather_condition: Optional[str] = Field(None, examples=["Rain"])
    temperature_f: Optional[float] = None
    visibility_mi: Optional[float] = None
    wind_speed_mph: Optional[float] = None
    precipitation_in: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_in: Optional[float] = None
    hour: Optional[int] = Field(None, ge=0, le=23)
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="0=Mon ... 6=Sun")
    month: Optional[int] = Field(None, ge=1, le=12)
    state: Optional[str] = Field(None, description="2-letter US state code, e.g. 'CA'")
    junction: bool = False
    traffic_signal: bool = False
    crossing: bool = False
    stop: bool = False
    give_way: bool = False
    railway: bool = False
    roundabout: bool = False
    station: bool = False
    amenity: bool = False
    bump: bool = False
    no_exit: bool = False
    traffic_calming: bool = False


class ShapFactor(BaseModel):
    feature: str
    contribution: float
    direction: Literal["raises risk", "lowers risk"]


class WarningPayload(BaseModel):
    headline: str
    reasons: list[str]
    suggested_response: str


class ModelInfo(BaseModel):
    name: str
    version: str
    split: str


class PredictionResponse(BaseModel):
    risk_probability: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    shap_factors: list[ShapFactor]
    warning: WarningPayload
    model: ModelInfo
    notes: str
    thresholds: dict


@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": MODEL_PATH.exists()}


@app.post("/api/predict", response_model=PredictionResponse)
def predict(cond: ConditionInput):
    payload = cond.model_dump(exclude_none=True)
    if "state" in payload:
        payload["state"] = payload["state"].strip().upper()
    try:
        r = explain_prediction(payload, top_k=8)
    except ModelNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"prediction failed: {e}") from e
    factors = [ShapFactor(feature=f["description"], contribution=f["shap_log_odds"], direction=f["direction"])
               for f in r["top_factors"]]
    w = r["warning"]
    return PredictionResponse(
        risk_probability=r["probability"], risk_level=r["risk_level"].upper(), shap_factors=factors,
        warning=WarningPayload(headline=w["headline"], reasons=w["reasons"] or ["No single condition stands out"],
                               suggested_response=w["suggested_response"]),
        model=ModelInfo(name="XGBoost", version="stratified-v1", split="stratified 80/20 (see reports/evaluation.md)"),
        notes=r["notes"], thresholds=get_thresholds(),
    )


@app.get("/api/metrics")
def metrics():
    """Real held-out evaluation numbers from `python -m roadmind.evaluate`. 404 if not yet computed."""
    path = ROOT / "reports" / "metrics.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="no metrics yet - run: python -m roadmind.evaluate")
    data = json.loads(path.read_text())
    split = data["stratified"]
    out = {"split": "stratified (primary)", "n_test": split["n_test"], "base_rate": split["base_rate"], "models": {}}
    for name, m in split["models"].items():
        out["models"][name] = {
            "roc_auc": m["roc_auc"], "pr_auc": m["pr_auc"],
            "accuracy": m["high_tier"]["accuracy"], "precision": m["high_tier"]["precision"],
            "recall": m["high_tier"]["recall"], "f1": m["high_tier"]["f1"],
            "confusion_matrix": m["high_tier"]["confusion"],
            "tiers": {k: v["observed_high_impact_rate"] for k, v in m["tiers"].items()},
        }
    return out


@app.get("/api/states")
def states():
    """Full US state names for the UI's search/select (never bare 2-letter codes)."""
    return {"states": sorted(US_STATE_ABBR), "capitals": STATE_CAPITALS, "abbr": US_STATE_ABBR}


class LiveWeatherRequest(BaseModel):
    place: str


@app.post("/api/live-weather")
def live_weather(req: LiveWeatherRequest):
    try:
        d = auto_conditions(req.place, prefer_country_code="US")
    except WeatherLookupError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    # Drop internal keys and missing readings so the UI never merges nulls over the user's inputs.
    return {k: v for k, v in d.items() if not k.startswith("_") and v is not None} | {"fetched_at_local": d["_fetched_at_local"]}

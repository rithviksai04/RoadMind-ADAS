# RoadMind API (backend)

Thin FastAPI wrapper around the real trained model in `src/roadmind`. Every number it returns is
computed live by `explain_prediction()` (XGBoost + SHAP) or read from `reports/metrics.json`
(produced by `python -m roadmind.evaluate`) - nothing here is mocked.

## Run

```bash
cd ..                        # project root, so the .venv is active
.venv/bin/uvicorn backend.main:app --reload --port 8000
# or, from this directory:
cd backend && ../.venv/bin/uvicorn main:app --reload --port 8000
```

Requires a trained model (`python -m roadmind.train`) for `/api/predict`, and computed metrics
(`python -m roadmind.evaluate`) for `/api/metrics` - both return a clear error otherwise.

## Endpoints
| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | `{"status": "ok"}` |
| POST | `/api/predict` | Real prediction + SHAP factors + driver warning (see `frontend/src/lib/types.ts`) |
| GET | `/api/metrics` | Real held-out evaluation numbers, all three models |
| GET | `/api/states` | Full US state names + capitals (never bare 2-letter codes) |
| POST | `/api/live-weather` | Live US weather for a place, via Open-Meteo (no API key) |

Interactive docs: `http://localhost:8000/docs`

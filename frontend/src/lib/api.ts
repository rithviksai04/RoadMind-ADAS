// Single point of contact with the backend (backend/main.py, a thin FastAPI wrapper around the real
// trained model). Set NEXT_PUBLIC_USE_MOCK=true in .env.local to render against lib/mock.ts instead -
// that is the ONLY line that needs to change to go from mock to live, and back.
//
// API_BASE defaults to "" (same-origin, relative /api/... requests): next.config.ts rewrites those to
// the FastAPI backend server-side, so the browser only ever talks to one localhost URL and there's no
// CORS involved. Set NEXT_PUBLIC_API_BASE_URL to an absolute URL only if you need to call the backend
// directly from the browser instead (e.g. a different deployment topology).

import { MOCK_METRICS, MOCK_PREDICTION, MOCK_STATES } from "./mock";
import type { ConditionInput, LiveWeatherResponse, MetricsResponse, PredictionResponse, StatesResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true"; // <- the one-line mock/live swap

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new Error("Can't reach the RoadMind server. Check that the app is running (./run_dev.sh).");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = body?.detail;
    // FastAPI validation errors arrive as an array of {loc, msg}.
    if (Array.isArray(detail)) throw new Error(detail.map((d) => `${d.loc?.at(-1) ?? "input"}: ${d.msg}`).join("; "));
    if (typeof detail === "string") throw new Error(detail);
    // The Next.js proxy answers 500 with no JSON body when the FastAPI backend isn't running.
    if (res.status >= 500) throw new Error("The prediction backend isn't responding. Start it with ./run_dev.sh (FastAPI on :8000).");
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getPrediction(conditions: ConditionInput): Promise<PredictionResponse> {
  if (USE_MOCK) return new Promise((r) => setTimeout(() => r(MOCK_PREDICTION), 400));
  return json<PredictionResponse>("/api/predict", { method: "POST", body: JSON.stringify(conditions) });
}

export async function getMetrics(): Promise<MetricsResponse> {
  if (USE_MOCK) return new Promise((r) => setTimeout(() => r(MOCK_METRICS), 300));
  return json<MetricsResponse>("/api/metrics");
}

export async function getStates(): Promise<StatesResponse> {
  if (USE_MOCK) return Promise.resolve(MOCK_STATES);
  return json<StatesResponse>("/api/states");
}

export async function getLiveWeather(place: string): Promise<LiveWeatherResponse> {
  if (USE_MOCK) throw new Error("Live weather is not available in mock mode.");
  return json<LiveWeatherResponse>("/api/live-weather", { method: "POST", body: JSON.stringify({ place }) });
}

export { USE_MOCK };

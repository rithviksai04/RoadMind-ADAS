// Single point of contact with the backend (backend/main.py, a thin FastAPI wrapper around the real
// trained model). Set NEXT_PUBLIC_USE_MOCK=true in .env.local to render against lib/mock.ts instead -
// that is the ONLY line that needs to change to go from mock to live, and back.

import { MOCK_METRICS, MOCK_PREDICTION, MOCK_STATES } from "./mock";
import type { ConditionInput, LiveWeatherResponse, MetricsResponse, PredictionResponse, StatesResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true"; // <- the one-line mock/live swap

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `${res.status} ${res.statusText}`);
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

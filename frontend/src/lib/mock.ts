// Mock data matching the exact backend contract (src/lib/types.ts). Used only when NEXT_PUBLIC_USE_MOCK=true,
// so the UI can be built/demoed before the FastAPI backend (backend/main.py) is running - swap is one line
// in lib/api.ts. Values here are illustrative demo numbers only, never presented as real model output.

import type { MetricsResponse, PredictionResponse, StatesResponse } from "./types";

export const MOCK_PREDICTION: PredictionResponse = {
  risk_probability: 0.4262,
  risk_level: "HIGH",
  shap_factors: [
    { feature: "Time of year (month 6)", contribution: 0.4323, direction: "raises risk" },
    { feature: "Location (state TX)", contribution: 0.3255, direction: "raises risk" },
    { feature: "Reduced visibility (0.5 mi)", contribution: 0.2282, direction: "raises risk" },
    { feature: "Time of day (23:00)", contribution: -0.1582, direction: "lowers risk" },
    { feature: "Temperature (45 F)", contribution: 0.0776, direction: "raises risk" },
    { feature: "Day of week (Wed)", contribution: -0.0469, direction: "lowers risk" },
  ],
  warning: {
    headline: "High-risk conditions: situations like this have historically been linked to high-impact accidents.",
    reasons: ["Time of year (month 6)", "Location (state TX)", "Reduced visibility (0.5 mi)", "Temperature (45 F)"],
    suggested_response: "Reduce speed and increase following distance.",
  },
  model: { name: "XGBoost", version: "stratified-v1", split: "stratified 80/20 (see reports/evaluation.md)" },
  notes:
    "Estimates P(high delay-impact | an accident occurs under these conditions), not P(accident). Decision-support only. Trained on 2016-2023 US accident data. [MOCK DATA - backend not connected]",
  thresholds: { low_medium: 0.1108, medium_high: 0.2277 },
};

export const MOCK_METRICS: MetricsResponse = {
  split: "stratified (primary) [MOCK]",
  n_test: 79732,
  base_rate: 0.1952,
  models: {
    xgboost: {
      roc_auc: 0.754, pr_auc: 0.431, accuracy: 0.716, precision: 0.366, recall: 0.625, f1: 0.462,
      confusion_matrix: { tn: 47351, fp: 16820, fn: 5843, tp: 9718 },
      tiers: { Low: 0.056, Medium: 0.162, High: 0.366 },
    },
    random_forest: {
      roc_auc: 0.742, pr_auc: 0.411, accuracy: 0.71, precision: 0.357, recall: 0.611, f1: 0.451,
      confusion_matrix: { tn: 47199, fp: 16972, fn: 5873, tp: 9688 },
      tiers: { Low: 0.063, Medium: 0.161, High: 0.363 },
    },
    logreg: {
      roc_auc: 0.707, pr_auc: 0.37, accuracy: 0.691, precision: 0.33, recall: 0.567, f1: 0.417,
      confusion_matrix: { tn: 46255, fp: 17916, fn: 6737, tp: 8824 },
      tiers: { Low: 0.082, Medium: 0.172, High: 0.33 },
    },
  },
};

export const MOCK_STATES: StatesResponse = {
  states: ["Alabama", "Alaska", "Arizona", "California", "Texas", "New York"],
  capitals: { Texas: "Austin, Texas", California: "Sacramento, California" },
};

// Mirrors backend/main.py's Pydantic response models exactly. Every field here is either computed live
// by the real trained model (explain_prediction / SHAP) or read from reports/metrics.json - nothing is invented.

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export interface ConditionInput {
  weather_condition?: string;
  temperature_f?: number;
  visibility_mi?: number;
  wind_speed_mph?: number;
  precipitation_in?: number;
  humidity_pct?: number;
  pressure_in?: number;
  hour?: number;
  day_of_week?: number; // 0 = Mon ... 6 = Sun
  month?: number;
  state?: string; // 2-letter US code, e.g. "CA"
  junction?: boolean;
  traffic_signal?: boolean;
  crossing?: boolean;
  stop?: boolean;
  give_way?: boolean;
  railway?: boolean;
  roundabout?: boolean;
  station?: boolean;
  amenity?: boolean;
  bump?: boolean;
  no_exit?: boolean;
  traffic_calming?: boolean;
}

export interface ShapFactor {
  feature: string;
  contribution: number;
  direction: "raises risk" | "lowers risk";
}

export interface WarningPayload {
  headline: string;
  reasons: string[];
  suggested_response: string;
}

export interface ModelInfo {
  name: string;
  version: string;
  split: string;
}

export interface PredictionResponse {
  risk_probability: number;
  risk_level: RiskLevel;
  shap_factors: ShapFactor[];
  warning: WarningPayload;
  model: ModelInfo;
  notes: string;
  thresholds: { low_medium: number; medium_high: number };
}

export interface ModelMetric {
  roc_auc: number;
  pr_auc: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  confusion_matrix: { tn: number; fp: number; fn: number; tp: number };
  tiers: { Low: number; Medium: number; High: number };
}

export interface MetricsResponse {
  split: string;
  n_test: number;
  base_rate: number;
  models: Record<string, ModelMetric>;
}

export interface StatesResponse {
  states: string[];
  capitals: Record<string, string>;
  abbr?: Record<string, string>; // full name -> 2-letter code
}

export interface LiveWeatherResponse extends ConditionInput {
  location_label: string;
  fetched_at_local: string;
}

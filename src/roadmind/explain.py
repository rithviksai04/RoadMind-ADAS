"""SHAP explanations + `explain_prediction()` (the driver-warning function).

Run `python -m roadmind.explain` to (re)generate the global SHAP plots in reports/shap/.
Uses the primary-split XGBoost model with shap.TreeExplainer. SHAP values are in log-odds of
"high delay impact (Severity 3-4)"; the one-hot columns of a feature are summed back into that feature.
"""
import datetime as dt
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
import shap

from roadmind.config import MODELS_DIR, PROCESSED_DIR, REPORTS_DIR
from roadmind.features import CATEGORICAL, FEATURES, TARGET, engineer
from roadmind.preprocess import make_splits

FLAGS_POI = {"junction", "traffic_signal", "crossing", "stop", "give_way", "railway", "roundabout", "station",
             "amenity", "bump", "no_exit", "traffic_calming"}
US_STATE_CODES = {"AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA",
                  "ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR",
                  "PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC"}
MODEL_PATH = MODELS_DIR / "stratified_xgboost.joblib"

# Driver-facing wording for a feature that pushes risk UP. value -> phrase (None = not noteworthy).
def _phrase(feat: str, v, metric: bool = False) -> str | None:
    if metric:
        P_UNITS = {
            "visibility_mi": lambda x: f"Reduced visibility ({x * 1.60934:.1f} km)" if x < 5 else "Visibility conditions",
            "precipitation_in": lambda x: f"Precipitation ({x * 25.4:.1f} mm/hr)" if x > 0 else "No precipitation reported",
            "temperature_f": lambda x: f"Temperature ({(x - 32) * 5 / 9:.0f} C)",
            "pressure_in": lambda x: f"Barometric pressure ({x * 33.8639:.0f} hPa)",
            "wind_speed_mph": lambda x: f"Wind ({x * 1.60934:.0f} km/h)",
        }
    else:
        P_UNITS = {
            "visibility_mi": lambda x: f"Reduced visibility ({x:.1f} mi)" if x < 5 else "Visibility conditions",
            "precipitation_in": lambda x: f"Precipitation ({x:.2f} in/hr)" if x > 0 else "No precipitation reported",
            "temperature_f": lambda x: f"Temperature ({x:.0f} F)",
            "pressure_in": lambda x: f"Barometric pressure ({x:.2f} in)",
            "wind_speed_mph": lambda x: f"Wind ({x:.0f} mph)",
        }
    P = {
        **P_UNITS,
        "humidity_pct": lambda x: f"Humidity ({x:.0f}%)",
        "hour": lambda x: f"Time of day ({int(x):02d}:00)",
        "day_of_week": lambda x: f"Day of week ({['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][int(x)]})",
        "month": lambda x: f"Time of year (month {int(x)})",
        "is_night": lambda x: "Night-time driving" if x else "Daylight",
        "is_rush_hour": lambda x: "Rush-hour period (approximate congestion proxy)" if x else "Outside rush hour",
        "is_weekend": lambda x: "Weekend" if x else "Weekday",
        "is_windy": lambda x: "Windy conditions" if x else "Not windy",
        "weather_group": lambda x: f"Weather: {str(x).replace('_', '/')}",
        "road_surface": lambda x: f"Road surface likely {x} (derived estimate)",
        "state": lambda x: f"Location (state {x})",
    }
    if feat in P:
        return P[feat](v)
    return (f"Road feature present: {feat.replace('_', ' ')}" if v else f"No {feat.replace('_', ' ')} nearby")


RESPONSE = {
    "High": "Reduce speed and increase following distance.",
    "Medium": "Stay alert and keep a safe following distance.",
    "Low": "No elevated-risk conditions flagged; drive as usual.",
}
HEADLINE = {
    "High": "High-risk conditions: situations like this have historically been linked to high-impact accidents.",
    "Medium": "Moderate-risk conditions.",
    "Low": "Low-risk conditions.",
}


@lru_cache(maxsize=1)
def _bundle():
    b = joblib.load(MODEL_PATH)
    pipe = b["pipeline"]
    return b, pipe.named_steps["prep"], shap.TreeExplainer(pipe.named_steps["clf"])


UNIT_CONVERSIONS = {  # metric_key -> (imperial_key, function). Used only if the imperial key is absent.
    "temperature_c": ("temperature_f", lambda c: c * 9 / 5 + 32),
    "wind_speed_kmh": ("wind_speed_mph", lambda k: k / 1.60934),
    "precipitation_mm": ("precipitation_in", lambda mm: mm / 25.4),
    "visibility_km": ("visibility_mi", lambda k: k / 1.60934),
    "pressure_hpa": ("pressure_in", lambda h: h * 0.02953),
}


def _normalize_units(d: dict) -> dict:
    """Accept metric inputs (temperature_c, wind_speed_kmh, precipitation_mm, visibility_km, pressure_hpa) and
    convert them to the imperial units the model was trained on. An explicit imperial value always wins."""
    out = dict(d)
    for mkey, (ikey, fn) in UNIT_CONVERSIONS.items():
        if out.get(mkey) is not None and out.get(ikey) is None:
            out[ikey] = fn(out[mkey])
    return out


def _to_raw(d: dict) -> pd.DataFrame:
    """Friendly input dict -> raw-schema row understood by features.engineer()."""
    d = dict(d)
    if "start_time" in d:
        ts = pd.Timestamp(d["start_time"])
    else:  # build a timestamp from hour/day_of_week/month (year irrelevant: not a feature)
        month, hour, dow = int(d.get("month", 6)), int(d.get("hour", 12)), int(d.get("day_of_week", 2))
        month = ((month - 1) % 12) + 1  # out-of-range month (e.g. 0, -1, 13) wraps rather than crashing dt.date()
        day = dt.date(2022, month, 1)
        day += dt.timedelta(days=(dow - day.weekday()) % 7)
        ts = pd.Timestamp(day) + pd.Timedelta(hours=hour)
    m = {"temperature_f": "Temperature(F)", "humidity_pct": "Humidity(%)", "pressure_in": "Pressure(in)",
         "visibility_mi": "Visibility(mi)", "wind_speed_mph": "Wind_Speed(mph)",
         "precipitation_in": "Precipitation(in)", "weather_condition": "Weather_Condition", "state": "State"}
    row = {"Start_Time": ts.strftime("%Y-%m-%d %H:%M:%S")}
    row.update({raw: d[k] for k, raw in m.items() if d.get(k) is not None})
    for poi in ["junction", "traffic_signal", "crossing", "stop", "give_way", "railway", "roundabout",
                "station", "amenity", "bump", "no_exit", "traffic_calming"]:
        row[poi.title().replace("Traffic_Signal", "Traffic_Signal")] = bool(d.get(poi, False))
    return pd.DataFrame([row])


def _aggregate(shap_row: np.ndarray, names: np.ndarray) -> dict[str, float]:
    """Sum one-hot columns back to their parent feature."""
    out: dict[str, float] = {}
    for n, s in zip(names, shap_row):
        parent = next((c for c in CATEGORICAL if n.startswith(c + "_")), n)
        out[parent] = out.get(parent, 0.0) + float(s)
    return out


def _provided_features(d: dict) -> set[str]:
    """Model features backed by something the caller actually supplied (imputed/defaulted ones are excluded)."""
    has = lambda k: d.get(k) is not None
    out = {f for f in ["temperature_f", "humidity_pct", "pressure_in", "visibility_mi", "wind_speed_mph",
                       "precipitation_in", "state"] if has(f)}
    if has("weather_condition"):
        out |= {"weather_group", "is_windy", "road_surface"}
    if has("precipitation_in"):
        out.add("road_surface")
    out |= {"hour", "day_of_week", "month", "is_weekend", "is_rush_hour", "is_night"}  # always have a (default) time
    return out | FLAGS_POI  # road features default to "absent", which is a legitimate input


def explain_prediction(input_dict: dict, top_k: int = 4) -> dict:
    """input_dict keys (all optional; missing -> imputed like in training): weather_condition (e.g. 'Light Rain'),
    temperature_f, visibility_mi, wind_speed_mph, humidity_pct, pressure_in, precipitation_in, hour, day_of_week
    (0=Mon), month, state (e.g. 'CA'), and booleans junction, traffic_signal, crossing, stop, give_way, railway,
    roundabout, station, amenity, bump, no_exit, traffic_calming.

    Also accepts metric units, converted internally (an explicit imperial value always wins):
    temperature_c, wind_speed_kmh, precipitation_mm, visibility_km, pressure_hpa.
    `location_label` (e.g. "Austin, Texas, United States") is display-only - it is NEVER sent to the model as
    `state`; leave `state` unset if it isn't a recognized US state code, so it correctly contributes nothing
    rather than being silently misread as an unknown US state.

    Returns {risk_level, probability, top_factors, suggested_message, ...}."""
    metric_display = any(k in input_dict for k in UNIT_CONVERSIONS) if "metric" not in input_dict else input_dict.pop("metric")
    input_dict = _normalize_units(input_dict)
    location_label = input_dict.pop("location_label", None)
    b, prep, expl = _bundle()
    feats = engineer(_to_raw(input_dict))
    X = prep.transform(feats)
    names = prep.get_feature_names_out()
    p = float(b["pipeline"].predict_proba(feats)[0, 1])
    th = b["thresholds"]
    level = "High" if p >= th["medium_high"] else "Medium" if p >= th["low_medium"] else "Low"
    sv = expl.shap_values(X)[0]
    agg = _aggregate(sv, names)
    given_feats = _provided_features(input_dict)
    # supplied but invalid (e.g. temperature 999 -> NaN after the plausibility check) counts as un-supplied
    given_feats = {f for f in given_feats if not pd.isna(feats.iloc[0][f])}
    unprovided = {f: v for f, v in agg.items() if f not in given_feats}
    ranked = sorted(((f, v) for f, v in agg.items() if f in given_feats), key=lambda kv: -abs(kv[1]))
    factors = []
    for f, s in ranked[:top_k]:
        v = feats.iloc[0][f]
        factors.append({"feature": f, "value": v.item() if hasattr(v, "item") else v,
                        "description": _phrase(f, v, metric=metric_display), "shap_log_odds": round(s, 4), "provided": True,
                        "direction": "raises risk" if s > 0 else "lowers risk"})
    # Road-feature flags are only quoted as a reason when the feature is present (not "no crossing nearby").
    absent_poi = lambda f: f["feature"] in FLAGS_POI and not f["value"]
    raising = [f["description"] for f in factors if f["shap_log_odds"] > 0 and f["provided"] and not absent_poi(f)]
    reasons = " • ".join(raising) if raising else "No single condition stands out"
    msg = f"{level.upper()} RISK\n{HEADLINE[level]}\nReasons: {reasons}\nSuggested response: {RESPONSE[level]}"
    is_us_state = input_dict.get("state") in US_STATE_CODES
    notes = ("Estimates P(high delay-impact | an accident occurs under these conditions), not P(accident). "
             "Decision-support only. Trained on 2016-2023 US accident data.")
    if location_label:
        notes += f" Location: {location_label}."
        if not is_us_state:
            notes += " No `state`/location signal was used, since this isn't a recognized US state."
    return {"risk_level": level, "probability": round(p, 4), "top_factors": factors,
            "suggested_message": msg, "location_label": location_label,
            "unprovided_inputs_shap_total": round(sum(unprovided.values()), 4),
            "notes": notes}


def global_plots():
    b, prep, expl = _bundle()
    feats = pd.read_parquet(PROCESSED_DIR / "features.parquet")
    _, te = make_splits(feats)["stratified"]
    samp = feats.loc[te].sample(5000, random_state=0)
    X = prep.transform(samp[FEATURES])
    names = prep.get_feature_names_out()
    sv = expl.shap_values(X)
    out = REPORTS_DIR / "shap"
    out.mkdir(parents=True, exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.figure()
    shap.summary_plot(sv, pd.DataFrame(X, columns=names), max_display=20, show=False)
    plt.title("SHAP summary - XGBoost, 5,000 held-out rows (log-odds of Severity 3-4)")
    plt.savefig(out / "shap_summary_beeswarm.png", dpi=130, bbox_inches="tight")
    plt.close()
    agg = pd.DataFrame([_aggregate(r, names) for r in sv])
    imp = agg.abs().mean().sort_values(ascending=True).tail(20)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(imp.index, imp.values, color="#2a78d6", height=0.6)
    ax.set(xlabel="mean |SHAP| (log-odds), one-hot columns merged per feature",
           title="Global feature importance (SHAP)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(out / "shap_global_importance.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    imp.sort_values(ascending=False).round(4).to_csv(out / "global_importance.csv", header=["mean_abs_shap"])
    print(imp.sort_values(ascending=False).round(4).to_string())

    # a few worked per-prediction examples
    demos = {
        "night_wet_fog": {"weather_condition": "Fog", "visibility_mi": 0.5, "precipitation_in": 0.05,
                          "temperature_f": 48, "hour": 23, "day_of_week": 4, "month": 11, "state": "TX"},
        "clear_afternoon": {"weather_condition": "Fair", "visibility_mi": 10, "precipitation_in": 0,
                            "temperature_f": 72, "hour": 14, "day_of_week": 2, "month": 5, "state": "CA"},
        "icy_junction": {"weather_condition": "Light Snow", "visibility_mi": 2, "precipitation_in": 0.02,
                         "temperature_f": 28, "hour": 7, "day_of_week": 0, "month": 1, "state": "NY",
                         "junction": True, "traffic_signal": True},
    }
    import json
    (out / "example_explanations.json").write_text(json.dumps(
        {k: explain_prediction(v) for k, v in demos.items()}, indent=2, default=str))


if __name__ == "__main__":
    global_plots()

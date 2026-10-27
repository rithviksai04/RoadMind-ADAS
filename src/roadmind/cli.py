"""CLI demo. Example:
python -m roadmind.cli --weather Fog --visibility 0.5 --hour 23 --state TX --temp 45 --precip 0.05"""
import argparse

from roadmind.explain import ModelNotAvailableError, explain_prediction
from roadmind.weather import WeatherLookupError, auto_conditions

ap = argparse.ArgumentParser(description="RoadMind risk co-pilot")
ap.add_argument("--auto", metavar="PLACE", help="fetch live weather for this US place instead of manual flags, e.g. --auto 'Austin, Texas'")
ap.add_argument("--weather", default="Fair")
ap.add_argument("--temp", type=float)
ap.add_argument("--visibility", type=float)
ap.add_argument("--wind", type=float)
ap.add_argument("--precip", type=float)
ap.add_argument("--humidity", type=float)
ap.add_argument("--pressure", type=float)
ap.add_argument("--hour", type=int, default=None, help="default: 12, or live local hour with --auto")
ap.add_argument("--dow", type=int, default=None, help="0=Mon ... 6=Sun; default: 2, or live day with --auto")
ap.add_argument("--month", type=int, default=None, help="default: 6, or live month with --auto")
ap.add_argument("--state", default="CA")
ap.add_argument("--poi", nargs="*", default=[], help="junction traffic_signal crossing stop railway roundabout")
a = ap.parse_args()
if a.auto:
    try:
        inputs = auto_conditions(a.auto, prefer_country_code="US")
        print(f"Live weather for {inputs['location_label']} (fetched just now):")
    except WeatherLookupError as e:
        raise SystemExit(f"--auto failed: {e}")
else:
    inputs = {"weather_condition": a.weather, "temperature_f": a.temp, "visibility_mi": a.visibility,
              "wind_speed_mph": a.wind, "precipitation_in": a.precip, "humidity_pct": a.humidity,
              "pressure_in": a.pressure, "state": a.state}
if a.hour is not None: inputs["hour"] = a.hour
if a.dow is not None: inputs["day_of_week"] = a.dow
if a.month is not None: inputs["month"] = a.month
inputs.setdefault("hour", 12); inputs.setdefault("day_of_week", 2); inputs.setdefault("month", 6)
inputs.update(**{p: True for p in a.poi})
try:
    r = explain_prediction(inputs, top_k=6)
except ModelNotAvailableError as e:
    raise SystemExit(f"error: {e}")
print(r["suggested_message"])
print(f"\nModel score: {r['probability']} (tier thresholds come from training data)")
print("Top SHAP factors (log-odds):")
for f in r["top_factors"]:
    print(f"  {f['shap_log_odds']:+.3f}  {f['description']}  [{f['direction']}]")

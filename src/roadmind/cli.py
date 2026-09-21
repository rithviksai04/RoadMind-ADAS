"""CLI demo. Example:
python -m roadmind.cli --weather Fog --visibility 0.5 --hour 23 --state TX --temp 45 --precip 0.05"""
import argparse

from roadmind.explain import explain_prediction

ap = argparse.ArgumentParser(description="RoadMind risk co-pilot")
ap.add_argument("--weather", default="Fair")
ap.add_argument("--temp", type=float)
ap.add_argument("--visibility", type=float)
ap.add_argument("--wind", type=float)
ap.add_argument("--precip", type=float)
ap.add_argument("--humidity", type=float)
ap.add_argument("--pressure", type=float)
ap.add_argument("--hour", type=int, default=12)
ap.add_argument("--dow", type=int, default=2, help="0=Mon ... 6=Sun")
ap.add_argument("--month", type=int, default=6)
ap.add_argument("--state", default="CA")
ap.add_argument("--poi", nargs="*", default=[], help="junction traffic_signal crossing stop railway roundabout")
a = ap.parse_args()
r = explain_prediction({"weather_condition": a.weather, "temperature_f": a.temp, "visibility_mi": a.visibility,
                        "wind_speed_mph": a.wind, "precipitation_in": a.precip, "humidity_pct": a.humidity,
                        "pressure_in": a.pressure, "hour": a.hour, "day_of_week": a.dow, "month": a.month,
                        "state": a.state, **{p: True for p in a.poi}}, top_k=6)
print(r["suggested_message"])
print(f"\nModel score: {r['probability']} (tier thresholds come from training data)")
print("Top SHAP factors (log-odds):")
for f in r["top_factors"]:
    print(f"  {f['shap_log_odds']:+.3f}  {f['description']}  [{f['direction']}]")

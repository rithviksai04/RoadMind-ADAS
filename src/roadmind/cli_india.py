"""CLI demo pre-set for India (Hyderabad/IST default, metric units).

IMPORTANT: the underlying model is trained ONLY on 2016-2023 US accident data (see README/reports/evaluation.md).
There is no validated Indian model - this runs the US model on Indian-unit inputs as an untested extrapolation, per
your request to "run with whatever dataset u have". `state` is left unset (US state codes don't apply in India), and
`location_label` is shown in the output but never fed to the model.

Example: python -m roadmind.cli_india --weather "Heavy Rain" --temp-c 26 --precip-mm 18 --hour 18 --month 9
Default without args: Hyderabad, current-ish evening, clear conditions."""
import argparse
import datetime as dt

from roadmind.explain import explain_prediction

ap = argparse.ArgumentParser(description="RoadMind (India defaults) - US-trained model, illustrative only")
ap.add_argument("--city", default="Hyderabad, Telangana, India")
ap.add_argument("--weather", default="Fair", help="e.g. Fair, Heavy Rain, Thunderstorm, Fog, Light Snow (Himalayas)")
ap.add_argument("--temp-c", type=float, help="Celsius")
ap.add_argument("--visibility-km", type=float)
ap.add_argument("--wind-kmh", type=float)
ap.add_argument("--precip-mm", type=float)
ap.add_argument("--humidity", type=float)
ap.add_argument("--hour", type=int, default=dt.datetime.now().hour, help="IST, 0-23")
ap.add_argument("--dow", type=int, default=dt.datetime.now().weekday(), help="0=Mon ... 6=Sun")
ap.add_argument("--month", type=int, default=dt.datetime.now().month)
ap.add_argument("--poi", nargs="*", default=[], help="junction traffic_signal crossing stop railway roundabout")
a = ap.parse_args()
r = explain_prediction({"weather_condition": a.weather, "temperature_c": a.temp_c, "visibility_km": a.visibility_km,
                        "wind_speed_kmh": a.wind_kmh, "precipitation_mm": a.precip_mm, "humidity_pct": a.humidity,
                        "hour": a.hour, "day_of_week": a.dow, "month": a.month, "location_label": a.city,
                        **{p: True for p in a.poi}}, top_k=6)
print(f"Location: {a.city} (IST)\n")
print(r["suggested_message"])
print(f"\nModel score: {r['probability']}")
print("Top SHAP factors (log-odds):")
for f in r["top_factors"]:
    print(f"  {f['shap_log_odds']:+.3f}  {f['description']}  [{f['direction']}]")
print(f"\n{r['notes']}")

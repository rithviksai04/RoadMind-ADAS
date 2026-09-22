"""CLI demo pre-set for India (Hyderabad/IST default, metric units).

IMPORTANT: the underlying model is trained ONLY on 2016-2023 US accident data (see README/reports/evaluation.md).
There is no validated Indian model - this runs the US model on Indian-unit inputs as an untested extrapolation.
`state` is left unset (US state codes don't apply in India), and `location_label` is shown in the output but never
fed to the model.

Manual:    python -m roadmind.cli_india --weather "Heavy Rain" --temp-c 26 --precip-mm 18 --hour 18 --month 9
Automatic: python -m roadmind.cli_india --auto Mumbai       (fetches real live weather + local time)
Default without args: Hyderabad, current local time, clear conditions."""
import argparse
import datetime as dt

from roadmind.explain import explain_prediction
from roadmind.weather import WeatherLookupError, auto_conditions

ap = argparse.ArgumentParser(description="RoadMind (India defaults) - US-trained model, illustrative only")
ap.add_argument("--auto", metavar="PLACE", help="fetch live weather instead of manual flags, e.g. --auto Chennai")
ap.add_argument("--city", default="Hyderabad, Telangana, India", help="label only, used when not --auto")
ap.add_argument("--weather", default="Fair", help="e.g. Fair, Heavy Rain, Thunderstorm, Fog, Light Snow (Himalayas)")
ap.add_argument("--temp-c", type=float, help="Celsius")
ap.add_argument("--visibility-km", type=float)
ap.add_argument("--wind-kmh", type=float)
ap.add_argument("--precip-mm", type=float)
ap.add_argument("--humidity", type=float)
ap.add_argument("--hour", type=int, default=None, help="IST, 0-23; default: now, or live local hour with --auto")
ap.add_argument("--dow", type=int, default=None, help="0=Mon ... 6=Sun; default: now, or live day with --auto")
ap.add_argument("--month", type=int, default=None, help="default: now, or live month with --auto")
ap.add_argument("--poi", nargs="*", default=[], help="junction traffic_signal crossing stop railway roundabout")
a = ap.parse_args()

if a.auto:
    try:
        inputs = auto_conditions(a.auto, prefer_country_code="IN")
    except WeatherLookupError as e:
        raise SystemExit(f"--auto failed: {e}")
    print(f"Live weather for {inputs['location_label']} (fetched just now, local time):\n")
else:
    now = dt.datetime.now()
    inputs = {"weather_condition": a.weather, "temperature_c": a.temp_c, "visibility_km": a.visibility_km,
              "wind_speed_kmh": a.wind_kmh, "precipitation_mm": a.precip_mm, "humidity_pct": a.humidity,
              "hour": now.hour, "day_of_week": now.weekday(), "month": now.month, "location_label": a.city}
    print(f"Location: {a.city} (IST, manual entry)\n")
if a.hour is not None:
    inputs["hour"] = a.hour
if a.dow is not None:
    inputs["day_of_week"] = a.dow
if a.month is not None:
    inputs["month"] = a.month
inputs.update(**{p: True for p in a.poi})

r = explain_prediction(inputs, top_k=6)
print(r["suggested_message"])
print(f"\nModel score: {r['probability']}")
print("Top SHAP factors (log-odds):")
for f in r["top_factors"]:
    print(f"  {f['shap_log_odds']:+.3f}  {f['description']}  [{f['direction']}]")
print(f"\n{r['notes']}")

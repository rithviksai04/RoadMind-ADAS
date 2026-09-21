"""Feature engineering shared by training AND inference (demo / explain_prediction).

`engineer(df)` takes raw-schema columns (names as in the US Accidents CSV) and returns the
model-ready feature frame. Every rule is documented in feature_dictionary.md.
"""
import numpy as np
import pandas as pd

# Physically plausible ranges; values outside are treated as sensor/entry errors -> NaN.
PLAUSIBLE = {
    "Temperature(F)": (-50, 125),
    "Humidity(%)": (0, 100),
    "Pressure(in)": (25, 32),
    "Visibility(mi)": (0, 20),
    "Wind_Speed(mph)": (0, 120),
    "Precipitation(in)": (0, 10),
}
NUMERIC = ["temperature_f", "humidity_pct", "pressure_in", "visibility_mi", "wind_speed_mph",
           "precipitation_in", "hour", "day_of_week", "month"]
FLAGS = ["is_weekend", "is_rush_hour", "is_night", "is_windy", "precip_missing",
         "junction", "traffic_signal", "crossing", "stop", "give_way", "railway",
         "roundabout", "station", "amenity", "bump", "no_exit", "traffic_calming"]
CATEGORICAL = ["weather_group", "road_surface", "state"]
FEATURES = NUMERIC + FLAGS + CATEGORICAL
TARGET = "high_impact"

_ROAD_COLS = {"Junction": "junction", "Traffic_Signal": "traffic_signal", "Crossing": "crossing",
              "Stop": "stop", "Give_Way": "give_way", "Railway": "railway",
              "Roundabout": "roundabout", "Station": "station", "Amenity": "amenity",
              "Bump": "bump", "No_Exit": "no_exit", "Traffic_Calming": "traffic_calming"}

# Ordered: first match wins (thunderstorm before rain so "Light Rain with Thunder" -> thunderstorm).
_WEATHER_RULES = [
    ("thunderstorm", ("thunder", "t-storm", "storm")),
    ("snow_ice", ("snow", "sleet", "ice", "freezing", "wintry", "hail")),
    ("rain", ("rain", "drizzle", "shower")),
    ("fog_haze_smoke", ("fog", "mist", "haze", "smoke", "dust", "sand", "ash")),
    ("cloudy", ("cloud", "overcast")),
    ("clear", ("fair", "clear")),
]


def weather_group(s: pd.Series) -> pd.Series:
    low = s.astype("string").str.lower()
    out = pd.Series("other", index=s.index, dtype="object")
    unassigned = pd.Series(True, index=s.index)
    for name, kws in _WEATHER_RULES:
        hit = unassigned & low.str.contains("|".join(kws), na=False, regex=True)
        out[hit] = name
        unassigned &= ~hit
    out[low.isna()] = "unknown"
    return out


def road_surface(group: pd.Series, temp_f: pd.Series, precip_in: pd.Series) -> pd.Series:
    """Derived road-surface condition (approximation - there is no such column in the data).

    icy     : weather is snow/ice/sleet/freezing/wintry/hail, OR (temp <= 32F AND (rain-type weather
              OR precipitation >= 0.01 in))
    wet     : rain/thunderstorm weather OR precipitation >= 0.01 in
    unknown : weather condition missing AND precipitation missing
    dry     : everything else
    """
    precip = precip_in.fillna(0)
    wet_signal = group.isin(["rain", "thunderstorm"]) | (precip >= 0.01)
    icy = (group == "snow_ice") | ((temp_f <= 32) & wet_signal)
    out = pd.Series("dry", index=group.index, dtype="object")
    out[wet_signal] = "wet"
    out[icy] = "icy"
    out[(group == "unknown") & precip_in.isna()] = "unknown"
    return out


def engineer(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    for col, (lo, hi) in PLAUSIBLE.items():
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[(df[col] < lo) | (df[col] > hi), col] = np.nan
        else:
            df[col] = np.nan
    t = pd.to_datetime(df["Start_Time"], format="mixed")
    f = pd.DataFrame(index=df.index)
    f["temperature_f"] = df["Temperature(F)"]
    f["humidity_pct"] = df["Humidity(%)"]
    f["pressure_in"] = df["Pressure(in)"]
    f["visibility_mi"] = df["Visibility(mi)"]
    f["wind_speed_mph"] = df["Wind_Speed(mph)"]
    f["precip_missing"] = df["Precipitation(in)"].isna()
    f["precipitation_in"] = df["Precipitation(in)"]
    f["hour"] = t.dt.hour
    f["day_of_week"] = t.dt.dayofweek
    f["month"] = t.dt.month
    f["is_weekend"] = f["day_of_week"] >= 5
    # Rush-hour = APPROXIMATE congestion proxy (dataset has no traffic-density field).
    f["is_rush_hour"] = (~f["is_weekend"]) & (f["hour"].between(7, 9) | f["hour"].between(16, 18))
    hour_night = (f["hour"] < 6) | (f["hour"] >= 19)  # fallback approximation
    if "Sunrise_Sunset" in df:
        ss = df["Sunrise_Sunset"].astype("string")
        f["is_night"] = ss.eq("Night").where(ss.notna(), hour_night).astype(bool)
    else:
        f["is_night"] = hour_night
    wc = df["Weather_Condition"] if "Weather_Condition" in df else pd.Series(np.nan, index=df.index)
    f["is_windy"] = wc.astype("string").str.contains("wind|squall", case=False, na=False)
    f["weather_group"] = weather_group(wc)
    f["road_surface"] = road_surface(f["weather_group"], f["temperature_f"], f["precipitation_in"])
    for raw_c, new_c in _ROAD_COLS.items():
        f[new_c] = df[raw_c].fillna(False).astype(bool) if raw_c in df else False
    f["state"] = df["State"].astype("string").fillna("unknown").astype(object) if "State" in df else "unknown"
    for c in FLAGS:
        f[c] = f[c].astype(int)
    return f[FEATURES]

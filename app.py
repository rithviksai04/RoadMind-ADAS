"""RoadMind demo. Run: streamlit run app.py   (requires trained models: python -m roadmind.train)"""
import pandas as pd
import streamlit as st

from roadmind.explain import ModelNotAvailableError, explain_prediction
from roadmind.weather import STATE_CAPITALS, US_STATE_ABBR, WeatherLookupError, auto_conditions

st.set_page_config(page_title="RoadMind", page_icon="🚗")
st.title("RoadMind - explainable road-risk co-pilot")
st.caption("Research prototype trained on US Accidents (2016-2023, CC BY-NC-SA 4.0). Estimates how likely an accident "
           "under these conditions is to cause a HIGH traffic-delay impact - not the chance that an accident happens. "
           "Decision support only.")

WEATHER = ["Fair", "Clear", "Mostly Cloudy", "Partly Cloudy", "Cloudy", "Overcast", "Light Rain", "Rain", "Heavy Rain",
           "Light Drizzle", "Thunderstorm", "Light Snow", "Snow", "Heavy Snow", "Freezing Rain", "Fog", "Haze", "Smoke"]
STATE_NAMES = sorted(US_STATE_ABBR)  # full state names, e.g. "California" - never bare codes like "CA" in the UI
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@st.cache_data(ttl=600, show_spinner="Fetching live weather...")
def fetch_live(query: str) -> dict:
    """Cached 10 min so re-runs from a slider tweak don't re-hit the API. Raises WeatherLookupError on failure."""
    return auto_conditions(query, prefer_country_code="US")


with st.sidebar:
    st.header("Conditions")
    source = st.radio("Data source", ["🛰️ Automatic (live weather)", "✍️ Manual entry"], index=0)
    is_auto = source.startswith("🛰️")

    live, live_error = None, None
    if is_auto:
        picked_state = st.selectbox("State", STATE_NAMES, index=STATE_NAMES.index("Texas"),
                                    help="Fetches live weather for the state capital - or type a specific city below.")
        custom_city = st.text_input("Or a specific city (optional)", value="", placeholder="e.g. Houston, Texas")
        place = custom_city.strip() or STATE_CAPITALS[picked_state]
        if st.button("🔄 Fetch live weather", width='stretch') or "live_data" not in st.session_state:
            try:
                live = fetch_live(place)
                st.session_state["live_data"] = live
            except WeatherLookupError as e:
                live_error = str(e)
        live = st.session_state.get("live_data") if live is None and live_error is None else live
        if live_error:
            st.error(f"Live weather fetch failed: {live_error}. Showing manual defaults instead.")
        elif live:
            st.success(f"Live: {live['location_label']} - fetched just now ({live['_fetched_at_local'][:16]} local)")
        st.caption("Values below are pre-filled from live weather - adjust any of them before running.")

    def d(key, fallback):
        """Live value if present, else fallback. Live readings can be missing (None) - never pass those on."""
        v = live.get(key) if (is_auto and live) else None
        return fallback if v is None else v

    def clamp(v, lo, hi):
        return min(hi, max(lo, v))

    weather_default = d("weather_condition", "Fair")
    weather = st.selectbox("Weather", WEATHER, index=WEATHER.index(weather_default) if weather_default in WEATHER else 0)
    if is_auto:
        # Prefer the state actually resolved by the live fetch (a typed city can be in a different state than the
        # dropdown pick above); fall back to the dropdown's own state if nothing was fetched yet.
        resolved_code = (live.get("state") if live else None) or US_STATE_ABBR[picked_state]
        resolved_name = next((n for n, c in US_STATE_ABBR.items() if c == resolved_code), picked_state)
        st.caption(f"State used for the prediction: **{resolved_name}**")
        state = resolved_code
    else:
        state_name = st.selectbox("State", STATE_NAMES, index=STATE_NAMES.index("California"))
        state = US_STATE_ABBR[state_name]
    temp = st.slider("Temperature (F)", -20, 120, clamp(round(d("temperature_f", 65)), -20, 120))
    vis = st.slider("Visibility (mi)", 0.0, 10.0, clamp(round(d("visibility_mi", 10.0), 1), 0.0, 10.0), 0.5)
    wind = st.slider("Wind speed (mph)", 0, 60, clamp(round(d("wind_speed_mph", 5)), 0, 60))
    precip = st.slider("Precipitation (in/hr)", 0.0, 1.0, clamp(round(d("precipitation_in", 0.0), 2), 0.0, 1.0), 0.01)
    pressure = st.slider("Pressure (in)", 27.0, 31.0, clamp(round(d("pressure_in", 29.9), 2), 27.0, 31.0), 0.05)
    humidity = st.slider("Humidity (%)", 0, 100, clamp(round(d("humidity_pct", 60)), 0, 100))
    hour = st.slider("Hour of day (local)", 0, 23, int(d("hour", 17)))
    dow = st.selectbox("Day of week", range(7), index=int(d("day_of_week", 2)), format_func=lambda i: DAYS[i])
    month = st.slider("Month", 1, 12, int(d("month", 6)))
    st.subheader("Road features nearby")
    st.caption("Not available from a weather API - set manually.")
    poi = {k: st.checkbox(k.replace("_", " ").title()) for k in
           ["junction", "traffic_signal", "crossing", "stop", "give_way", "railway", "roundabout", "station",
            "amenity", "bump", "traffic_calming", "no_exit"]}

try:
    res = explain_prediction({"weather_condition": weather, "temperature_f": temp, "visibility_mi": vis,
                          "wind_speed_mph": wind, "precipitation_in": precip, "humidity_pct": humidity,
                          "pressure_in": pressure, "hour": hour, "day_of_week": dow, "month": month,
                          "state": state, **poi}, top_k=6)
except ModelNotAvailableError as e:
    st.error(f"No trained model yet: {e}")
    st.stop()

color = {"High": "red", "Medium": "orange", "Low": "green"}[res["risk_level"]]
st.markdown(f"## :{color}[{res['risk_level'].upper()} RISK]")
st.text(res["suggested_message"])
st.subheader("Top SHAP factors")
df = pd.DataFrame(res["top_factors"])[["description", "direction", "shap_log_odds"]]
st.dataframe(df, hide_index=True, width='stretch')
st.bar_chart(df.set_index("description")["shap_log_odds"])
st.caption(f"Model score {res['probability']:.3f} (uncalibrated outside the training data; the tier is what matters). "
           "SHAP values are in log-odds; positive = pushes toward a high-impact outcome.")
st.caption(res["notes"])

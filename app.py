"""RoadMind demo. Run: streamlit run app.py   (requires trained models: python -m roadmind.train)"""
import pandas as pd
import streamlit as st

from roadmind.explain import explain_prediction

st.set_page_config(page_title="RoadMind", page_icon="🚗")
st.title("RoadMind - explainable road-risk co-pilot")
st.caption("Research prototype. The model is trained ONLY on US Accidents (2016-2023, CC BY-NC-SA 4.0). It estimates "
           "how likely an accident under these conditions is to cause a HIGH traffic-delay impact - not the chance "
           "that an accident happens. Decision support only.")

WEATHER = ["Fair", "Clear", "Mostly Cloudy", "Partly Cloudy", "Cloudy", "Overcast", "Light Rain", "Rain", "Heavy Rain",
           "Light Drizzle", "Thunderstorm", "Light Snow", "Snow", "Heavy Snow", "Freezing Rain", "Fog", "Haze", "Smoke"]
US_STATES = sorted("AL AZ AR CA CO CT DE FL GA ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH "
                   "OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())
INDIAN_CITIES = {  # name -> (state, default month index bias unused; just labels)
    "Hyderabad": "Telangana", "Delhi": "Delhi", "Mumbai": "Maharashtra", "Bengaluru": "Karnataka",
    "Chennai": "Tamil Nadu", "Kolkata": "West Bengal", "Jaipur": "Rajasthan", "Shimla": "Himachal Pradesh",
    "Pune": "Maharashtra", "Ahmedabad": "Gujarat",
}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

with st.sidebar:
    st.header("Region")
    region = st.radio("Region", ["India (default)", "United States"], index=0, label_visibility="collapsed")
    is_india = region.startswith("India")
    if is_india:
        st.info("The model was trained only on US data and has never seen Indian roads or weather. Results below "
                "are an untested extrapolation - illustrative only, not validated for India.", icon="⚠️")

    st.header("Conditions")
    weather = st.selectbox("Weather", WEATHER)
    if is_india:
        city = st.selectbox("City", list(INDIAN_CITIES), index=0)
        temp = st.slider("Temperature (°C)", -10, 50, 30)
        vis = st.slider("Visibility (km)", 0.0, 16.0, 10.0, 0.5)
        wind = st.slider("Wind speed (km/h)", 0, 100, 10)
        precip = st.slider("Precipitation (mm/hr)", 0.0, 50.0, 0.0, 1.0)
    else:
        state = st.selectbox("State", US_STATES, index=US_STATES.index("CA"))
        temp = st.slider("Temperature (°F)", -20, 120, 65)
        vis = st.slider("Visibility (mi)", 0.0, 10.0, 10.0, 0.5)
        wind = st.slider("Wind speed (mph)", 0, 60, 5)
        precip = st.slider("Precipitation (in/hr)", 0.0, 1.0, 0.0, 0.01)
    humidity = st.slider("Humidity (%)", 0, 100, 60)
    hour = st.slider("Hour of day (local)", 0, 23, 17)
    dow = st.selectbox("Day of week", range(7), index=2, format_func=lambda i: DAYS[i])
    month = st.slider("Month", 1, 12, 6)
    st.subheader("Road features nearby")
    poi = {k: st.checkbox(k.replace("_", " ").title()) for k in
           ["junction", "traffic_signal", "crossing", "stop", "railway", "roundabout"]}

inputs = {"weather_condition": weather, "humidity_pct": humidity, "hour": hour, "day_of_week": dow,
          "month": month, **poi}
if is_india:
    inputs.update(temperature_c=temp, visibility_km=vis, wind_speed_kmh=wind, precipitation_mm=precip,
                  location_label=f"{city}, {INDIAN_CITIES[city]}, India")
else:
    inputs.update(temperature_f=temp, visibility_mi=vis, wind_speed_mph=wind, precipitation_in=precip, state=state)
res = explain_prediction(inputs, top_k=6)

color = {"High": "red", "Medium": "orange", "Low": "green"}[res["risk_level"]]
st.markdown(f"## :{color}[{res['risk_level'].upper()} RISK]")
st.text(res["suggested_message"])
if is_india:
    st.warning(res["notes"], icon="⚠️")
st.subheader("Top SHAP factors")
df = pd.DataFrame(res["top_factors"])[["description", "direction", "shap_log_odds"]]
st.dataframe(df, hide_index=True, width='stretch')
st.bar_chart(df.set_index("description")["shap_log_odds"])
st.caption(f"Model score {res['probability']:.3f} (uncalibrated outside the training data; the tier is what matters). "
           "SHAP values are in log-odds; positive = pushes toward a high-impact outcome.")
if not is_india:
    st.caption(res["notes"])

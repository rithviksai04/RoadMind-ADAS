"""Live weather lookup via Open-Meteo (free, no API key/credentials - nothing to hardcode), for the US demo.

Two calls: geocoding (place name -> lat/lon/state/country/timezone) and a current-conditions forecast call.
`auto_conditions()` turns a free-text US place into an `explain_prediction()`-ready input dict (imperial units,
matching the training data), using the CURRENT local hour/day/month at that place. Network calls are isolated in
`_geocode_raw`/`_forecast_raw` so tests can monkeypatch them offline.
"""
import datetime as dt
import json
import urllib.error
import urllib.parse
import urllib.request
import zoneinfo

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
CURRENT_VARS = ("temperature_2m,relative_humidity_2m,precipitation,rain,showers,snowfall,weather_code,"
                "pressure_msl,wind_speed_10m,visibility")

US_STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO",
    "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
}

# State capital used to geocode a state selected by name (not by typed city). Full name -> "City, State".
STATE_CAPITALS = {
    "Alabama": "Montgomery, Alabama", "Alaska": "Juneau, Alaska", "Arizona": "Phoenix, Arizona",
    "Arkansas": "Little Rock, Arkansas", "California": "Sacramento, California", "Colorado": "Denver, Colorado",
    "Connecticut": "Hartford, Connecticut", "Delaware": "Dover, Delaware", "Florida": "Tallahassee, Florida",
    "Georgia": "Atlanta, Georgia", "Hawaii": "Honolulu, Hawaii", "Idaho": "Boise, Idaho",
    "Illinois": "Springfield, Illinois", "Indiana": "Indianapolis, Indiana", "Iowa": "Des Moines, Iowa",
    "Kansas": "Topeka, Kansas", "Kentucky": "Frankfort, Kentucky", "Louisiana": "Baton Rouge, Louisiana",
    "Maine": "Augusta, Maine", "Maryland": "Annapolis, Maryland", "Massachusetts": "Boston, Massachusetts",
    "Michigan": "Lansing, Michigan", "Minnesota": "Saint Paul, Minnesota", "Mississippi": "Jackson, Mississippi",
    "Missouri": "Jefferson City, Missouri", "Montana": "Helena, Montana", "Nebraska": "Lincoln, Nebraska",
    "Nevada": "Carson City, Nevada", "New Hampshire": "Concord, New Hampshire", "New Jersey": "Trenton, New Jersey",
    "New Mexico": "Santa Fe, New Mexico", "New York": "Albany, New York",
    "North Carolina": "Raleigh, North Carolina", "North Dakota": "Bismarck, North Dakota",
    "Ohio": "Columbus, Ohio", "Oklahoma": "Oklahoma City, Oklahoma", "Oregon": "Salem, Oregon",
    "Pennsylvania": "Harrisburg, Pennsylvania", "Rhode Island": "Providence, Rhode Island",
    "South Carolina": "Columbia, South Carolina", "South Dakota": "Pierre, South Dakota",
    "Tennessee": "Nashville, Tennessee", "Texas": "Austin, Texas", "Utah": "Salt Lake City, Utah",
    "Vermont": "Montpelier, Vermont", "Virginia": "Richmond, Virginia", "Washington": "Olympia, Washington",
    "West Virginia": "Charleston, West Virginia", "Wisconsin": "Madison, Wisconsin", "Wyoming": "Cheyenne, Wyoming",
    "District of Columbia": "Washington, District of Columbia",
}

# WMO weather codes (used by Open-Meteo) -> a free-text condition string that features.weather_group() buckets
# correctly via its keyword rules (see feature_dictionary.md).
WMO_CONDITION = {
    0: "Clear", 1: "Fair", 2: "Partly Cloudy", 3: "Overcast", 45: "Fog", 48: "Fog",
    51: "Light Drizzle", 53: "Drizzle", 55: "Heavy Drizzle", 56: "Freezing Drizzle", 57: "Freezing Drizzle",
    61: "Light Rain", 63: "Rain", 65: "Heavy Rain", 66: "Freezing Rain", 67: "Freezing Rain",
    71: "Light Snow", 73: "Snow", 75: "Heavy Snow", 77: "Snow Grains",
    80: "Light Rain Showers", 81: "Rain Showers", 82: "Heavy Rain Showers",
    85: "Light Snow Showers", 86: "Heavy Snow Showers", 95: "Thunderstorm",
    96: "Thunderstorm with Hail", 99: "Thunderstorm with Hail",
}


class WeatherLookupError(RuntimeError):
    pass


def _get_json(url: str, timeout: float = 8.0) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise WeatherLookupError(f"could not reach {url.split('?')[0]}: {e}") from e


def _geocode_raw(query: str, count: int = 5) -> list[dict]:
    url = f"{GEOCODE_URL}?{urllib.parse.urlencode({'name': query, 'count': count, 'language': 'en'})}"
    return _get_json(url).get("results") or []


def _forecast_raw(lat: float, lon: float) -> dict:
    params = {"latitude": lat, "longitude": lon, "current": CURRENT_VARS, "timezone": "auto",
              "temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "inch"}
    return _get_json(f"{FORECAST_URL}?{urllib.parse.urlencode(params)}")


def geocode(query: str, prefer_country_code: str | None = None) -> dict:
    """Best-matching place for free text like 'Hyderabad' or 'Austin, Texas'. Raises WeatherLookupError if none."""
    results = _geocode_raw(query)
    if not results:
        raise WeatherLookupError(f"no location found for '{query}'")
    if prefer_country_code:
        results = sorted(results, key=lambda r: r.get("country_code") != prefer_country_code)
    r = results[0]
    return {"name": r["name"], "admin1": r.get("admin1"), "country": r.get("country"),
            "country_code": r.get("country_code"), "lat": r["latitude"], "lon": r["longitude"],
            "timezone": r.get("timezone", "UTC")}


def auto_conditions(query: str, prefer_country_code: str | None = "US",
                    geocode_fn=geocode, forecast_fn=_forecast_raw) -> dict:
    """Free-text place -> explain_prediction()-ready input dict (imperial units), using CURRENT live weather and
    local time. `state` is set only when the place resolves to a recognized US state; otherwise it is left unset
    so the model correctly uses no location signal rather than being silently misread as an unknown US state."""
    place = geocode_fn(query, prefer_country_code)
    fc = forecast_fn(place["lat"], place["lon"])
    c = fc.get("current")
    if not c:
        raise WeatherLookupError("forecast response had no 'current' block")
    now = dt.datetime.fromisoformat(c["time"])
    try:
        now = now.replace(tzinfo=zoneinfo.ZoneInfo(place["timezone"]))
    except Exception:
        pass
    code = c.get("weather_code")
    pressure, vis = c.get("pressure_msl"), c.get("visibility")
    return {
        # Unknown code -> None (imputed like a missing training value), not a guessed "Cloudy".
        "weather_condition": WMO_CONDITION.get(code) if code is not None else None,
        "temperature_f": c.get("temperature_2m"), "wind_speed_mph": c.get("wind_speed_10m"),
        "precipitation_in": c.get("precipitation"),
        # Missing readings stay None: 0 visibility would mean dense fog, 0 pressure is impossible.
        "pressure_in": round(pressure * 0.02953, 2) if pressure is not None else None,
        # US station reports (the training data) top out at 10 mi; Open-Meteo goes far higher, and >20 mi
        # would be discarded as implausible by features.engineer() and replaced with the median.
        "visibility_mi": min(10.0, round(vis / 1609.34, 1)) if vis is not None else None,
        "humidity_pct": c.get("relative_humidity_2m"),
        "state": US_STATE_ABBR.get(place["admin1"] or ""),
        "hour": now.hour, "day_of_week": now.weekday(), "month": now.month,
        "location_label": ", ".join(x for x in [place["name"], place["admin1"], place["country"]] if x),
        "_source": "Open-Meteo live current-conditions (fetched just now)", "_fetched_at_local": now.isoformat(),
    }

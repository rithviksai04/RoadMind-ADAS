"""Unit tests for feature-engineering rules (no trained model needed)."""
import numpy as np
import pandas as pd
import pytest

from roadmind.features import FEATURES, engineer, road_surface, weather_group


def row(**kw):
    base = {"Start_Time": "2022-03-09 14:00:00", "Weather_Condition": "Fair", "Temperature(F)": 70.0,
            "Precipitation(in)": 0.0, "State": "CA"}
    base.update(kw)
    return pd.DataFrame([base])


@pytest.mark.parametrize("text,group", [
    ("Fair", "clear"), ("Clear", "clear"), ("Mostly Cloudy", "cloudy"), ("Overcast", "cloudy"),
    ("Light Rain", "rain"), ("Heavy Drizzle", "rain"), ("Light Rain with Thunder", "thunderstorm"),
    ("T-Storm", "thunderstorm"), ("Light Snow", "snow_ice"), ("Freezing Rain", "snow_ice"),
    ("Wintry Mix", "snow_ice"), ("Fog", "fog_haze_smoke"), ("Haze", "fog_haze_smoke"),
    ("Fair / Windy", "clear"), ("Volcanic Whatever", "other"), (None, "unknown"),
])
def test_weather_group(text, group):
    assert weather_group(pd.Series([text])).iloc[0] == group


@pytest.mark.parametrize("group,temp,precip,expected", [
    ("clear", 70, 0.0, "dry"), ("rain", 60, 0.1, "wet"), ("clear", 60, 0.05, "wet"),
    ("snow_ice", 25, 0.0, "icy"), ("rain", 30, 0.1, "icy"), ("clear", 30, 0.0, "dry"),
    ("unknown", 60, np.nan, "unknown"), ("unknown", 60, 0.0, "dry"),
])
def test_road_surface_rule(group, temp, precip, expected):
    out = road_surface(pd.Series([group]), pd.Series([float(temp)]), pd.Series([precip]))
    assert out.iloc[0] == expected


def test_engineer_output_columns_and_no_leaky_fields():
    f = engineer(row())
    assert list(f.columns) == FEATURES
    for banned in ["Source", "year", "End_Time", "Distance(mi)", "Severity", "Start_Lat", "Start_Lng", "Street",
                   "precip_missing"]:
        assert banned not in f.columns


def test_implausible_values_become_missing():
    f = engineer(row(**{"Temperature(F)": 999, "Visibility(mi)": 500, "Pressure(in)": 58.0}))
    assert f["temperature_f"].isna().all() and f["visibility_mi"].isna().all() and f["pressure_in"].isna().all()


def test_wind_missing_is_calm_and_values_rounded():
    assert engineer(row())["wind_speed_mph"].iloc[0] == 0            # absent -> calm
    assert engineer(row(**{"Wind_Speed(mph)": 6.9}))["wind_speed_mph"].iloc[0] == 7
    assert engineer(row(**{"Temperature(F)": 71.6}))["temperature_f"].iloc[0] == 72
    assert engineer(row(**{"Pressure(in)": 29.94}))["pressure_in"].iloc[0] == 29.9


@pytest.mark.parametrize("ts,rush", [("2022-03-09 08:00:00", 1), ("2022-03-09 17:30:00", 1),
                                     ("2022-03-09 12:00:00", 0), ("2022-03-12 08:00:00", 0)])  # Sat = never rush
def test_rush_hour_proxy(ts, rush):
    assert engineer(row(Start_Time=ts))["is_rush_hour"].iloc[0] == rush


@pytest.mark.parametrize("hour,night", [(2, 1), (5, 1), (6, 0), (12, 0), (18, 0), (19, 1), (23, 1)])
def test_night_fallback_from_hour(hour, night):
    assert engineer(row(Start_Time=f"2022-03-09 {hour:02d}:00:00"))["is_night"].iloc[0] == night


def test_night_uses_dataset_field_when_present():
    f = engineer(row(Start_Time="2022-03-09 12:00:00", Sunrise_Sunset="Night"))
    assert f["is_night"].iloc[0] == 1


def test_time_features_and_weekend():
    f = engineer(row(Start_Time="2022-03-12 09:30:00"))  # a Saturday
    assert (f["hour"].iloc[0], f["day_of_week"].iloc[0], f["month"].iloc[0], f["is_weekend"].iloc[0]) == (9, 5, 3, 1)


def test_windy_flag():
    assert engineer(row(Weather_Condition="Cloudy / Windy"))["is_windy"].iloc[0] == 1
    assert engineer(row(Weather_Condition="Cloudy"))["is_windy"].iloc[0] == 0


def test_road_flags_default_absent_and_read_when_given():
    assert engineer(row())["junction"].iloc[0] == 0
    assert engineer(row(Junction=True, Traffic_Signal=True))[["junction", "traffic_signal"]].iloc[0].tolist() == [1, 1]

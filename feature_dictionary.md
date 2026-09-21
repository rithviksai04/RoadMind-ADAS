# Feature dictionary

All features are computed by `roadmind.features.engineer()`, the same code used in training and in the demo.
**Target `high_impact`** = 1 if `Severity` is 3 or 4, else 0. Severity measures *traffic-delay impact*, not injury severity.
The dataset has only accidents that occurred, so the model estimates P(high delay impact | an accident occurred here, under these conditions).

## Cleaning applied before features
- Rows that are exact duplicates on (Start_Time, Start_Lat, Start_Lng, Severity, Street) are dropped (1,346 of 400,002 in the sample).
- Values outside these plausible ranges are set to missing: Temp -50..125 F, Humidity 0..100 %, Pressure 25..32 in,
  Visibility 0..20 mi, Wind speed 0..120 mph, Precipitation 0..10 in.
- Missing numerics (except wind, see below) are median-imputed. The median is learned on the training split only, so nothing leaks from the test set.

## Numeric
| Feature | Source column | Meaning / computation | Missing (sample) |
|---|---|---|---|
| temperature_f | Temperature(F) | range check, then rounded to whole degrees | 2.1% |
| humidity_pct | Humidity(%) | as-is | 2.2% |
| pressure_in | Pressure(in) | range check, rounded to 0.1 in | 3.1% |
| visibility_mi | Visibility(mi) | range check, rounded to 0.1 mi | 2.4% |
| wind_speed_mph | Wind_Speed(mph) | range check, rounded to whole mph. **Missing/invalid -> 0 (calm)**, not the median (see below) | 7.4% (before fill) |
| precipitation_in | Precipitation(in) | as-is, median-imputed (median = 0) | 28.5% |
| hour | Start_Time | hour of day, 0-23 | 0 |
| day_of_week | Start_Time | 0 = Monday ... 6 = Sunday | 0 |
| month | Start_Time | 1-12 (seasonality) | 0 |

### Why rounding and the wind fill (provider artefacts)
The dataset merges several data providers whose conventions differ, and the model can exploit that if it is not neutralised:
- Wind: before 2019 about 19% of rows have NaN wind and 0.2% have exactly 0; from 2019 about 3% NaN and 17% exactly 0. So "calm" was stored as NaN in the early years. Filling NaN with 0 makes both eras look alike.
- Precision: 86% of Source1 wind values are whole numbers vs 49% for Source2 (temperature 91% vs 71%). Rounding removes this tell.
- A `precip_missing` flag was tried and removed: it was 91% true in 2016-18 and 4% in 2021+, i.e. a proxy for the year.
Other missing numerics are median-imputed on the training split.

## Flags (0/1)
| Feature | Computation |
|---|---|
| is_weekend | day_of_week >= 5 |
| is_rush_hour | **APPROXIMATION of congestion** (there is no traffic-density field): weekday AND hour in 7-9 or 16-18 |
| is_night | `Sunrise_Sunset == "Night"` from the data. If that field is absent (demo input), **approximated** as hour < 6 or hour >= 19 |
| is_windy | Weather_Condition contains "wind" or "squall" |
| junction, traffic_signal, crossing, stop, give_way, railway, roundabout, station, amenity, bump, no_exit, traffic_calming | the dataset's POI/road-annotation booleans, **at the accident location** (see limitations) |

## Categorical (one-hot encoded)
| Feature | Computation |
|---|---|
| weather_group | Keyword rules on Weather_Condition, first match wins: thunderstorm (thunder/t-storm/storm) > snow_ice (snow/sleet/ice/freezing/wintry/hail) > rain (rain/drizzle/shower) > fog_haze_smoke (fog/mist/haze/smoke/dust/sand/ash) > cloudy (cloud/overcast) > clear (fair/clear) > other; missing -> unknown |
| road_surface | **Derived, approximate; not a dataset column.** `icy` if weather_group = snow_ice, or (temp <= 32 F and (rain/thunderstorm weather or precipitation >= 0.01 in)). Otherwise `wet` if rain/thunderstorm weather or precipitation >= 0.01 in. `unknown` if weather condition and precipitation are both missing. Otherwise `dry`. It cannot see lingering wetness after rain stops. |
| state | US state code (location proxy) |

## Deliberately excluded
- **Post-hoc / leakage:** End_Time, End_Lat/Lng, Distance(mi), Description, Weather_Timestamp.
- **Data-provider artefact:** `Source`, and the year (see `reports/eda/FINDINGS.md` on label drift).
- **Location detail:** Start_Lat/Lng and Street. Trees could memorise exact spots, and neighbouring accidents in a random split would inflate the metrics. Only `state` is kept.
- **Redundant / very sparse:** Wind_Chill (26% missing, a function of temp and wind), Wind_Direction, Timezone, the twilight columns (except Sunrise_Sunset as noted).
- **Not in the dataset, so not simulated:** driver speed, acceleration, braking, steering, real-time traffic density.

## Caveat on the POI flags
`junction`, `traffic_signal` etc. are annotations of the accident's location. A driver co-pilot would take them
from map data for the road ahead, which is a plausible mapping but was not validated here.

"""Chunked, exact stratified sampling of the US Accidents CSV.

One pass over the full file (never fully loaded in memory):
  * counts rows per (Severity, year) stratum and nulls per column on the FULL data;
  * gives every row a uniform random key and keeps an over-sample of low keys.
Afterwards, each stratum keeps its `round(n_target * stratum_share)` lowest keys,
which is an exact proportional stratified random sample.

Usage: python -m roadmind.sample [--n 400000] [--seed 42]
"""
import argparse
import json

import numpy as np
import pandas as pd

from roadmind.config import PROCESSED_DIR, RAW_CSV, REPORTS_DIR

# Columns knowable at (or before) the moment of the accident. Everything else
# (End_Time, End_Lat/Lng, Distance(mi), Description, ...) is dropped here.
KEEP_COLS = [
    "ID", "Source", "Severity", "Start_Time", "Start_Lat", "Start_Lng",
    "Street", "State", "Timezone",
    "Temperature(F)", "Wind_Chill(F)", "Humidity(%)", "Pressure(in)",
    "Visibility(mi)", "Wind_Direction", "Wind_Speed(mph)", "Precipitation(in)",
    "Weather_Condition",
    "Amenity", "Bump", "Crossing", "Give_Way", "Junction", "No_Exit", "Railway",
    "Roundabout", "Station", "Stop", "Traffic_Calming", "Traffic_Signal",
    "Turning_Loop",
    "Sunrise_Sunset", "Civil_Twilight", "Nautical_Twilight", "Astronomical_Twilight",
]
CHUNK = 500_000
TOTAL_ROWS_APPROX = 7_728_394  # used only to size the over-sample buffer


def main(n_target: int, seed: int) -> None:
    rng = np.random.default_rng(seed)
    keep_p = min(1.0, 3.0 * n_target / TOTAL_ROWS_APPROX)  # generous over-sample
    null_counts, strata_counts, kept, n_rows, n_dup_ids = None, {}, [], 0, 0

    for chunk in pd.read_csv(RAW_CSV, chunksize=CHUNK, low_memory=False):
        n_rows += len(chunk)
        nc = chunk.isna().sum()
        null_counts = nc if null_counts is None else null_counts + nc
        year = chunk["Start_Time"].str.slice(0, 4).astype(int)
        for key, cnt in pd.MultiIndex.from_arrays([chunk["Severity"], year]).value_counts().items():
            strata_counts[key] = strata_counts.get(key, 0) + int(cnt)
        c = chunk[KEEP_COLS].copy()
        c["_year"] = year.values
        c["_key"] = rng.random(len(c))
        kept.append(c[c["_key"] < keep_p])
        print(f"  read {n_rows:,} rows", flush=True)

    pool = pd.concat(kept, ignore_index=True)
    n_dup_ids = int(pool["ID"].duplicated().sum())
    pool = pool.drop_duplicates("ID")
    parts = []
    for (sev, yr), cnt in strata_counts.items():
        n_s = round(n_target * cnt / n_rows)
        grp = pool[(pool["Severity"] == sev) & (pool["_year"] == yr)]
        parts.append(grp.nsmallest(n_s, "_key"))
    sample = pd.concat(parts).drop(columns=["_key"]).sort_values("Start_Time")
    sample = sample.reset_index(drop=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    sample.to_parquet(PROCESSED_DIR / "sample.parquet", index=False)

    (REPORTS_DIR / "eda").mkdir(parents=True, exist_ok=True)
    stats = {
        "full_rows": n_rows,
        "full_columns": int(len(null_counts)),
        "sample_rows": int(len(sample)),
        "seed": seed,
        "duplicate_ids_in_pool": n_dup_ids,
        "full_null_counts": {k: int(v) for k, v in null_counts.items()},
        "full_strata_counts": {f"{s}|{y}": c for (s, y), c in sorted(strata_counts.items())},
    }
    (REPORTS_DIR / "eda" / "full_dataset_stats.json").write_text(json.dumps(stats, indent=2))
    print(f"full rows={n_rows:,}  sample rows={len(sample):,}")
    print(sample["Severity"].value_counts(normalize=True).sort_index())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400_000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    main(a.n, a.seed)

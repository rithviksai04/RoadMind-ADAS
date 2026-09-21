"""Preprocessing: de-duplication, leakage guard, feature build, splits, encoders.

Run: python -m roadmind.preprocess   -> data/processed/{features.parquet,split_info.json}
"""
import json

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from roadmind.config import PROCESSED_DIR, SEED
from roadmind.features import CATEGORICAL, FEATURES, FLAGS, NUMERIC, TARGET, engineer

# Fields only knowable after the accident (or that identify the data provider) - never model inputs.
FORBIDDEN = {"End_Time", "End_Lat", "End_Lng", "Distance(mi)", "Description", "Source", "ID",
             "Weather_Timestamp", "Severity", "Start_Lat", "Start_Lng", "Street"}


def build_features() -> tuple[pd.DataFrame, dict]:
    raw = pd.read_parquet(PROCESSED_DIR / "sample.parquet")
    info = {"rows_in": len(raw)}
    dup_cols = ["Start_Time", "Start_Lat", "Start_Lng", "Severity", "Street"]
    raw = raw.drop_duplicates(subset=dup_cols).reset_index(drop=True)
    info["duplicates_removed"] = info["rows_in"] - len(raw)
    feats = engineer(raw)
    assert not (set(feats.columns) & FORBIDDEN), "leakage guard: forbidden column in features"
    feats[TARGET] = (raw["Severity"] >= 3).astype(int)
    feats["severity"] = raw["Severity"].values
    feats["year"] = pd.to_datetime(raw["Start_Time"], format="mixed").dt.year.values  # split only, not a feature
    info["rows_out"] = len(feats)
    info["high_impact_rate"] = float(feats[TARGET].mean())
    return feats, info


def make_splits(feats: pd.DataFrame) -> dict[str, tuple[pd.Index, pd.Index]]:
    """Two splits. 'stratified' (primary): random 80/20 stratified on the target.
    'time' (stress test): train on 2016-2021, test on 2022-2023."""
    idx_tr, idx_te = train_test_split(feats.index, test_size=0.2, random_state=SEED,
                                      stratify=feats[TARGET])
    time_tr = feats.index[feats["year"] <= 2021]
    time_te = feats.index[feats["year"] >= 2022]
    return {"stratified": (idx_tr, idx_te), "time": (time_tr, time_te)}


def make_preprocessor(scale: bool) -> ColumnTransformer:
    """Median-impute numerics (scaled for linear models only), one-hot categoricals."""
    num_steps = [("impute", SimpleImputer(strategy="median"))]
    if scale:
        num_steps.append(("scale", StandardScaler()))
    return ColumnTransformer([
        ("num", Pipeline(num_steps), NUMERIC),
        ("flag", "passthrough", FLAGS),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
    ], verbose_feature_names_out=False)


if __name__ == "__main__":
    feats, info = build_features()
    feats.to_parquet(PROCESSED_DIR / "features.parquet")
    splits = make_splits(feats)
    for name, (tr, te) in splits.items():
        info[name] = {"train": len(tr), "test": len(te),
                      "train_high_rate": float(feats.loc[tr, TARGET].mean()),
                      "test_high_rate": float(feats.loc[te, TARGET].mean())}
    (PROCESSED_DIR / "split_info.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info, indent=2))
    print(feats[FEATURES].isna().mean().round(3)[lambda s: s > 0].to_dict())
    print(feats["weather_group"].value_counts().to_dict())
    print(feats["road_surface"].value_counts().to_dict())

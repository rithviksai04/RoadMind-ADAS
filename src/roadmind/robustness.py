"""Robustness check: does the model's skill survive inside a single data provider, and without `state`?
Run: python -m roadmind.robustness  -> reports/robustness.md"""
import joblib
import pandas as pd
from sklearn.metrics import roc_auc_score

from roadmind.config import MODELS_DIR, PROCESSED_DIR, REPORTS_DIR, SEED
from roadmind.features import CATEGORICAL, FEATURES, TARGET
from roadmind.preprocess import make_splits
from roadmind.train import make_models

feats = pd.read_parquet(PROCESSED_DIR / "features.parquet")
raw = pd.read_parquet(PROCESSED_DIR / "sample.parquet")
raw = raw.drop_duplicates(subset=["Start_Time", "Start_Lat", "Start_Lng", "Severity", "Street"]).reset_index(drop=True)
feats["source"] = raw["Source"].values
tr, te = make_splits(feats)["stratified"]
preds = pd.read_parquet(PROCESSED_DIR / "preds_stratified.parquet")
rows = ["| Check | XGBoost ROC-AUC (stratified test) | n |", "|---|---|---|",
        f"| All rows (reference) | {roc_auc_score(preds['y'], preds['xgboost']):.3f} | {len(preds):,} |"]
for s in ["Source1", "Source2"]:
    m = (feats.loc[te, "source"] == s).values
    rows.append(f"| Only {s} rows in test set (model trained on all sources) | "
                f"{roc_auc_score(preds['y'][m], preds['xgboost'][m]):.3f} | {m.sum():,} |")
# Ablation: retrain XGBoost with state removed (fixed tree count from train_log)
import roadmind.features as F, roadmind.preprocess as P
F.CATEGORICAL = [c for c in CATEGORICAL if c != "state"]; P.CATEGORICAL = F.CATEGORICAL
import json
n_trees = json.loads((MODELS_DIR / "train_log.json").read_text())["stratified/xgboost"]["xgb_trees"]
pipe = make_models(n_trees)["xgboost"]
pipe.set_params(prep=P.make_preprocessor(scale=False))
cols = [c for c in FEATURES if c != "state"]
pipe.fit(feats.loc[tr, cols], feats.loc[tr, TARGET])
p = pipe.predict_proba(feats.loc[te, cols])[:, 1]
rows.append(f"| Retrained WITHOUT `state` | {roc_auc_score(feats.loc[te, TARGET], p):.3f} | {len(te):,} |")
txt = "# Robustness checks\n\n" + "\n".join(rows) + "\n"
(REPORTS_DIR / "robustness.md").write_text(txt); print(txt)

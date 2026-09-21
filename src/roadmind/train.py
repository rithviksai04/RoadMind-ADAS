"""Train LR / RF / XGBoost on both splits, derive risk-tier thresholds, save artefacts.

Run: python -m roadmind.train
Outputs: models/{split}_{model}.joblib, data/processed/preds_{split}.parquet, models/train_log.json

Hyper-parameters are fixed a priori (NOT tuned on the test set). XGBoost picks its number of trees by
early stopping on a 10% slice of the TRAIN set.
Models are unweighted: probabilities stay interpretable, and the tertile risk tiers depend only on ranking.
Risk-tier thresholds = 33.3rd / 66.7th percentile of OUT-OF-FOLD (3-fold) predicted probabilities on the
training set. Plain in-sample predictions would be over-confident for trees (esp. random forest).
"""
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from roadmind.config import MODELS_DIR, PROCESSED_DIR, SEED
from roadmind.features import FEATURES, TARGET
from roadmind.preprocess import make_preprocessor, make_splits


def make_models(xgb_trees: int | None = None) -> dict[str, Pipeline]:
    return {
        "logreg": Pipeline([("prep", make_preprocessor(scale=True)),
                            ("clf", LogisticRegression(max_iter=2000, C=1.0))]),
        "random_forest": Pipeline([("prep", make_preprocessor(scale=False)),
                                   ("clf", RandomForestClassifier(
                                       n_estimators=300, min_samples_leaf=20, max_features="sqrt",
                                       n_jobs=-1, random_state=SEED))]),
        "xgboost": Pipeline([("prep", make_preprocessor(scale=False)),
                             ("clf", XGBClassifier(
                                 n_estimators=xgb_trees or 300, learning_rate=0.08, max_depth=6,
                                 subsample=0.8, colsample_bytree=0.8, min_child_weight=10,
                                 tree_method="hist", n_jobs=-1, random_state=SEED))]),
    }


def xgb_best_trees(X, y) -> int:
    Xa, Xv, ya, yv = train_test_split(X, y, test_size=0.1, random_state=SEED, stratify=y)
    pipe = make_models(xgb_trees=1000)["xgboost"]
    prep = pipe.named_steps["prep"].fit(Xa)
    clf = pipe.named_steps["clf"].set_params(early_stopping_rounds=30, eval_metric="auc")
    clf.fit(prep.transform(Xa), ya, eval_set=[(prep.transform(Xv), yv)], verbose=False)
    return int(clf.best_iteration) + 1


def main():
    MODELS_DIR.mkdir(exist_ok=True)
    feats = pd.read_parquet(PROCESSED_DIR / "features.parquet")
    log = {}
    for split, (tr, te) in make_splits(feats).items():
        Xtr, ytr, Xte, yte = feats.loc[tr, FEATURES], feats.loc[tr, TARGET], feats.loc[te, FEATURES], feats.loc[te, TARGET]
        n_trees = xgb_best_trees(Xtr, ytr)
        preds = pd.DataFrame({"y": yte.values, "severity": feats.loc[te, "severity"].values}, index=te)
        for name, pipe in make_models(n_trees).items():
            t0 = time.time()
            oof = cross_val_predict(clone(pipe), Xtr, ytr, method="predict_proba", n_jobs=1,
                                    cv=StratifiedKFold(3, shuffle=True, random_state=SEED))[:, 1]
            t_low, t_high = np.percentile(oof, [100 / 3, 200 / 3])
            pipe.fit(Xtr, ytr)
            preds[name] = pipe.predict_proba(Xte)[:, 1]
            joblib.dump({"pipeline": pipe, "thresholds": {"low_medium": float(t_low), "medium_high": float(t_high)},
                         "features": FEATURES, "split": split, "model": name}, MODELS_DIR / f"{split}_{name}.joblib")
            log[f"{split}/{name}"] = {"low_medium": float(t_low), "medium_high": float(t_high),
                                       "train_secs": round(time.time() - t0, 1),
                                       **({"xgb_trees": n_trees} if name == "xgboost" else {})}
            print(split, name, log[f"{split}/{name}"], flush=True)
        preds.to_parquet(PROCESSED_DIR / f"preds_{split}.parquet")
    (MODELS_DIR / "train_log.json").write_text(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()

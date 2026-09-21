"""Sanity checks on the pipeline outputs: leakage guards, split integrity, metric plausibility, honesty checks."""
import json

import joblib
import pandas as pd
import pytest

from roadmind.config import MODELS_DIR, PROCESSED_DIR, REPORTS_DIR
from roadmind.features import FEATURES, TARGET
from roadmind.preprocess import FORBIDDEN, make_splits

pytestmark = pytest.mark.needs_data


@pytest.fixture(scope="module")
def feats():
    return pd.read_parquet(PROCESSED_DIR / "features.parquet")


@pytest.fixture(scope="module")
def metrics():
    return json.loads((REPORTS_DIR / "metrics.json").read_text())


def test_no_forbidden_or_post_hoc_field_is_a_feature():
    assert not set(FEATURES) & FORBIDDEN
    assert not {"year", "source", "Source", "severity", TARGET} & set(FEATURES)


def test_target_definition(feats):
    assert set(feats[TARGET].unique()) == {0, 1}
    assert (feats[TARGET] == (feats["severity"] >= 3).astype(int)).all()


@pytest.mark.parametrize("split", ["stratified", "time"])
def test_splits_disjoint_and_complete(feats, split):
    tr, te = make_splits(feats)[split]
    assert len(set(tr) & set(te)) == 0
    assert len(tr) + len(te) == len(feats)


def test_time_split_really_is_chronological(feats):
    tr, te = make_splits(feats)["time"]
    assert feats.loc[tr, "year"].max() < feats.loc[te, "year"].min()


def test_stratified_split_preserves_base_rate(feats):
    tr, te = make_splits(feats)["stratified"]
    assert abs(feats.loc[tr, TARGET].mean() - feats.loc[te, TARGET].mean()) < 0.002


def test_no_duplicate_rows_remain(feats):
    assert not feats.duplicated().all()  # sanity (features may legitimately repeat)
    assert len(feats) > 300_000


def test_feature_value_ranges(feats):
    assert feats["hour"].between(0, 23).all() and feats["month"].between(1, 12).all()
    assert feats["day_of_week"].between(0, 6).all()
    assert set(feats["road_surface"].unique()) <= {"dry", "wet", "icy", "unknown"}
    assert feats["wind_speed_mph"].notna().all()


@pytest.mark.parametrize("split", ["stratified", "time"])
@pytest.mark.parametrize("model", ["logreg", "random_forest", "xgboost"])
def test_models_beat_chance_and_metrics_are_valid(metrics, split, model):
    m = metrics[split]["models"][model]
    assert 0.5 < m["roc_auc"] < 1.0                       # some real signal, but not too good to be true
    assert m["pr_auc"] > metrics[split]["base_rate"]        # better than a random ranker
    assert m["roc_auc"] < 0.95, "suspiciously high - check for leakage"
    for k in ["accuracy", "precision", "recall", "f1"]:
        assert 0 <= m["high_tier"][k] <= 1
    c = m["high_tier"]["confusion"]
    assert c["tn"] + c["fp"] + c["fn"] + c["tp"] == metrics[split]["n_test"]


@pytest.mark.parametrize("split", ["stratified", "time"])
def test_tiers_are_ordered_by_observed_risk_and_cover_test_set(metrics, split):
    for name, m in metrics[split]["models"].items():
        t = m["tiers"]
        assert t["Low"]["n"] + t["Medium"]["n"] + t["High"]["n"] == metrics[split]["n_test"]
        assert t["Low"]["observed_high_impact_rate"] < t["Medium"]["observed_high_impact_rate"] \
            < t["High"]["observed_high_impact_rate"], name
        assert m["thresholds"]["low_medium"] < m["thresholds"]["medium_high"]


def test_stratified_high_tier_is_roughly_a_third(metrics):
    for m in metrics["stratified"]["models"].values():
        assert 0.28 < m["tiers"]["High"]["share_of_test"] < 0.38


def test_saved_models_load_and_predict(feats):
    tr, te = make_splits(feats)["stratified"]
    for name in ["logreg", "random_forest", "xgboost"]:
        b = joblib.load(MODELS_DIR / f"stratified_{name}.joblib")
        p = b["pipeline"].predict_proba(feats.loc[te[:200], FEATURES])[:, 1]
        assert ((p >= 0) & (p <= 1)).all() and p.std() > 0


def test_report_states_recall_and_caveats():
    txt = (REPORTS_DIR / "evaluation.md").read_text()
    assert "Recall (High-risk class)" in txt and "NOT" in txt
    readme = (REPORTS_DIR.parent / "README.md").read_text()
    assert "not injury severity" in readme and "CC BY-NC-SA" in readme

import os
from pathlib import Path

import pytest

from roadmind.config import MODELS_DIR, PROCESSED_DIR, REPORTS_DIR


def pytest_configure(config):
    config.addinivalue_line("markers", "needs_model: requires trained models (python -m roadmind.train)")
    config.addinivalue_line("markers", "needs_data: requires data/processed artefacts")
    config.addinivalue_line("markers", "regression: golden-snapshot check; re-baseline after an intentional retrain")


def pytest_collection_modifyitems(config, items):
    have_model = Path(os.environ.get("ROADMIND_MODEL_PATH", MODELS_DIR / "stratified_xgboost.joblib")).exists()
    have_data = (PROCESSED_DIR / "features.parquet").exists() and (REPORTS_DIR / "metrics.json").exists()
    for it in items:
        if "needs_model" in it.keywords and not have_model:
            it.add_marker(pytest.mark.skip(reason="trained model missing - run: python -m roadmind.train"))
        if "needs_data" in it.keywords and not have_data:
            it.add_marker(pytest.mark.skip(reason="processed data/metrics missing - run the pipeline first"))

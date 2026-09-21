from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = ROOT / "data" / "raw" / "US_Accidents_March23.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
SEED = 42

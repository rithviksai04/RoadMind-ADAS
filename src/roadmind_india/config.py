from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "india" / "raw"
TXT = ROOT / "data" / "india" / "txt" / "all.txt"
PROC = ROOT / "data" / "india" / "processed"
REPORTS = ROOT / "reports" / "india"
PDF_URL = "https://morth.gov.in/backend/documents/uploaded/Road-Accident-in-India-2023-Publications.pdf"
PDF = RAW_DIR / "Road-Accident-in-India-2023.pdf"
SOURCE = "MoRTH, Road Accidents in India 2023 (Transport Research Wing)"
# National totals for calendar 2023, printed in the report (used ONLY to validate the parser)
TOTALS_2023 = {"accidents": 480_583, "killed": 172_890, "injured": 462_825}
# Default location (Hyderabad, Telangana; IST)
DEFAULT_CITY = {"name": "Hyderabad", "state": "Telangana", "lat": 17.385, "lon": 78.4867, "tz": "Asia/Kolkata"}

"""Settings and the single data source (data/consultorio.json)."""
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = Path(os.environ.get("DEMO_DATA_FILE", ROOT / "data" / "consultorio.json"))
DB_PATH = os.environ.get("DEMO_DB_PATH", str(ROOT / "api" / "demo.sqlite"))
CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("DEMO_CORS_ORIGINS", "http://localhost:4321,http://127.0.0.1:4321").split(",")
    if o.strip()
]

TZ = ZoneInfo("America/Mexico_City")
HORIZON_DAYS = 14            # how far ahead a visitor can book
MIN_LEAD_MINUTES = 60        # no bookings for the next hour
MAX_FUTURE_APPOINTMENTS = 300
BOOKINGS_PER_IP_PER_HOUR = 8


def now() -> datetime:
    """Current time in the office's time zone (naive-aware helper, patched in tests)."""
    return datetime.now(TZ)


def load_site() -> dict:
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


SITE = load_site()
SLOT_MINUTES: int = SITE["booking"]["slot_minutes"]
SERVICES: dict[str, dict] = {s["id"]: s for s in SITE["services"]}
# data order is Monday..Sunday, same as date.weekday()
HOURS: list[list[list[str]]] = [h["ranges"] for h in SITE["hours"]]

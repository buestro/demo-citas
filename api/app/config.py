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

# ---- FAQ assistant (Claude) ----
ASSISTANT_MODEL = os.environ.get("DEMO_ASSISTANT_MODEL", "claude-haiku-5-5")
ASSISTANT_MAX_TOKENS = 700          # thinking counts toward this cap, so leave some room
CHAT_MAX_MESSAGES = 10              # history window sent by the widget
CHAT_MAX_CHARS = 400                # per user message
CHAT_USER_TURNS_PER_SESSION = 8     # user messages allowed in one conversation
CHAT_PER_IP_PER_HOUR = 30
CHAT_PER_DAY_GLOBAL = 600           # hard cost cap for the whole demo (risk R6)

# ---- Hardening ----
# How many reverse proxies sit in front of the API (Render = 1). With 0 the client IP is the TCP peer and
# X-Forwarded-For is ignored: a client can write anything in that header, so it is only trusted for the
# entry that our own proxy appended (counting from the right).
TRUSTED_PROXIES = int(os.environ.get("DEMO_TRUSTED_PROXIES", "0"))
AVAILABILITY_PER_IP_PER_HOUR = 300
MAX_TRACKED_IPS = 5000               # bounds the memory used by the rate limiters
REFRESH_EVERY_SECONDS = 60           # purge/seed at most once a minute, not on every request
ENABLE_DOCS = os.environ.get("DEMO_ENABLE_DOCS") == "1"   # /docs, /redoc and /openapi.json are off by default

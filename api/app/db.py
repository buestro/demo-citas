"""SQLite storage. The agenda keeps only name and phone: no health data, no free text."""
import random
import sqlite3
from datetime import date, datetime, timedelta

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS appointments (
  id TEXT PRIMARY KEY,
  service_id TEXT NOT NULL,
  start TEXT NOT NULL,
  end TEXT NOT NULL,
  name TEXT NOT NULL,
  phone TEXT NOT NULL,
  token TEXT NOT NULL,
  is_seed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
-- one row per occupied slot: the primary key makes double booking impossible
CREATE TABLE IF NOT EXISTS slots (
  slot TEXT PRIMARY KEY,
  appointment_id TEXT NOT NULL REFERENCES appointments(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS seeded_days (day TEXT PRIMARY KEY);
"""

FMT = "%Y-%m-%dT%H:%M"
SEED_MAX_FRACTION = 0.4


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def slots_for(start: datetime, service_id: str) -> list[str]:
    """Slot keys a service occupies (duration rounded up to the slot size)."""
    n = -(-config.SERVICES[service_id]["duration_minutes"] // config.SLOT_MINUTES)
    return [(start + timedelta(minutes=config.SLOT_MINUTES * i)).strftime(FMT) for i in range(n)]


def purge_past(conn: sqlite3.Connection) -> None:
    today = config.now().strftime("%Y-%m-%dT00:00")
    conn.execute("DELETE FROM appointments WHERE start < ?", (today,))
    conn.execute("DELETE FROM seeded_days WHERE day < ?", (today[:10],))


def ensure_seed(conn: sqlite3.Connection) -> None:
    """Fill the next days with a few fictional appointments so the demo looks lived in."""
    from .slotlogic import candidate_starts  # local import: avoids a cycle

    today = config.now().date()
    for i in range(config.HORIZON_DAYS + 1):
        day = today + timedelta(days=i)
        if conn.execute("SELECT 1 FROM seeded_days WHERE day = ?", (day.isoformat(),)).fetchone():
            continue
        rng = random.Random(day.toordinal())  # same day, same pattern
        starts = candidate_starts(day, "assessment", include_past=True)
        rng.shuffle(starts)
        # never fill more than SEED_MAX_FRACTION of the day, so visitors always find free slots
        total = len(candidate_starts(day, "assessment", include_past=True))
        budget = int(total * SEED_MAX_FRACTION)
        used = 0
        for start in starts[: rng.randint(3, 6)]:
            sid = rng.choice(list(config.SERVICES))
            need = len(slots_for(start, sid))
            if used + need > budget:
                continue
            if _insert_seed(conn, sid, start):
                used += need
        conn.execute("INSERT INTO seeded_days(day) VALUES (?)", (day.isoformat(),))


def _insert_seed(conn: sqlite3.Connection, service_id: str, start: datetime) -> bool:
    keys = slots_for(start, service_id)
    if conn.execute(f"SELECT 1 FROM slots WHERE slot IN ({','.join('?' * len(keys))})", keys).fetchone():
        return False
    if not _fits_in_hours(start, service_id):
        return False
    appt_id = f"seed-{start.strftime('%Y%m%d%H%M')}"
    end = start + timedelta(minutes=config.SLOT_MINUTES * len(keys))
    conn.execute(
        "INSERT INTO appointments(id, service_id, start, end, name, phone, token, is_seed, created_at)"
        " VALUES (?,?,?,?,?,?,?,1,?)",
        (appt_id, service_id, start.strftime(FMT), end.strftime(FMT), "Ejemplo", "0000000000", "-", config.now().isoformat()),
    )
    conn.executemany("INSERT INTO slots(slot, appointment_id) VALUES (?,?)", [(k, appt_id) for k in keys])
    return True


def _fits_in_hours(start: datetime, service_id: str) -> bool:
    from .slotlogic import candidate_starts

    return start in candidate_starts(start.date(), service_id, include_past=True)

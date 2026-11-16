"""Booking API for the fictional dental office (FastAPI + SQLite).

Privacy by design: it stores only name and phone, never a reason for the visit or any health data.
"""
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from . import config, db
from .slotlogic import candidate_starts


@asynccontextmanager
async def lifespan(_: FastAPI):
    conn = db.connect()
    db.init(conn)
    refresh(conn)
    conn.close()
    yield


app = FastAPI(title="demo-citas API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def get_conn():
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


def refresh(conn: sqlite3.Connection) -> None:
    """Drop past appointments and top up the fictional ones for the booking window."""
    db.init(conn)
    db.purge_past(conn)
    db.ensure_seed(conn)


# ---------------------------------------------------------------- rate limit
_hits: dict[str, deque] = defaultdict(deque)


def check_rate(request: Request) -> None:
    ip = (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "?")).split(",")[0].strip()
    q, t = _hits[ip], time.monotonic()
    while q and t - q[0] > 3600:
        q.popleft()
    if len(q) >= config.BOOKINGS_PER_IP_PER_HOUR:
        raise HTTPException(429, "Demasiados intentos. Prueba de nuevo en un rato.")
    q.append(t)


# ---------------------------------------------------------------- models
class BookingIn(BaseModel):
    service_id: str
    date: date
    time: str = Field(pattern=r"^\d{2}:\d{2}$")
    name: str = Field(min_length=2, max_length=60)
    phone: str = Field(max_length=20)
    website: str = ""  # honeypot: real people leave it empty

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2 or not all(c.isalpha() or c in " .'-" for c in v):
            raise ValueError("Escribe solo tu nombre, sin números ni símbolos.")
        return v

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) == 12 and digits.startswith("52"):
            digits = digits[2:]
        if len(digits) != 10:
            raise ValueError("El teléfono debe tener 10 dígitos.")
        return digits


class CancelIn(BaseModel):
    token: str


# ---------------------------------------------------------------- routes
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/services")
def services():
    return [
        {k: s[k] for k in ("id", "name", "description", "price_from", "duration_minutes")}
        for s in config.SERVICES.values()
    ]


def _check_window(day: date) -> None:
    today = config.now().date()
    if day < today or day > today + timedelta(days=config.HORIZON_DAYS):
        raise HTTPException(422, f"Elige una fecha dentro de los próximos {config.HORIZON_DAYS} días.")


def _free_starts(conn: sqlite3.Connection, day: date, service_id: str) -> list[datetime]:
    taken = {r["slot"] for r in conn.execute("SELECT slot FROM slots WHERE slot LIKE ?", (day.isoformat() + "%",))}
    return [
        s for s in candidate_starts(day, service_id)
        if not taken.intersection(db.slots_for(s, service_id))
    ]


@app.get("/api/availability")
def availability(service_id: str, date: date, conn: sqlite3.Connection = Depends(get_conn)):
    if service_id not in config.SERVICES:
        raise HTTPException(404, "Servicio no encontrado.")
    _check_window(date)
    refresh(conn)
    return {
        "service_id": service_id,
        "date": date.isoformat(),
        "slots": [s.strftime("%H:%M") for s in _free_starts(conn, date, service_id)],
    }


@app.post("/api/appointments", status_code=201)
def book(body: BookingIn, request: Request, conn: sqlite3.Connection = Depends(get_conn)):
    if body.website:
        raise HTTPException(400, "Solicitud no válida.")
    check_rate(request)
    if body.service_id not in config.SERVICES:
        raise HTTPException(404, "Servicio no encontrado.")
    _check_window(body.date)
    refresh(conn)

    start = datetime.strptime(f"{body.date.isoformat()}T{body.time}", db.FMT)
    if start not in candidate_starts(body.date, body.service_id):
        raise HTTPException(422, "Ese horario no está disponible.")
    count = conn.execute("SELECT COUNT(*) FROM appointments WHERE is_seed = 0").fetchone()[0]
    if count >= config.MAX_FUTURE_APPOINTMENTS:
        raise HTTPException(503, "La demo está llena por ahora. Intenta más tarde.")

    keys = db.slots_for(start, body.service_id)
    end = start + timedelta(minutes=config.SLOT_MINUTES * len(keys))
    appt_id, token = secrets.token_urlsafe(8), secrets.token_urlsafe(16)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "INSERT INTO appointments(id, service_id, start, end, name, phone, token, is_seed, created_at)"
            " VALUES (?,?,?,?,?,?,?,0,?)",
            (appt_id, body.service_id, start.strftime(db.FMT), end.strftime(db.FMT), body.name, body.phone, token, config.now().isoformat()),
        )
        conn.executemany("INSERT INTO slots(slot, appointment_id) VALUES (?,?)", [(k, appt_id) for k in keys])
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:
        conn.execute("ROLLBACK")
        raise HTTPException(409, "Ese horario acaba de ser tomado. Elige otro.")
    svc = config.SERVICES[body.service_id]
    return {
        "id": appt_id,
        "token": token,
        "service": {"id": svc["id"], "name": svc["name"]},
        "start": start.strftime(db.FMT),
        "end": end.strftime(db.FMT),
        "name": body.name,
    }


@app.post("/api/appointments/{appt_id}/cancel")
def cancel(appt_id: str, body: CancelIn, conn: sqlite3.Connection = Depends(get_conn)):
    row = conn.execute("SELECT token, is_seed FROM appointments WHERE id = ?", (appt_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "No encontramos esa cita.")
    if row["is_seed"] or not secrets.compare_digest(row["token"], body.token):
        raise HTTPException(403, "No tienes permiso para cancelar esta cita.")
    conn.execute("DELETE FROM appointments WHERE id = ?", (appt_id,))  # slots go with it (ON DELETE CASCADE)
    return {"status": "cancelled"}

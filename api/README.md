# demo-citas API

Booking API for the fictional dental office. FastAPI + SQLite (standard library), no other dependencies.
It reads `../data/consultorio.json` (services, hours, slot size), so changing that file changes the API.

```bash
cd api
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload        # http://localhost:8000/docs
.venv/bin/python -m pytest -q                   # 15 tests
```

| Method | Path | What it does |
|---|---|---|
| GET | `/api/health` | liveness check |
| GET | `/api/services` | services with price and duration |
| GET | `/api/availability?service_id=&date=` | free start times for a service on a day |
| POST | `/api/appointments` | book (`service_id`, `date`, `time`, `name`, `phone`) |
| POST | `/api/appointments/{id}/cancel` | cancel with the token returned when booking |

**Rules:** 30-minute slots (a service takes as many as its duration needs), bookings up to 14 days ahead and not within the next hour, the primary key on `slots` makes double booking impossible, 8 bookings per IP per hour, and past appointments are purged.

**Privacy:** it stores only name and phone. There is no free-text field and no reason for the visit; extra fields sent by a client are ignored. The demo seeds a few fictional appointments ("Ejemplo", up to 40 % of a day) so the calendar looks lived in.

**Environment:** `DEMO_DB_PATH` (SQLite file), `DEMO_CORS_ORIGINS` (comma separated, default the local Astro dev server), `DEMO_DATA_FILE`.

**Render free plan:** the disk is ephemeral, so appointments disappear on restart and the API reseeds on startup. That is fine for a demo (risk R9).

# demo-citas API

Booking API for the fictional dental office. FastAPI + SQLite (standard library), no other dependencies.
It reads `../data/consultorio.json` (services, hours, slot size), so changing that file changes the API.

```bash
cd api
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/DEMO_ENABLE_DOCS=1 .venv/bin/uvicorn app.main:app --reload   # docs at http://localhost:8000/docs (off by default)
.venv/bin/python -m pytest -q                   # 38 tests (the assistant tests use a fake client)
```

| Method | Path | What it does |
|---|---|---|
| GET | `/api/health` | liveness check |
| GET | `/api/services` | services with price and duration |
| GET | `/api/availability?service_id=&date=` | free start times for a service on a day |
| POST | `/api/appointments` | book (`service_id`, `date`, `time`, `name`, `phone`) |
| POST | `/api/appointments/{id}/cancel` | cancel with the token returned when booking |
| POST | `/api/chat` | FAQ assistant (Claude Haiku 5.5): `{messages: [{role, content}]}` -> `{reply, remaining}` |

**Rules:** 30-minute slots (a service takes as many as its duration needs), bookings up to 14 days ahead and not within the next hour, the primary key on `slots` makes double booking impossible, 8 bookings per IP per hour, and past appointments are purged.

**Privacy:** it stores only name and phone. There is no free-text field and no reason for the visit; extra fields sent by a client are ignored. The demo seeds a few fictional appointments ("Ejemplo", up to 40 % of a day) so the calendar looks lived in.

**Assistant:** `app/assistant.py` builds the system prompt from `data/consultorio.json` and calls `claude-haiku-5-5` with `effort: low` (no sampling parameters, no `fallbacks`: Haiku 5.5 has neither). It answers only with the office's public information, refuses clinical and off-topic questions, and never stores or logs conversations. Limits: 400 characters per message, a 10-message window, 30 messages per IP per hour and a global daily cap (risk R6). Live check against the real API: `set -a; . ./.env; set +a; .venv/bin/python tests/live_assistant.py` (costs a few cents).

**Environment:** `DEMO_DB_PATH` (SQLite file), `DEMO_CORS_ORIGINS` (comma separated, default the local Astro dev server), `DEMO_DATA_FILE`, `ANTHROPIC_API_KEY` (copy `.env.example` to `.env`, which is git-ignored; run with `uvicorn app.main:app --env-file .env`; on Render set it in the dashboard) and `DEMO_ASSISTANT_MODEL`, `DEMO_TRUSTED_PROXIES`, `DEMO_SIGNING_KEY`, `DEMO_ENABLE_DOCS`.

**Security notes**
- **Client IP:** the rate limits use the TCP peer. `X-Forwarded-For` is client-controlled, so it is ignored unless `DEMO_TRUSTED_PROXIES=N` says N proxies are in front; then only the entry the proxy added (N-th from the right) counts. If N is set too high the limiter fails closed (one shared bucket). On Render use `1` and confirm it on the first deploy by checking that two different clients get separate counters.
- **Chat history:** the browser sends it, so every assistant turn carries a signature issued by the server (HMAC-SHA256); unsigned or edited turns are rejected, so nobody can put words in the assistant's mouth. Set `DEMO_SIGNING_KEY` to keep conversations valid across restarts.
- **Limiters** keep at most 5,000 clients in memory. Purge/seed writes run at most once a minute. `/docs`, `/redoc` and `/openapi.json` are disabled unless `DEMO_ENABLE_DOCS=1`.
- **Known limits:** the 30 per hour and 600 per day caps also mean one determined person can use up a day's chat for everyone (a demo trade-off); the 300 appointment cap works the same way. Set a spend limit in the Anthropic console too.

**Render free plan:** the disk is ephemeral, so appointments disappear on restart and the API reseeds on startup. That is fine for a demo (risk R9).

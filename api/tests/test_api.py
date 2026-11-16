import sqlite3

from app import config

from .conftest import book


def free(client, service="assessment", day="2026-11-24"):
    return client.get("/api/availability", params={"service_id": service, "date": day}).json()["slots"]


def test_health_and_services(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert len(client.get("/api/services").json()) == 6


def test_closed_day_has_no_slots(client):
    assert free(client, day="2026-11-29") == []  # Sunday


def test_lead_time_hides_the_next_hour(client):
    slots = free(client, day="2026-11-23")  # today, now is 10:30 (seeded visits may take some)
    assert slots and min(slots) >= "11:30"


def test_service_must_fit_before_closing_time(client):
    # whitening needs 90 min; Saturday is 09:00-14:00, so 12:30 is the last possible start
    slots = free(client, service="whitening", day="2026-11-28")
    assert slots and min(slots) >= "09:00" and max(slots) <= "12:30"


def test_window_is_enforced(client):
    assert client.get("/api/availability", params={"service_id": "assessment", "date": "2026-11-22"}).status_code == 422
    assert client.get("/api/availability", params={"service_id": "assessment", "date": "2026-12-20"}).status_code == 422
    assert client.get("/api/availability", params={"service_id": "nope", "date": "2026-11-24"}).status_code == 404


def test_book_then_slot_disappears(client):
    target = free(client)[0]
    r = book(client, time=target)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Ana Pérez" and data["token"] and data["start"].endswith(target)
    assert target not in free(client)


def test_double_booking_is_rejected(client):
    t = free(client)[0]
    assert book(client, time=t).status_code == 201
    assert book(client, time=t, name="Luis Gómez").status_code in (409, 422)


def test_longer_service_blocks_following_slots(client):
    starts = free(client, service="cleaning")
    t = next(s for s in starts if s in free(client))  # a start with two free slots
    assert book(client, service_id="cleaning", time=t).status_code == 201
    h, m = map(int, t.split(":"))
    second = f"{h + (m + 30) // 60:02d}:{(m + 30) % 60:02d}"
    assert second not in free(client)  # the second block is taken too


def test_cancel_needs_the_right_token(client):
    t = free(client)[0]
    data = book(client, time=t).json()
    bad = client.post(f"/api/appointments/{data['id']}/cancel", json={"token": "wrong"})
    assert bad.status_code == 403
    ok = client.post(f"/api/appointments/{data['id']}/cancel", json={"token": data["token"]})
    assert ok.status_code == 200
    assert t in free(client)  # the slot is free again


def test_seeded_appointments_cannot_be_cancelled(client):
    conn = sqlite3.connect(config.DB_PATH)
    seed_id = conn.execute("SELECT id FROM appointments WHERE is_seed = 1 LIMIT 1").fetchone()[0]
    r = client.post(f"/api/appointments/{seed_id}/cancel", json={"token": "-"})
    assert r.status_code == 403


def test_validation(client):
    t = free(client)[0]
    assert book(client, time=t, phone="123").status_code == 422
    assert book(client, time=t, name="Ana 123").status_code == 422
    assert book(client, time=t, name="A").status_code == 422
    assert book(client, time=t, website="http://spam").status_code == 400
    assert book(client, time="03:00").status_code == 422  # outside opening hours


def test_phone_is_normalized(client):
    t = free(client)[0]
    assert book(client, time=t, phone="+52 33 1234 5678").status_code == 201
    conn = sqlite3.connect(config.DB_PATH)
    assert conn.execute("SELECT phone FROM appointments WHERE is_seed = 0").fetchone()[0] == "3312345678"


def test_only_name_and_phone_are_stored(client):
    cols = {r[1] for r in sqlite3.connect(config.DB_PATH).execute("PRAGMA table_info(appointments)")}
    assert cols == {"id", "service_id", "start", "end", "name", "phone", "token", "is_seed", "created_at"}
    # an extra "reason" field sent by a client is ignored, not stored
    t = free(client)[0]
    assert book(client, time=t, motivo="me duele una muela").status_code == 201
    conn = sqlite3.connect(config.DB_PATH)
    dump = " ".join(str(v) for row in conn.execute("SELECT * FROM appointments WHERE is_seed = 0") for v in row)
    assert "muela" not in dump


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(config, "BOOKINGS_PER_IP_PER_HOUR", 2)
    slots = free(client)
    assert book(client, time=slots[0]).status_code == 201
    assert book(client, time=slots[1]).status_code == 201
    assert book(client, time=slots[2]).status_code == 429


def test_seeding_never_fills_a_day(client):
    for offset in range(0, 15):
        day = f"2026-11-{23 + offset:02d}" if offset < 8 else f"2026-12-{offset - 7:02d}"
        for service in ("assessment", "whitening"):
            slots = client.get("/api/availability", params={"service_id": service, "date": day})
            assert slots.status_code == 200
            if day not in ("2026-11-29", "2026-12-06"):  # Sundays are closed
                assert slots.json()["slots"], f"{service} has no free slot on {day}"

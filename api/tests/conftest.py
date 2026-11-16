from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import config, main

# Monday 2026-11-23, 10:30 in Mexico City
FIXED_NOW = datetime(2026, 11, 23, 10, 30, tzinfo=config.TZ)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.setattr(config, "now", lambda: FIXED_NOW)
    main._hits.clear()
    main._chat_hits.clear()
    main._chat_day.update(day="", count=0)
    with TestClient(main.app) as c:
        yield c


def book(client, **over):
    body = {"service_id": "assessment", "date": "2026-11-24", "time": "10:00", "name": "Ana Pérez", "phone": "33 1234 5678"}
    body.update(over)
    return client.post("/api/appointments", json=body)

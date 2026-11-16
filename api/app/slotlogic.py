"""Pure scheduling rules: which start times exist for a service on a date."""
from datetime import date, datetime, timedelta

from . import config


def _parse(day: date, hhmm: str) -> datetime:
    h, m = hhmm.split(":")
    return datetime(day.year, day.month, day.day, int(h), int(m))


def candidate_starts(day: date, service_id: str, include_past: bool = False) -> list[datetime]:
    """Start times inside opening hours where the whole service fits (naive local datetimes)."""
    svc = config.SERVICES[service_id]
    block = timedelta(minutes=config.SLOT_MINUTES * -(-svc["duration_minutes"] // config.SLOT_MINUTES))
    step = timedelta(minutes=config.SLOT_MINUTES)
    earliest = config.now().replace(tzinfo=None) + timedelta(minutes=config.MIN_LEAD_MINUTES)
    out: list[datetime] = []
    for a, b in config.HOURS[day.weekday()]:
        t, end = _parse(day, a), _parse(day, b)
        while t + block <= end:
            if include_past or t >= earliest:
                out.append(t)
            t += step
    return out

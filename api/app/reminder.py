"""Simulated WhatsApp reminder text. Nothing is ever sent: it is only previewed in the doctor's view."""
from datetime import datetime

from . import config

WEEKDAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def build(name: str, service_name: str, start: datetime) -> str:
    """Plain text (the page renders it with textContent). Names are validated to letters on booking."""
    first = name.split()[0] if name and name != "Ejemplo" else ""
    greeting = f"Hola {first}," if first else "Hola,"
    when = f"{WEEKDAYS[start.weekday()]} {start.day} de {MONTHS[start.month - 1]} a las {start.strftime('%H:%M')}"
    return (
        f"{greeting} te recordamos tu cita en {config.SITE['business']['name']}:\n"
        f"{service_name}, {when}.\n"
        "Si no puedes asistir, avísanos con 24 horas de anticipación respondiendo este mensaje. ¡Te esperamos!"
    )

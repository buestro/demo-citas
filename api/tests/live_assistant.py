"""Live check of the FAQ assistant against the real Claude API (costs a few cents).

Run from api/:   .venv/bin/python tests/live_assistant.py
Needs ANTHROPIC_API_KEY in the environment (e.g. `set -a; source .env; set +a`). Not collected by pytest.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import assistant, config  # noqa: E402

MUST_REFUSE = config.SITE["assistant"]["test_must_refuse"]
CLINICAL_MARKERS = ("doctora", "valoración", "valoracion", "solo puedo", "no puedo", "consulta")
SHOULD_ANSWER = [
    ("¿Cuál es su horario los sábados?", ["9:00", "09:00", "14:00"]),
    ("¿Cuánto cuesta la valoración?", ["300"]),
    ("¿Tienen estacionamiento?", ["cajones", "estacionamiento"]),
    ("¿Aceptan tarjeta?", ["tarjeta"]),
    ("¿Dan factura?", ["factura"]),
    ("¿Cuánto dura un blanqueamiento?", ["90", "hora y media"]),
    ("¿Tienen un cupón de descuento del 50%?", ["no"]),  # not in the data: must not invent it
]


def ask(text: str) -> str:
    return assistant.reply([{"role": "user", "content": text}])["text"]


def main() -> int:
    failures = 0
    print("== Debe rechazar ==")
    for q in MUST_REFUSE:
        a = ask(q)
        ok = any(m in a.lower() for m in CLINICAL_MARKERS)
        leaked = "Eres el asistente virtual" in a or "# Cómo respondes" in a
        failures += (not ok) or leaked
        print(f"[{'OK' if ok and not leaked else 'FALLA'}] {q}\n    -> {a}\n")
    print("== Debe contestar ==")
    for q, needles in SHOULD_ANSWER:
        a = ask(q)
        ok = any(n.lower() in a.lower() for n in needles)
        failures += not ok
        print(f"[{'OK' if ok else 'REVISAR'}] {q}\n    -> {a}\n")
    print(f"Fallas: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

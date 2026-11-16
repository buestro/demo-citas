"""Signatures for assistant replies, so a client cannot invent turns of the assistant in the chat history."""
import hashlib
import hmac
import os
import secrets

# Set DEMO_SIGNING_KEY to keep conversations valid across restarts; otherwise a random key per process.
_KEY = os.environ.get("DEMO_SIGNING_KEY", "").encode() or secrets.token_bytes(32)


def sign(text: str) -> str:
    return hmac.new(_KEY, text.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def verify(text: str, sig: str) -> bool:
    return bool(sig) and hmac.compare_digest(sign(text), sig)

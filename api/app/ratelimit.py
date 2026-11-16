"""Per-client rate limiting with a bounded memory footprint, and a client IP that cannot be spoofed."""
import time
from collections import OrderedDict, deque
from typing import Callable

from fastapi import HTTPException, Request

from . import config


def client_ip(request: Request) -> str:
    """The TCP peer, or, behind N trusted proxies, the entry our own proxy added (N-th from the right).

    X-Forwarded-For is client-controlled on its left side, so the first value is never trusted.
    If the header is shorter than expected we fall back to the TCP peer.
    """
    peer = request.client.host if request.client else "unknown"
    n = config.TRUSTED_PROXIES
    if n > 0:
        parts = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
        if len(parts) >= n:
            return parts[-n]
    return peer


class RateLimiter:
    def __init__(self, limit: Callable[[], int], message: str, window: float = 3600.0):
        self.limit, self.message, self.window = limit, message, window
        self.hits: "OrderedDict[str, deque]" = OrderedDict()

    def reset(self) -> None:
        self.hits.clear()

    def hit(self, request: Request) -> None:
        now, key = time.monotonic(), client_ip(request)
        # drop clients whose last hit is outside the window (least recently used come first)
        while self.hits and now - next(iter(self.hits.values()))[-1] > self.window:
            self.hits.popitem(last=False)
        q = self.hits.setdefault(key, deque())
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit():
            raise HTTPException(429, self.message)
        q.append(now)
        self.hits.move_to_end(key)
        while len(self.hits) > config.MAX_TRACKED_IPS:  # hard cap: forget the least recently used
            self.hits.popitem(last=False)

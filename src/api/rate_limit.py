"""Rate limiting for Phase 3.

Uses a sliding-window approach backed by in-memory counters.
Configurable via env vars:
- AGENT_RATE_LIMIT_REQUESTS: max requests per window (default 60)
- AGENT_RATE_LIMIT_WINDOW_SECONDS: window size in seconds (default 60)
- AGENT_RATE_LIMIT_LIMIT_HEADER: if true, include X-RateLimit-* headers
"""
from __future__ import annotations

import time
from threading import Lock
from typing import Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from src.config.settings import get_settings


class SlidingWindowRateLimiter:
    def __init__(self):
        self._windows: dict[str, Tuple[float, int]] = {}
        self._lock = Lock()

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "anon"

    def is_allowed(self, key: str, limit: int, window: float) -> bool:
        now = time.time()
        with self._lock:
            start, count = self._windows.get(key, (now, 0))
            if now - start >= window:
                self._windows[key] = (now, 1)
                return True
            if count >= limit:
                return False
            self._windows[key] = (start, count + 1)
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        try:
            limit = int(getattr(settings, "rate_limit_requests", 60))
        except (TypeError, ValueError):
            limit = 60
        try:
            window = float(getattr(settings, "rate_limit_window_seconds", 60))
        except (TypeError, ValueError):
            window = 60.0

        limiter = SlidingWindowRateLimiter()
        key = limiter._client_key(request)

        if not limiter.is_allowed(key, limit, window):
            return Response(status_code=429, content="Rate limit exceeded. Please retry later.")

        response = await call_next(request)
        if getattr(settings, "rate_limit_limit_header", False):
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = "0"
        return response

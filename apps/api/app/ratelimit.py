"""Rate limiting configuration using slowapi (Redis-backed)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _get_session_key(request: Request) -> str:
    """Rate-limit key: use session_id from JWT if available, else fall back to IP."""
    state = getattr(request, "state", None)
    if state is not None:
        rid = getattr(state, "request_id", None)
        if rid:
            return rid
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        try:
            from apps.api.app.auth.jwt import decode_token

            payload = decode_token(auth[7:])
            return payload.get("session_id", get_remote_address(request))
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(
    key_func=_get_session_key,
    default_limits=["200/minute"],
    storage_uri="memory://",
)

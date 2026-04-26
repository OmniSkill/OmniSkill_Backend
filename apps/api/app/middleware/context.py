"""Context resolver middleware – injects CountryConfig into request.state."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.api.app.auth.jwt import decode_token


class ContextResolverMiddleware(BaseHTTPMiddleware):
    """Resolve context_id from JWT or X-Context-Id header and load CountryConfig."""

    EXEMPT_PREFIXES = ("/health", "/ready", "/docs", "/openapi.json", "/api/v1/auth")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if any(path.startswith(p) for p in self.EXEMPT_PREFIXES):
            return await call_next(request)

        context_id = self._extract_context_id(request)
        if context_id:
            loader = getattr(request.app.state, "config_loader", None)
            if loader is not None:
                try:
                    config = await loader.get(context_id)
                    request.state.context = config
                    request.state.context_id = context_id
                except Exception:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "invalid_context",
                            "detail": f"Unknown context_id: '{context_id}'. "
                            "Use GET /api/v1/config/contexts to list available contexts.",
                        },
                    )

        return await call_next(request)

    def _extract_context_id(self, request: Request) -> str:
        header_val = request.headers.get("x-context-id", "")
        if header_val:
            return header_val

        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            try:
                payload = decode_token(auth[7:])
                return payload.get("context_id", "")
            except Exception:
                pass

        return ""

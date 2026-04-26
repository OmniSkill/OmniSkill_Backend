"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from apps.api.app.auth.jwt import decode_token
from apps.api.app.schemas.auth import TokenPayload

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_token_payload(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> TokenPayload:
    """Extract and validate the JWT from the Authorization header."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    try:
        data = decode_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    session_valid = await request.app.state.auth_service.validate_session(data["session_id"])
    if not session_valid:
        raise HTTPException(status_code=401, detail="Session has been revoked")

    return TokenPayload(**data)


async def get_current_context(
    request: Request,
    token: TokenPayload = Depends(get_token_payload),
    x_context_id: str | None = Header(None),
) -> str:
    """Resolve the active context_id from JWT claim or X-Context-Id header fallback."""
    context_id = token.context_id or x_context_id or ""
    if not context_id:
        raise HTTPException(
            status_code=400,
            detail="No context_id found. Provide it via JWT claim or X-Context-Id header.",
        )

    loader = request.app.state.config_loader
    try:
        config = await loader.get(context_id)
        request.state.context = config
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown context_id: '{context_id}'. Use GET /api/v1/config/contexts to list available contexts.",
        ) from exc

    return context_id


def require_role(*roles: str):
    """Dependency factory that enforces role-based access."""

    async def _check(token: TokenPayload = Depends(get_token_payload)) -> TokenPayload:
        if token.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return token

    return _check

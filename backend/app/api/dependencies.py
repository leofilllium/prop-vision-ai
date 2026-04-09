"""
API key authentication, JWT authentication, and rate limiting dependencies.
"""

import hashlib
import time
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from app.database import get_db
from app.models.partner import Partner
from app.config import get_settings

settings = get_settings()

_bearer = HTTPBearer(auto_error=False)


async def get_partner_by_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Partner:
    """
    Validate the X-API-Key header and return the associated Partner.

    Hashes the provided API key with SHA-256 and looks up the partner
    in the database. Returns 401 if the key is missing or invalid.
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header",
        )

    # Hash the API key and lookup
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    result = await db.execute(
        select(Partner).where(
            Partner.api_key_hash == key_hash,
            Partner.is_active == True,  # noqa: E712
        )
    )
    partner = result.scalar_one_or_none()

    if partner is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key",
        )

    # Store partner in request state for logging
    request.state.partner_id = str(partner.id)
    return partner


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> Partner | None:
    """
    Dual-mode auth: accepts JWT Bearer (web app) or X-API-Key (B2B partners).

    - JWT Bearer → validates token, sets request.state.partner_id to user:<id>, returns None.
    - X-API-Key  → looks up partner, applies rate limiting, returns Partner.
    - Neither    → 401.
    """
    from app.models.user import User
    from app.services.auth_service import decode_access_token

    # ── 1. JWT Bearer ──────────────────────────────
    if credentials:
        try:
            email = decode_access_token(credentials.credentials)
            result = await db.execute(select(User).where(User.email == email, User.is_active == True))  # noqa: E712
            user = result.scalar_one_or_none()
            if user:
                request.state.partner_id = f"user:{user.id}"
                return None
        except JWTError:
            pass  # fall through to API key

    # ── 2. X-API-Key ───────────────────────────────
    api_key = request.headers.get("X-API-Key")
    if api_key:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        result = await db.execute(
            select(Partner).where(
                Partner.api_key_hash == key_hash,
                Partner.is_active == True,  # noqa: E712
            )
        )
        partner = result.scalar_one_or_none()
        if partner:
            request.state.partner_id = str(partner.id)
            return partner

    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide a Bearer token or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    """Validate a Bearer JWT and return the authenticated User."""
    from app.models.user import User
    from app.services.auth_service import decode_access_token

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        email = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.email == email, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_admin_user(current_user=Depends(get_current_user)):
    """Validate that the current user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )
    return current_user


async def check_rate_limit(
    request: Request,
    partner: Partner = Depends(get_partner_by_api_key),
) -> Partner:
    """
    Check rate limiting for the authenticated partner.

    Uses Redis sliding window counter. Allows settings.rate_limit_per_minute
    requests per minute per API key. Returns 429 if exceeded.
    """
    redis = request.app.state.redis
    rate_key = f"rate_limit:{partner.id}"
    current_time = int(time.time())
    window_start = current_time - 60

    pipe = redis.pipeline()
    # Remove old entries outside the 1-minute window
    pipe.zremrangebyscore(rate_key, 0, window_start)
    # Count requests in current window
    pipe.zcard(rate_key)
    # Add current request
    pipe.zadd(rate_key, {str(current_time) + ":" + str(id(request)): current_time})
    # Set expiry on the key
    pipe.expire(rate_key, 120)
    results = await pipe.execute()

    request_count = results[1]

    # Set rate limit headers
    request.state.rate_limit = settings.rate_limit_per_minute
    request.state.rate_remaining = max(0, settings.rate_limit_per_minute - request_count - 1)
    request.state.rate_reset = current_time + 60

    if request_count >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum {} requests per minute.".format(settings.rate_limit_per_minute),
            headers={"Retry-After": "60"},
        )

    return partner

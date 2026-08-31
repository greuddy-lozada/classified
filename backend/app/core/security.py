from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

_hasher = PasswordHash.recommended()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _hasher.verify(plain, hashed)


def create_access_token(
    *,
    sub: str,
    org_id: str | None,
    rol: str | None,
    es_plataforma: bool,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": sub,
        "org_id": org_id,
        "rol": rol,
        "es_plataforma": es_plataforma,
        "typ": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_ttl_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, sub: str) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": sub,
        "typ": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_ttl_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def as_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    return UUID(value)

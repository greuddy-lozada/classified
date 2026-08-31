from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.usuario import Usuario

bearer = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(
        self,
        usuario: Usuario,
        org_id: UUID | None,
        rol: str | None,
        es_plataforma: bool,
    ) -> None:
        self.usuario = usuario
        self.org_id = org_id
        self.rol = rol
        self.es_plataforma = es_plataforma


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> CurrentUser:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    try:
        payload = decode_token(creds.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc
    if payload.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = db.get(Usuario, UUID(payload["sub"]))
    if user is None or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo")
    org_raw = payload.get("org_id")
    return CurrentUser(
        usuario=user,
        org_id=UUID(org_raw) if org_raw else None,
        rol=payload.get("rol"),
        es_plataforma=bool(payload.get("es_plataforma")),
    )


def require_org(current: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if current.org_id is None or current.rol is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Selecciona un plantel")
    return current

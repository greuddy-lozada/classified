from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.models.membresia import Membresia
from app.models.usuario import Usuario
from app.schemas.auth import MembresiaOut, TokenOut


def _membresias_out(user: Usuario) -> list[MembresiaOut]:
    return [
        MembresiaOut(
            organizacion_id=m.organizacion_id,
            organizacion_nombre=m.organizacion.nombre,
            rol=m.rol.value,
        )
        for m in user.membresias
        if m.activo
    ]


def _tokens(user: Usuario, org_id: str | None, rol: str | None) -> TokenOut:
    return TokenOut(
        access_token=create_access_token(
            sub=str(user.id),
            org_id=org_id,
            rol=rol,
            es_plataforma=user.es_plataforma,
        ),
        refresh_token=create_refresh_token(sub=str(user.id)),
        membresias=_membresias_out(user),
    )


def login(db: Session, email: str, password: str) -> TokenOut:
    user = (
        db.query(Usuario)
        .options(joinedload(Usuario.membresias).joinedload(Membresia.organizacion))
        .filter(Usuario.email == email)
        .first()
    )
    if user is None or not user.activo or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    org_id = None
    rol = None
    activas = [m for m in user.membresias if m.activo]
    if len(activas) == 1:
        org_id = str(activas[0].organizacion_id)
        rol = activas[0].rol.value
    return _tokens(user, org_id, rol)


def seleccionar(db: Session, user: Usuario, organizacion_id: UUID, rol: str) -> TokenOut:
    db.refresh(user)
    user = (
        db.query(Usuario)
        .options(joinedload(Usuario.membresias).joinedload(Membresia.organizacion))
        .filter(Usuario.id == user.id)
        .one()
    )
    match = next(
        (
            m
            for m in user.membresias
            if m.activo and m.organizacion_id == organizacion_id and m.rol.value == rol
        ),
        None,
    )
    if match is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin membresía")
    return _tokens(user, str(match.organizacion_id), match.rol.value)

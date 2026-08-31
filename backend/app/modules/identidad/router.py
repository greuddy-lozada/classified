from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.modules.identidad.service import login, seleccionar
from app.schemas.auth import LoginIn, MeOut, SeleccionarIn, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def auth_login(body: LoginIn, db: Annotated[Session, Depends(get_db)]) -> TokenOut:
    return login(db, body.email, body.password)


@router.post("/seleccionar", response_model=TokenOut)
def auth_seleccionar(
    body: SeleccionarIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> TokenOut:
    return seleccionar(db, current.usuario, body.organizacion_id, body.rol)


@router.get("/me", response_model=MeOut)
def auth_me(current: Annotated[CurrentUser, Depends(get_current_user)]) -> MeOut:
    return MeOut(
        id=current.usuario.id,
        email=current.usuario.email,
        es_plataforma=current.es_plataforma,
        organizacion_id=current.org_id,
        rol=current.rol,
    )

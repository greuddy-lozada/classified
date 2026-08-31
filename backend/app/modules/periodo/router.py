from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_org
from app.db.session import get_db
from app.modules.periodo.service import crear_anio, crear_grado, crear_seccion, listar_anios, listar_grados
from app.schemas.periodo import AnioCreate, AnioOut, GradoCreate, GradoOut, SeccionCreate, SeccionOut

router = APIRouter(prefix="/periodo", tags=["periodo"])

_WRITE = {"direccion"}
_READ = {"direccion", "secretaria"}


def _org_id(current: CurrentUser) -> UUID:
    if current.org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Selecciona un plantel")
    return current.org_id


def _require_write(current: CurrentUser) -> None:
    if current.rol not in _WRITE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


def _require_read(current: CurrentUser) -> None:
    if current.rol not in _READ:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


@router.post("/anios", response_model=AnioOut, status_code=status.HTTP_201_CREATED)
def post_anio(
    body: AnioCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> AnioOut:
    _require_write(current)
    return crear_anio(db, _org_id(current), body.nombre)


@router.get("/anios", response_model=list[AnioOut])
def get_anios(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> list[AnioOut]:
    _require_read(current)
    return listar_anios(db, _org_id(current))


@router.post("/grados", response_model=GradoOut, status_code=status.HTTP_201_CREATED)
def post_grado(
    body: GradoCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> GradoOut:
    _require_write(current)
    return crear_grado(
        db,
        _org_id(current),
        body.anio_escolar_id,
        body.nivel,
        body.nombre,
        body.esquema_evaluacion,
    )


@router.get("/grados", response_model=list[GradoOut])
def get_grados(
    anio_escolar_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> list[GradoOut]:
    _require_read(current)
    return listar_grados(db, _org_id(current), anio_escolar_id)


@router.post("/secciones", response_model=SeccionOut, status_code=status.HTTP_201_CREATED)
def post_seccion(
    body: SeccionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> SeccionOut:
    _require_write(current)
    return crear_seccion(db, _org_id(current), body.grado_id, body.letra, body.turno)

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_org
from app.db.session import get_db
from app.modules.inscripcion.service import (
    activar,
    asignar_seccion,
    crear,
    listar,
    marcar_matricula,
    marcar_recaudo,
    mis_inscripciones,
    retirar,
)
from app.schemas.inscripcion import (
    AsignarSeccionIn,
    InscripcionCreate,
    InscripcionOut,
    MatriculaPatch,
    RecaudoPatch,
)

router = APIRouter(prefix="/inscripciones", tags=["inscripciones"])

_STAFF = {"direccion", "secretaria"}


def _org_id(current: CurrentUser) -> UUID:
    if current.org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Selecciona un plantel")
    return current.org_id


def _staff(current: CurrentUser) -> None:
    if current.rol not in _STAFF:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


@router.post("", response_model=InscripcionOut, status_code=status.HTTP_201_CREATED)
def post_inscripcion(
    body: InscripcionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> InscripcionOut:
    _staff(current)
    return crear(db, _org_id(current), body.alumno_id, body.anio_escolar_id)


@router.get("", response_model=list[InscripcionOut])
def get_inscripciones(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
    anio_escolar_id: UUID | None = None,
) -> list[InscripcionOut]:
    if current.rol not in {"direccion", "secretaria", "docente"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return listar(db, _org_id(current), anio_escolar_id)


@router.get("/mias", response_model=list[InscripcionOut])
def get_mias(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> list[InscripcionOut]:
    if current.rol != "representante":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return mis_inscripciones(db, _org_id(current), current.usuario.id)


@router.post("/{inscripcion_id}/seccion", response_model=InscripcionOut)
def post_seccion(
    inscripcion_id: UUID,
    body: AsignarSeccionIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> InscripcionOut:
    _staff(current)
    return asignar_seccion(db, _org_id(current), inscripcion_id, body.seccion_id)


@router.post("/{inscripcion_id}/activar", response_model=InscripcionOut)
def post_activar(
    inscripcion_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> InscripcionOut:
    _staff(current)
    return activar(db, _org_id(current), inscripcion_id)


@router.post("/{inscripcion_id}/retirar", response_model=InscripcionOut)
def post_retirar(
    inscripcion_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> InscripcionOut:
    _staff(current)
    return retirar(db, _org_id(current), inscripcion_id)


@router.patch("/{inscripcion_id}/recaudos", response_model=InscripcionOut)
def patch_recaudo(
    inscripcion_id: UUID,
    body: RecaudoPatch,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> InscripcionOut:
    _staff(current)
    return marcar_recaudo(db, _org_id(current), inscripcion_id, body.tipo, body.estado)


@router.patch("/{inscripcion_id}/matricula", response_model=InscripcionOut)
def patch_matricula(
    inscripcion_id: UUID,
    body: MatriculaPatch,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> InscripcionOut:
    _staff(current)
    return marcar_matricula(db, _org_id(current), inscripcion_id, body.estado_matricula)

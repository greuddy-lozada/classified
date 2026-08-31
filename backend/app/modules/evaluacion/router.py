from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_org
from app.db.session import get_db
from app.modules.evaluacion.service import (
    asignar_docente,
    boletin,
    cargar_informe,
    cargar_nota,
    crear_materia,
    listar_materias,
)
from app.schemas.evaluacion import (
    AsignacionCreate,
    AsignacionOut,
    BoletinOut,
    InformeIn,
    InformeOut,
    MateriaCreate,
    MateriaOut,
    NotaIn,
    NotaOut,
)

router = APIRouter(prefix="/evaluacion", tags=["evaluacion"])

_STAFF = {"direccion", "secretaria"}


def _org_id(current: CurrentUser) -> UUID:
    if current.org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Selecciona un plantel")
    return current.org_id


def _staff(current: CurrentUser) -> None:
    if current.rol not in _STAFF:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


@router.post("/materias", response_model=MateriaOut, status_code=status.HTTP_201_CREATED)
def post_materia(
    body: MateriaCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> MateriaOut:
    _staff(current)
    return crear_materia(db, _org_id(current), body.grado_id, body.nombre)


@router.get("/materias", response_model=list[MateriaOut])
def get_materias(
    grado_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> list[MateriaOut]:
    _staff(current)
    return listar_materias(db, _org_id(current), grado_id)


@router.post("/asignaciones", response_model=AsignacionOut, status_code=status.HTTP_201_CREATED)
def post_asignacion(
    body: AsignacionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> AsignacionOut:
    if current.rol != "direccion":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return asignar_docente(db, _org_id(current), body.usuario_id, body.seccion_id, body.materia_id)


@router.post("/notas", response_model=NotaOut)
def post_nota(
    body: NotaIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> NotaOut:
    return cargar_nota(
        db,
        current,
        _org_id(current),
        body.inscripcion_id,
        body.lapso_id,
        body.materia_id,
        body.valor,
    )


@router.post("/informes", response_model=InformeOut)
def post_informe(
    body: InformeIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> InformeOut:
    return cargar_informe(
        db,
        current,
        _org_id(current),
        body.inscripcion_id,
        body.lapso_id,
        body.area,
        body.juicio,
        body.comentario,
    )


@router.get("/boletines/{inscripcion_id}", response_model=BoletinOut)
def get_boletin(
    inscripcion_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> BoletinOut:
    return boletin(db, current, _org_id(current), inscripcion_id)

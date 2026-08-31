from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_org
from app.db.session import get_db
from app.modules.asistencia.service import lista, marcar, mis_resumenes, resumen
from app.schemas.asistencia import AsistenciaIn, ListaItemOut, ResumenOut

router = APIRouter(prefix="/asistencia", tags=["asistencia"])


def _org_id(current: CurrentUser) -> UUID:
    if current.org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Selecciona un plantel")
    return current.org_id


@router.get("/lista", response_model=list[ListaItemOut])
def get_lista(
    seccion_id: UUID,
    fecha: date,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
    materia_id: UUID | None = None,
) -> list[ListaItemOut]:
    if current.rol not in {"direccion", "secretaria", "docente"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return lista(db, _org_id(current), seccion_id, fecha, materia_id)


@router.put("", response_model=ListaItemOut)
def put_asistencia(
    body: AsistenciaIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> ListaItemOut:
    return marcar(
        db,
        current,
        _org_id(current),
        body.inscripcion_id,
        body.fecha,
        body.estado,
        body.materia_id,
    )


@router.get("/mias", response_model=list[ResumenOut])
def get_mias(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> list[ResumenOut]:
    if current.rol != "representante":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return mis_resumenes(db, _org_id(current), current.usuario.id)


@router.get("/{inscripcion_id}", response_model=ResumenOut)
def get_resumen(
    inscripcion_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
    materia_id: UUID | None = None,
) -> ResumenOut:
    if current.rol not in {"direccion", "secretaria", "docente"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return resumen(db, _org_id(current), inscripcion_id, materia_id)

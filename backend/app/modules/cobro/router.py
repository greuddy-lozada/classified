from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_org
from app.db.session import get_db
from app.models.enums import EstadoMatricula
from app.modules.cobro.service import generar, listar, marcar, mios
from app.schemas.cobro import CargoOut, CargoPatch, GenerarIn

router = APIRouter(prefix="/cobro", tags=["cobro"])

_STAFF = {"direccion", "secretaria"}


def _org_id(current: CurrentUser) -> UUID:
    if current.org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Selecciona un plantel")
    return current.org_id


def _staff(current: CurrentUser) -> None:
    if current.rol not in _STAFF:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


@router.post("/generar", response_model=list[CargoOut])
def post_generar(
    body: GenerarIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> list[CargoOut]:
    _staff(current)
    return generar(db, _org_id(current), body.anio_escolar_id, body.periodos)


@router.get("", response_model=list[CargoOut])
def get_cargos(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
    anio_escolar_id: UUID | None = None,
    estado: EstadoMatricula | None = None,
) -> list[CargoOut]:
    _staff(current)
    return listar(db, _org_id(current), anio_escolar_id, estado)


@router.get("/mios", response_model=list[CargoOut])
def get_mios(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> list[CargoOut]:
    if current.rol != "representante":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return mios(db, _org_id(current), current.usuario.id)


@router.patch("/{cargo_id}", response_model=CargoOut)
def patch_cargo(
    cargo_id: UUID,
    body: CargoPatch,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> CargoOut:
    _staff(current)
    return marcar(db, _org_id(current), cargo_id, body.estado, body.fecha_pago, body.nota)

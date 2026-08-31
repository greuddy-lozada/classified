from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_org
from app.db.session import get_db
from app.modules.periodo.service import (
    actualizar_anio,
    actualizar_grado,
    actualizar_seccion,
    borrar_anio,
    borrar_grado,
    borrar_seccion,
    cerrar_lapso,
    crear_anio,
    crear_grado,
    crear_seccion,
    listar_anios,
    listar_grados,
    reabrir_lapso,
)
from app.schemas.periodo import (
    AnioCreate,
    AnioOut,
    AnioUpdate,
    GradoCreate,
    GradoOut,
    GradoUpdate,
    LapsoOut,
    SeccionCreate,
    SeccionOut,
    SeccionUpdate,
)

router = APIRouter(prefix="/periodo", tags=["periodo"])

_WRITE = {"direccion"}
_READ = {"direccion", "secretaria", "docente"}


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


@router.patch("/anios/{anio_id}", response_model=AnioOut)
def patch_anio(
    anio_id: UUID,
    body: AnioUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> AnioOut:
    _require_write(current)
    return actualizar_anio(db, _org_id(current), anio_id, body.nombre)


@router.delete("/anios/{anio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_anio(
    anio_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> None:
    _require_write(current)
    borrar_anio(db, _org_id(current), anio_id)


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


@router.patch("/grados/{grado_id}", response_model=GradoOut)
def patch_grado(
    grado_id: UUID,
    body: GradoUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> GradoOut:
    _require_write(current)
    return actualizar_grado(db, _org_id(current), grado_id, body.nombre)


@router.delete("/grados/{grado_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grado(
    grado_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> None:
    _require_write(current)
    borrar_grado(db, _org_id(current), grado_id)


@router.post("/secciones", response_model=SeccionOut, status_code=status.HTTP_201_CREATED)
def post_seccion(
    body: SeccionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> SeccionOut:
    _require_write(current)
    return crear_seccion(db, _org_id(current), body.grado_id, body.letra, body.turno)


@router.patch("/secciones/{seccion_id}", response_model=SeccionOut)
def patch_seccion(
    seccion_id: UUID,
    body: SeccionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> SeccionOut:
    _require_write(current)
    return actualizar_seccion(db, _org_id(current), seccion_id, body.letra, body.turno)


@router.delete("/secciones/{seccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seccion(
    seccion_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> None:
    _require_write(current)
    borrar_seccion(db, _org_id(current), seccion_id)


@router.post("/lapsos/{lapso_id}/cerrar", response_model=LapsoOut)
def post_cerrar_lapso(
    lapso_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> LapsoOut:
    _require_write(current)
    return cerrar_lapso(db, _org_id(current), lapso_id)


@router.post("/lapsos/{lapso_id}/reabrir", response_model=LapsoOut)
def post_reabrir_lapso(
    lapso_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> LapsoOut:
    _require_write(current)
    return reabrir_lapso(db, _org_id(current), lapso_id)

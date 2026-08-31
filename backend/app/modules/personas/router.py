from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_org
from app.db.session import get_db
from app.modules.personas.service import (
    actualizar_persona,
    borrar_persona,
    crear_alumno,
    crear_docente,
    crear_representante,
    listar,
    mis_pupilos,
    obtener,
)
from app.schemas.persona import DocenteCreate, PersonaCreate, PersonaOut, PersonaUpdate, RepresentanteCreate

router = APIRouter(prefix="/personas", tags=["personas"])

_STAFF = {"direccion", "secretaria"}


def _staff(current: CurrentUser) -> CurrentUser:
    if current.rol not in _STAFF:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return current


@router.post("/alumnos", response_model=PersonaOut, status_code=status.HTTP_201_CREATED)
def post_alumno(
    body: PersonaCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> PersonaOut:
    _staff(current)
    return crear_alumno(db, current.org_id, **body.model_dump())


@router.get("", response_model=list[PersonaOut])
def get_personas(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> list[PersonaOut]:
    _staff(current)
    return listar(db, current.org_id)


@router.post("/representantes", response_model=PersonaOut, status_code=status.HTTP_201_CREATED)
def post_representante(
    body: RepresentanteCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> PersonaOut:
    _staff(current)
    return crear_representante(db, current.org_id, **body.model_dump())


@router.post("/docentes", response_model=PersonaOut, status_code=status.HTTP_201_CREATED)
def post_docente(
    body: DocenteCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> PersonaOut:
    _staff(current)
    return crear_docente(db, current.org_id, **body.model_dump())


@router.get("/mis-pupilos", response_model=list[PersonaOut])
def get_mis_pupilos(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> list[PersonaOut]:
    if current.rol != "representante":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return mis_pupilos(db, current.org_id, current.usuario.id)


@router.get("/{persona_id}", response_model=PersonaOut)
def get_persona(
    persona_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> PersonaOut:
    _staff(current)
    return obtener(db, current.org_id, persona_id)


@router.patch("/{persona_id}", response_model=PersonaOut)
def patch_persona(
    persona_id: UUID,
    body: PersonaUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> PersonaOut:
    _staff(current)
    return actualizar_persona(
        db,
        current.org_id,
        persona_id,
        body.tipo_doc,
        body.numero_doc,
        body.nombres,
        body.apellidos,
    )


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_persona(
    persona_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> None:
    _staff(current)
    borrar_persona(db, current.org_id, persona_id)

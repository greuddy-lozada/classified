from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_org
from app.db.session import get_db
from app.modules.personas.service import crear_alumno, listar, obtener
from app.schemas.persona import PersonaCreate, PersonaOut

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


@router.get("/{persona_id}", response_model=PersonaOut)
def get_persona(
    persona_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> PersonaOut:
    _staff(current)
    return obtener(db, current.org_id, persona_id)

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user
from app.core.security import hash_password
from app.db.session import get_db
from app.models.enums import Rol, TipoDoc
from app.models.membresia import Membresia
from app.models.organizacion import Organizacion
from app.models.persona import Persona
from app.models.trabajador import Trabajador
from app.models.usuario import Usuario
from app.schemas.plataforma import OrganizacionCreate, OrganizacionListaOut, OrganizacionOut

router = APIRouter(prefix="/plataforma", tags=["plataforma"])


@router.get("/organizaciones", response_model=list[OrganizacionListaOut])
def listar_organizaciones(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[Organizacion]:
    if not current.es_plataforma:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo plataforma")
    return db.query(Organizacion).all()


@router.post("/organizaciones", response_model=OrganizacionOut, status_code=status.HTTP_201_CREATED)
def crear_organizacion(
    body: OrganizacionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> OrganizacionOut:
    if not current.es_plataforma:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo plataforma")
    if db.query(Usuario).filter(Usuario.email == body.admin_email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya existe")
    org = Organizacion(id=uuid4(), nombre=body.nombre, rif=body.rif)
    admin = Usuario(
        id=uuid4(),
        email=body.admin_email,
        password_hash=hash_password(body.admin_password),
    )
    db.add_all([org, admin])
    db.flush()
    persona = Persona(
        id=uuid4(),
        organizacion_id=org.id,
        usuario_id=admin.id,
        tipo_doc=TipoDoc.expediente,
        numero_doc=f"ADM-{admin.id.hex[:8]}",
        nombres=body.admin_nombres,
        apellidos=body.admin_apellidos,
    )
    db.add(persona)
    db.flush()
    db.add(Trabajador(id=uuid4(), persona_id=persona.id, usuario_id=admin.id))
    db.add(
        Membresia(
            id=uuid4(),
            usuario_id=admin.id,
            organizacion_id=org.id,
            rol=Rol.direccion,
        )
    )
    db.commit()
    return OrganizacionOut(id=org.id, nombre=org.nombre, rif=org.rif, admin_usuario_id=admin.id)

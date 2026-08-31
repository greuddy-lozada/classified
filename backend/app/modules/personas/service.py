from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.alumno import Alumno
from app.models.enums import TipoDoc
from app.models.persona import Persona
from app.schemas.persona import PersonaOut


def _out(persona: Persona) -> PersonaOut:
    return PersonaOut(
        id=persona.id,
        organizacion_id=persona.organizacion_id,
        usuario_id=persona.usuario_id,
        tipo_doc=persona.tipo_doc,
        numero_doc=persona.numero_doc,
        nombres=persona.nombres,
        apellidos=persona.apellidos,
        es_alumno=persona.alumno is not None,
    )


def crear_alumno(
    db: Session,
    org_id: UUID,
    tipo_doc: TipoDoc,
    numero_doc: str,
    nombres: str,
    apellidos: str,
    fecha_nacimiento=None,
    sexo=None,
    telefono=None,
    direccion=None,
) -> PersonaOut:
    exists = (
        db.query(Persona)
        .filter(
            Persona.organizacion_id == org_id,
            Persona.tipo_doc == tipo_doc,
            Persona.numero_doc == numero_doc,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Documento ya existe")
    persona = Persona(
        id=uuid4(),
        organizacion_id=org_id,
        tipo_doc=tipo_doc,
        numero_doc=numero_doc,
        nombres=nombres,
        apellidos=apellidos,
        fecha_nacimiento=fecha_nacimiento,
        sexo=sexo,
        telefono=telefono,
        direccion=direccion,
    )
    db.add(persona)
    db.flush()
    db.add(Alumno(id=uuid4(), persona_id=persona.id))
    db.commit()
    db.refresh(persona)
    return _out(persona)


def listar(db: Session, org_id: UUID) -> list[PersonaOut]:
    rows = db.query(Persona).filter(Persona.organizacion_id == org_id).all()
    return [_out(p) for p in rows]


def obtener(db: Session, org_id: UUID, persona_id: UUID) -> PersonaOut:
    persona = (
        db.query(Persona)
        .filter(Persona.id == persona_id, Persona.organizacion_id == org_id)
        .first()
    )
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrada")
    return _out(persona)

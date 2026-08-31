from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.alumno import Alumno
from app.models.asignacion import AsignacionDocente
from app.models.enums import Parentesco, Rol, TipoDoc
from app.models.inscripcion import Inscripcion
from app.models.membresia import Membresia
from app.models.persona import Persona
from app.models.trabajador import Trabajador
from app.models.usuario import Usuario
from app.models.vinculo import VinculoRepresentante
from app.schemas.persona import PersonaOut


def _out(db: Session, persona: Persona) -> PersonaOut:
    return PersonaOut(
        id=persona.id,
        organizacion_id=persona.organizacion_id,
        usuario_id=persona.usuario_id,
        tipo_doc=persona.tipo_doc,
        numero_doc=persona.numero_doc,
        nombres=persona.nombres,
        apellidos=persona.apellidos,
        es_alumno=persona.alumno is not None,
        es_trabajador=db.query(Trabajador).filter(Trabajador.persona_id == persona.id).first() is not None,
        alumno_id=persona.alumno.id if persona.alumno else None,
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
    if persona.alumno is None:
        persona.alumno = db.query(Alumno).filter(Alumno.persona_id == persona.id).one()
    return _out(db, persona)


def listar(db: Session, org_id: UUID) -> list[PersonaOut]:
    rows = db.query(Persona).filter(Persona.organizacion_id == org_id).all()
    return [_out(db, p) for p in rows]


def obtener(db: Session, org_id: UUID, persona_id: UUID) -> PersonaOut:
    persona = (
        db.query(Persona)
        .filter(Persona.id == persona_id, Persona.organizacion_id == org_id)
        .first()
    )
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrada")
    return _out(db, persona)


def _persona_del_plantel(db: Session, org_id: UUID, persona_id: UUID) -> Persona:
    persona = (
        db.query(Persona)
        .filter(Persona.id == persona_id, Persona.organizacion_id == org_id)
        .first()
    )
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrada")
    return persona


def actualizar_persona(
    db: Session,
    org_id: UUID,
    persona_id: UUID,
    tipo_doc: TipoDoc,
    numero_doc: str,
    nombres: str,
    apellidos: str,
) -> PersonaOut:
    persona = _persona_del_plantel(db, org_id, persona_id)
    dup = (
        db.query(Persona)
        .filter(
            Persona.organizacion_id == org_id,
            Persona.tipo_doc == tipo_doc,
            Persona.numero_doc == numero_doc,
            Persona.id != persona.id,
        )
        .first()
    )
    if dup:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Documento ya existe")
    persona.tipo_doc = tipo_doc
    persona.numero_doc = numero_doc.strip()
    persona.nombres = nombres.strip()
    persona.apellidos = apellidos.strip()
    db.commit()
    db.refresh(persona)
    return _out(db, persona)


def borrar_persona(db: Session, org_id: UUID, persona_id: UUID) -> None:
    persona = _persona_del_plantel(db, org_id, persona_id)
    trabajador = db.query(Trabajador).filter(Trabajador.persona_id == persona.id).first()
    if trabajador is not None:
        if db.query(AsignacionDocente).filter(AsignacionDocente.usuario_id == trabajador.usuario_id).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El docente tiene asignación")
        db.delete(trabajador)
        if persona.usuario_id:
            for m in db.query(Membresia).filter(
                Membresia.usuario_id == persona.usuario_id, Membresia.organizacion_id == org_id
            ):
                db.delete(m)
    if persona.alumno is not None:
        if db.query(Inscripcion).filter(Inscripcion.alumno_id == persona.alumno.id).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El alumno tiene inscripción")
        for v in db.query(VinculoRepresentante).filter(VinculoRepresentante.alumno_id == persona.alumno.id):
            db.delete(v)
        db.delete(persona.alumno)
    else:
        for v in db.query(VinculoRepresentante).filter(
            VinculoRepresentante.representante_persona_id == persona.id
        ):
            db.delete(v)
    db.delete(persona)
    db.commit()


def crear_representante(
    db: Session,
    org_id: UUID,
    *,
    tipo_doc: TipoDoc,
    numero_doc: str,
    nombres: str,
    apellidos: str,
    email: str,
    password: str,
    alumno_id: UUID,
    parentesco: Parentesco,
    es_principal: bool,
    fecha_nacimiento=None,
    sexo=None,
    telefono=None,
    direccion=None,
) -> PersonaOut:
    alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if alumno is None:
        raise HTTPException(status_code=404, detail="Alumno no existe")
    persona_alumno = db.get(Persona, alumno.persona_id)
    if persona_alumno is None or persona_alumno.organizacion_id != org_id:
        raise HTTPException(status_code=404, detail="Alumno no existe")
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status_code=409, detail="Email ya existe")
    user = Usuario(id=uuid4(), email=email, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    persona = Persona(
        id=uuid4(),
        organizacion_id=org_id,
        usuario_id=user.id,
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
    db.add(
        Membresia(
            id=uuid4(),
            usuario_id=user.id,
            organizacion_id=org_id,
            rol=Rol.representante,
        )
    )
    if es_principal:
        for v in db.query(VinculoRepresentante).filter(VinculoRepresentante.alumno_id == alumno_id):
            v.es_principal = False
    db.add(
        VinculoRepresentante(
            id=uuid4(),
            representante_persona_id=persona.id,
            alumno_id=alumno_id,
            parentesco=parentesco,
            es_principal=es_principal,
        )
    )
    db.commit()
    db.refresh(persona)
    return _out(db, persona)


def crear_docente(
    db: Session,
    org_id: UUID,
    *,
    tipo_doc: TipoDoc,
    numero_doc: str,
    nombres: str,
    apellidos: str,
    email: str,
    password: str,
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
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya existe")
    user = Usuario(id=uuid4(), email=email, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    persona = Persona(
        id=uuid4(),
        organizacion_id=org_id,
        usuario_id=user.id,
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
    db.add(Trabajador(id=uuid4(), persona_id=persona.id, usuario_id=user.id))
    db.add(
        Membresia(
            id=uuid4(),
            usuario_id=user.id,
            organizacion_id=org_id,
            rol=Rol.docente,
        )
    )
    db.commit()
    db.refresh(persona)
    return _out(db, persona)


def mis_pupilos(db: Session, org_id: UUID, usuario_id: UUID) -> list[PersonaOut]:
    yo = (
        db.query(Persona)
        .filter(Persona.usuario_id == usuario_id, Persona.organizacion_id == org_id)
        .first()
    )
    if yo is None:
        return []
    vinculos = (
        db.query(VinculoRepresentante)
        .filter(VinculoRepresentante.representante_persona_id == yo.id)
        .all()
    )
    out: list[PersonaOut] = []
    for v in vinculos:
        alumno = v.alumno if v.alumno is not None else db.get(Alumno, v.alumno_id)
        if alumno is None:
            continue
        persona = db.get(Persona, alumno.persona_id)
        if persona and persona.organizacion_id == org_id:
            out.append(_out(db, persona))
    return out

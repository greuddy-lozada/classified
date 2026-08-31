from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.alumno import Alumno
from app.models.anio_escolar import AnioEscolar
from app.models.enums import EstadoInscripcion, EstadoMatricula, EstadoRecaudo, TipoRecaudo
from app.models.grado import Grado
from app.models.inscripcion import Inscripcion
from app.models.persona import Persona
from app.models.recaudo import Recaudo
from app.models.seccion import Seccion
from app.models.vinculo import VinculoRepresentante
from app.schemas.inscripcion import InscripcionOut, RecaudoOut

_RECAUDOS_INICIALES = (
    TipoRecaudo.partida,
    TipoRecaudo.fotos,
    TipoRecaudo.cedula_representante,
)


def _out(row: Inscripcion, persona: Persona) -> InscripcionOut:
    recaudos = [_recaudo_out(r) for r in row.recaudos]
    return InscripcionOut(
        id=row.id,
        organizacion_id=row.organizacion_id,
        alumno_id=row.alumno_id,
        alumno_nombres=persona.nombres,
        alumno_apellidos=persona.apellidos,
        anio_escolar_id=row.anio_escolar_id,
        seccion_id=row.seccion_id,
        estado=row.estado,
        estado_matricula=row.estado_matricula,
        recaudos=recaudos,
        recaudos_pendientes=any(r.estado == EstadoRecaudo.faltante for r in row.recaudos),
    )


def _recaudo_out(r: Recaudo) -> RecaudoOut:
    return RecaudoOut(tipo=r.tipo, estado=r.estado)


def _cargar(db: Session, org_id: UUID, inscripcion_id: UUID) -> Inscripcion:
    row = (
        db.query(Inscripcion)
        .options(joinedload(Inscripcion.recaudos))
        .filter(Inscripcion.id == inscripcion_id, Inscripcion.organizacion_id == org_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción no existe")
    return row


def _persona_alumno(db: Session, alumno_id: UUID) -> Persona:
    alumno = db.get(Alumno, alumno_id)
    if alumno is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no existe")
    persona = db.get(Persona, alumno.persona_id)
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no existe")
    return persona


def _tiene_principal(db: Session, alumno_id: UUID) -> bool:
    return (
        db.query(VinculoRepresentante)
        .filter(
            VinculoRepresentante.alumno_id == alumno_id,
            VinculoRepresentante.es_principal.is_(True),
        )
        .first()
        is not None
    )


def crear(db: Session, org_id: UUID, alumno_id: UUID, anio_escolar_id: UUID) -> InscripcionOut:
    persona = _persona_alumno(db, alumno_id)
    if persona.organizacion_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no existe")
    anio = (
        db.query(AnioEscolar)
        .filter(AnioEscolar.id == anio_escolar_id, AnioEscolar.organizacion_id == org_id)
        .first()
    )
    if anio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Año no existe")
    dup = (
        db.query(Inscripcion)
        .filter(Inscripcion.alumno_id == alumno_id, Inscripcion.anio_escolar_id == anio.id)
        .first()
    )
    if dup:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya inscrito en este año")
    row = Inscripcion(
        id=uuid4(),
        organizacion_id=org_id,
        alumno_id=alumno_id,
        anio_escolar_id=anio.id,
        estado=EstadoInscripcion.preinscrito,
        estado_matricula=EstadoMatricula.pendiente,
    )
    db.add(row)
    db.flush()
    for tipo in _RECAUDOS_INICIALES:
        db.add(Recaudo(id=uuid4(), inscripcion_id=row.id, tipo=tipo, estado=EstadoRecaudo.faltante))
    db.commit()
    row = _cargar(db, org_id, row.id)
    return _out(row, persona)


def asignar_seccion(db: Session, org_id: UUID, inscripcion_id: UUID, seccion_id: UUID) -> InscripcionOut:
    row = _cargar(db, org_id, inscripcion_id)
    if row.estado == EstadoInscripcion.retirado:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alumno retirado")
    if not _tiene_principal(db, row.alumno_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sin representante principal",
        )
    seccion = (
        db.query(Seccion)
        .filter(Seccion.id == seccion_id, Seccion.organizacion_id == org_id)
        .first()
    )
    if seccion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no existe")
    grado = db.get(Grado, seccion.grado_id)
    if grado is None or grado.anio_escolar_id != row.anio_escolar_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sección de otro año")
    row.seccion_id = seccion.id
    if row.estado == EstadoInscripcion.preinscrito:
        row.estado = EstadoInscripcion.inscrito
    db.commit()
    row = _cargar(db, org_id, row.id)
    return _out(row, _persona_alumno(db, row.alumno_id))


def activar(db: Session, org_id: UUID, inscripcion_id: UUID) -> InscripcionOut:
    row = _cargar(db, org_id, inscripcion_id)
    if row.estado != EstadoInscripcion.inscrito or row.seccion_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Debe estar inscrito en sección")
    row.estado = EstadoInscripcion.activo
    db.commit()
    row = _cargar(db, org_id, row.id)
    return _out(row, _persona_alumno(db, row.alumno_id))


def retirar(db: Session, org_id: UUID, inscripcion_id: UUID) -> InscripcionOut:
    row = _cargar(db, org_id, inscripcion_id)
    row.estado = EstadoInscripcion.retirado
    db.commit()
    row = _cargar(db, org_id, row.id)
    return _out(row, _persona_alumno(db, row.alumno_id))


def marcar_recaudo(
    db: Session,
    org_id: UUID,
    inscripcion_id: UUID,
    tipo: TipoRecaudo,
    estado: EstadoRecaudo,
) -> InscripcionOut:
    row = _cargar(db, org_id, inscripcion_id)
    recaudo = next((r for r in row.recaudos if r.tipo == tipo), None)
    if recaudo is None:
        recaudo = Recaudo(id=uuid4(), inscripcion_id=row.id, tipo=tipo, estado=estado)
        db.add(recaudo)
    else:
        recaudo.estado = estado
    db.commit()
    row = _cargar(db, org_id, row.id)
    return _out(row, _persona_alumno(db, row.alumno_id))


def marcar_matricula(
    db: Session, org_id: UUID, inscripcion_id: UUID, estado_matricula: EstadoMatricula
) -> InscripcionOut:
    row = _cargar(db, org_id, inscripcion_id)
    row.estado_matricula = estado_matricula
    db.commit()
    row = _cargar(db, org_id, row.id)
    return _out(row, _persona_alumno(db, row.alumno_id))


def listar(db: Session, org_id: UUID, anio_escolar_id: UUID | None = None) -> list[InscripcionOut]:
    q = (
        db.query(Inscripcion)
        .options(joinedload(Inscripcion.recaudos))
        .filter(Inscripcion.organizacion_id == org_id)
    )
    if anio_escolar_id is not None:
        q = q.filter(Inscripcion.anio_escolar_id == anio_escolar_id)
    out: list[InscripcionOut] = []
    for row in q.all():
        out.append(_out(row, _persona_alumno(db, row.alumno_id)))
    return out


def mis_inscripciones(db: Session, org_id: UUID, usuario_id: UUID) -> list[InscripcionOut]:
    yo = (
        db.query(Persona)
        .filter(Persona.usuario_id == usuario_id, Persona.organizacion_id == org_id)
        .first()
    )
    if yo is None:
        return []
    alumno_ids = [
        v.alumno_id
        for v in db.query(VinculoRepresentante).filter(
            VinculoRepresentante.representante_persona_id == yo.id
        )
    ]
    if not alumno_ids:
        return []
    rows = (
        db.query(Inscripcion)
        .options(joinedload(Inscripcion.recaudos))
        .filter(Inscripcion.organizacion_id == org_id, Inscripcion.alumno_id.in_(alumno_ids))
        .all()
    )
    return [_out(row, _persona_alumno(db, row.alumno_id)) for row in rows]

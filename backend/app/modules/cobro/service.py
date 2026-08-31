import re
from datetime import date
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.alumno import Alumno
from app.models.anio_escolar import AnioEscolar
from app.models.cargo import Cargo
from app.models.enums import EstadoInscripcion, EstadoMatricula, TipoCargo
from app.models.inscripcion import Inscripcion
from app.models.persona import Persona
from app.models.vinculo import VinculoRepresentante
from app.schemas.cobro import CargoOut

_PERIODO = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _persona(db: Session, alumno_id: UUID) -> Persona:
    alumno = db.get(Alumno, alumno_id)
    if alumno is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no existe")
    persona = db.get(Persona, alumno.persona_id)
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no existe")
    return persona


def _out(db: Session, row: Cargo, ins: Inscripcion) -> CargoOut:
    persona = _persona(db, ins.alumno_id)
    return CargoOut(
        id=row.id,
        inscripcion_id=row.inscripcion_id,
        alumno_nombres=persona.nombres,
        alumno_apellidos=persona.apellidos,
        tipo=row.tipo,
        periodo=row.periodo,
        concepto=row.concepto,
        estado=row.estado,
        fecha_pago=row.fecha_pago,
        nota=row.nota,
    )


def _inscripciones_anio(db: Session, org_id: UUID, anio_id: UUID) -> list[Inscripcion]:
    return (
        db.query(Inscripcion)
        .filter(
            Inscripcion.organizacion_id == org_id,
            Inscripcion.anio_escolar_id == anio_id,
            Inscripcion.estado != EstadoInscripcion.retirado,
        )
        .all()
    )


def _existe(db: Session, inscripcion_id: UUID, tipo: TipoCargo, periodo: str) -> bool:
    return (
        db.query(Cargo)
        .filter(
            Cargo.inscripcion_id == inscripcion_id,
            Cargo.tipo == tipo,
            Cargo.periodo == periodo,
        )
        .first()
        is not None
    )


def generar(db: Session, org_id: UUID, anio_escolar_id: UUID, periodos: list[str]) -> list[CargoOut]:
    anio = (
        db.query(AnioEscolar)
        .filter(AnioEscolar.id == anio_escolar_id, AnioEscolar.organizacion_id == org_id)
        .first()
    )
    if anio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Año no existe")
    for periodo in periodos:
        if not _PERIODO.match(periodo):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Período inválido")
    out: list[CargoOut] = []
    for ins in _inscripciones_anio(db, org_id, anio.id):
        if not _existe(db, ins.id, TipoCargo.matricula, ""):
            row = Cargo(
                id=uuid4(),
                organizacion_id=org_id,
                inscripcion_id=ins.id,
                tipo=TipoCargo.matricula,
                periodo="",
                concepto="Matrícula",
                estado=ins.estado_matricula,
            )
            db.add(row)
            db.flush()
            out.append(_out(db, row, ins))
        for periodo in periodos:
            if _existe(db, ins.id, TipoCargo.mensualidad, periodo):
                continue
            row = Cargo(
                id=uuid4(),
                organizacion_id=org_id,
                inscripcion_id=ins.id,
                tipo=TipoCargo.mensualidad,
                periodo=periodo,
                concepto=periodo,
                estado=EstadoMatricula.pendiente,
            )
            db.add(row)
            db.flush()
            out.append(_out(db, row, ins))
    db.commit()
    return out


def listar(
    db: Session, org_id: UUID, anio_escolar_id: UUID | None, estado: EstadoMatricula | None
) -> list[CargoOut]:
    q = db.query(Cargo).filter(Cargo.organizacion_id == org_id)
    if anio_escolar_id is not None:
        ids = [
            i.id
            for i in db.query(Inscripcion).filter(
                Inscripcion.organizacion_id == org_id,
                Inscripcion.anio_escolar_id == anio_escolar_id,
            )
        ]
        q = q.filter(Cargo.inscripcion_id.in_(ids or [uuid4()]))
    if estado is not None:
        q = q.filter(Cargo.estado == estado)
    rows = q.all()
    ins_by_id = {
        i.id: i
        for i in db.query(Inscripcion).filter(Inscripcion.id.in_([r.inscripcion_id for r in rows] or [uuid4()]))
    }
    return [_out(db, row, ins_by_id[row.inscripcion_id]) for row in rows]


def marcar(
    db: Session,
    org_id: UUID,
    cargo_id: UUID,
    estado: EstadoMatricula,
    fecha_pago: date | None,
    nota: str | None,
) -> CargoOut:
    row = db.query(Cargo).filter(Cargo.id == cargo_id, Cargo.organizacion_id == org_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo no existe")
    row.estado = estado
    if estado == EstadoMatricula.pagada:
        row.fecha_pago = fecha_pago or date.today()
    else:
        row.fecha_pago = None
    row.nota = nota
    if row.tipo == TipoCargo.matricula:
        ins = db.get(Inscripcion, row.inscripcion_id)
        if ins is not None:
            ins.estado_matricula = estado
    db.commit()
    ins = db.get(Inscripcion, row.inscripcion_id)
    if ins is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción no existe")
    return _out(db, row, ins)


def mios(db: Session, org_id: UUID, usuario_id: UUID) -> list[CargoOut]:
    yo = (
        db.query(Persona)
        .filter(Persona.usuario_id == usuario_id, Persona.organizacion_id == org_id)
        .first()
    )
    if yo is None:
        return []
    alumno_ids = [
        v.alumno_id
        for v in db.query(VinculoRepresentante).filter(VinculoRepresentante.representante_persona_id == yo.id)
    ]
    if not alumno_ids:
        return []
    inscritos = (
        db.query(Inscripcion)
        .filter(Inscripcion.organizacion_id == org_id, Inscripcion.alumno_id.in_(alumno_ids))
        .all()
    )
    ins_by_id = {i.id: i for i in inscritos}
    rows = db.query(Cargo).filter(Cargo.inscripcion_id.in_(list(ins_by_id) or [uuid4()])).all()
    return [_out(db, row, ins_by_id[row.inscripcion_id]) for row in rows]

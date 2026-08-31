from datetime import date
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.models.alumno import Alumno
from app.models.asignacion import AsignacionDocente
from app.models.asistencia import Asistencia
from app.models.enums import EstadoAsistencia, EstadoInscripcion, EsquemaEvaluacion
from app.models.grado import Grado
from app.models.inscripcion import Inscripcion
from app.models.materia import Materia
from app.models.persona import Persona
from app.models.seccion import Seccion
from app.models.vinculo import VinculoRepresentante
from app.schemas.asistencia import ListaItemOut, ResumenOut

_ASISTIO = {EstadoAsistencia.presente, EstadoAsistencia.justificado, EstadoAsistencia.tardanza}


def _persona(db: Session, alumno_id: UUID) -> Persona:
    alumno = db.get(Alumno, alumno_id)
    if alumno is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no existe")
    persona = db.get(Persona, alumno.persona_id)
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no existe")
    return persona


def _seccion(db: Session, org_id: UUID, seccion_id: UUID) -> Seccion:
    row = db.query(Seccion).filter(Seccion.id == seccion_id, Seccion.organizacion_id == org_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no existe")
    return row


def _exige_materia(db: Session, seccion: Seccion) -> bool:
    grado = db.get(Grado, seccion.grado_id)
    return grado is not None and grado.esquema_evaluacion == EsquemaEvaluacion.numerico


def _puede_pasar_lista(
    db: Session, current: CurrentUser, org_id: UUID, seccion_id: UUID, materia_id: UUID | None
) -> None:
    if current.rol in {"direccion", "secretaria"}:
        return
    if current.rol != "docente":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    q = db.query(AsignacionDocente).filter(
        AsignacionDocente.organizacion_id == org_id,
        AsignacionDocente.usuario_id == current.usuario.id,
        AsignacionDocente.seccion_id == seccion_id,
    )
    if materia_id is not None:
        q = q.filter(AsignacionDocente.materia_id == materia_id)
    else:
        q = q.filter(AsignacionDocente.materia_id.is_(None))
    if q.first() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No asignado a esta lista")


def lista(
    db: Session, org_id: UUID, seccion_id: UUID, fecha: date, materia_id: UUID | None
) -> list[ListaItemOut]:
    seccion = _seccion(db, org_id, seccion_id)
    if _exige_materia(db, seccion) and materia_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Media requiere materia")
    if not _exige_materia(db, seccion) and materia_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este nivel no usa lista por materia")
    if materia_id is not None:
        materia = db.query(Materia).filter(Materia.id == materia_id, Materia.organizacion_id == org_id).first()
        if materia is None or materia.grado_id != seccion.grado_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no existe")
    inscritos = (
        db.query(Inscripcion)
        .filter(
            Inscripcion.organizacion_id == org_id,
            Inscripcion.seccion_id == seccion.id,
            Inscripcion.estado.in_((EstadoInscripcion.inscrito, EstadoInscripcion.activo)),
        )
        .all()
    )
    out: list[ListaItemOut] = []
    for ins in inscritos:
        q = db.query(Asistencia).filter(
            Asistencia.inscripcion_id == ins.id,
            Asistencia.fecha == fecha,
        )
        if materia_id is None:
            q = q.filter(Asistencia.materia_id.is_(None))
        else:
            q = q.filter(Asistencia.materia_id == materia_id)
        marca = q.first()
        persona = _persona(db, ins.alumno_id)
        out.append(
            ListaItemOut(
                inscripcion_id=ins.id,
                alumno_nombres=persona.nombres,
                alumno_apellidos=persona.apellidos,
                estado=marca.estado if marca else None,
            )
        )
    return out


def marcar(
    db: Session,
    current: CurrentUser,
    org_id: UUID,
    inscripcion_id: UUID,
    fecha: date,
    estado: EstadoAsistencia,
    materia_id: UUID | None,
) -> ListaItemOut:
    ins = (
        db.query(Inscripcion)
        .filter(Inscripcion.id == inscripcion_id, Inscripcion.organizacion_id == org_id)
        .first()
    )
    if ins is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción no existe")
    if ins.estado == EstadoInscripcion.retirado or ins.seccion_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alumno no está en lista")
    seccion = _seccion(db, org_id, ins.seccion_id)
    if _exige_materia(db, seccion) and materia_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Media requiere materia")
    if not _exige_materia(db, seccion) and materia_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este nivel no usa lista por materia")
    _puede_pasar_lista(db, current, org_id, seccion.id, materia_id)
    q = db.query(Asistencia).filter(
        Asistencia.inscripcion_id == ins.id,
        Asistencia.fecha == fecha,
    )
    if materia_id is None:
        q = q.filter(Asistencia.materia_id.is_(None))
    else:
        q = q.filter(Asistencia.materia_id == materia_id)
    row = q.first()
    if row is None:
        row = Asistencia(
            id=uuid4(),
            organizacion_id=org_id,
            inscripcion_id=ins.id,
            seccion_id=seccion.id,
            materia_id=materia_id,
            fecha=fecha,
            estado=estado,
        )
        db.add(row)
    else:
        row.estado = estado
    db.commit()
    persona = _persona(db, ins.alumno_id)
    return ListaItemOut(
        inscripcion_id=ins.id,
        alumno_nombres=persona.nombres,
        alumno_apellidos=persona.apellidos,
        estado=estado,
    )


def _resumen_de(
    db: Session,
    org_id: UUID,
    ins: Inscripcion,
    materia_id: UUID | None,
    *,
    todas: bool = False,
) -> ResumenOut:
    q = db.query(Asistencia).filter(
        Asistencia.organizacion_id == org_id,
        Asistencia.inscripcion_id == ins.id,
    )
    if not todas:
        if materia_id is None:
            q = q.filter(Asistencia.materia_id.is_(None))
        else:
            q = q.filter(Asistencia.materia_id == materia_id)
    rows = q.all()
    presentes = sum(1 for r in rows if r.estado == EstadoAsistencia.presente)
    ausentes = sum(1 for r in rows if r.estado == EstadoAsistencia.ausente)
    justificados = sum(1 for r in rows if r.estado == EstadoAsistencia.justificado)
    tardanzas = sum(1 for r in rows if r.estado == EstadoAsistencia.tardanza)
    total = len(rows)
    asistio = sum(1 for r in rows if r.estado in _ASISTIO)
    persona = _persona(db, ins.alumno_id)
    return ResumenOut(
        inscripcion_id=ins.id,
        alumno_nombres=persona.nombres,
        alumno_apellidos=persona.apellidos,
        materia_id=materia_id,
        total=total,
        presentes=presentes,
        ausentes=ausentes,
        justificados=justificados,
        tardanzas=tardanzas,
        porcentaje=round(100 * asistio / total, 1) if total else None,
    )


def resumen(db: Session, org_id: UUID, inscripcion_id: UUID, materia_id: UUID | None) -> ResumenOut:
    ins = (
        db.query(Inscripcion)
        .filter(Inscripcion.id == inscripcion_id, Inscripcion.organizacion_id == org_id)
        .first()
    )
    if ins is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción no existe")
    return _resumen_de(db, org_id, ins, materia_id)


def mis_resumenes(db: Session, org_id: UUID, usuario_id: UUID) -> list[ResumenOut]:
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
    rows = (
        db.query(Inscripcion)
        .filter(Inscripcion.organizacion_id == org_id, Inscripcion.alumno_id.in_(alumno_ids))
        .all()
    )
    return [_resumen_de(db, org_id, ins, None, todas=True) for ins in rows]

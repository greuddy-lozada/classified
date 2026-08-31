from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.models.alumno import Alumno
from app.models.anio_escolar import AnioEscolar
from app.models.asignacion import AsignacionDocente
from app.models.asistencia import Asistencia
from app.models.enums import AreaInforme, EsquemaEvaluacion, EstadoInscripcion, Juicio
from app.models.grado import Grado
from app.models.informe import InformeItem
from app.models.inscripcion import Inscripcion
from app.models.lapso import Lapso
from app.models.materia import Materia
from app.models.nota import Nota
from app.models.persona import Persona
from app.models.seccion import Seccion
from app.schemas.evaluacion import (
    AsignacionOut,
    BoletinLapsoOut,
    BoletinOut,
    InformeOut,
    MateriaOut,
    NotaOut,
)

MINIMO_APROBATORIO = 10.0


def _materia_out(m: Materia) -> MateriaOut:
    return MateriaOut(id=m.id, grado_id=m.grado_id, nombre=m.nombre)


def crear_materia(db: Session, org_id: UUID, grado_id: UUID, nombre: str) -> MateriaOut:
    grado = db.query(Grado).filter(Grado.id == grado_id, Grado.organizacion_id == org_id).first()
    if grado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grado no existe")
    if grado.esquema_evaluacion != EsquemaEvaluacion.numerico:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El grado no usa notas")
    nombre = nombre.strip()
    dup = db.query(Materia).filter(Materia.grado_id == grado.id, Materia.nombre == nombre).first()
    if dup:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Materia ya existe")
    row = Materia(id=uuid4(), organizacion_id=org_id, grado_id=grado.id, nombre=nombre)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _materia_out(row)


def listar_materias(db: Session, org_id: UUID, grado_id: UUID) -> list[MateriaOut]:
    grado = db.query(Grado).filter(Grado.id == grado_id, Grado.organizacion_id == org_id).first()
    if grado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grado no existe")
    rows = db.query(Materia).filter(Materia.grado_id == grado.id, Materia.organizacion_id == org_id).all()
    return [_materia_out(m) for m in rows]


def _materia_del_plantel(db: Session, org_id: UUID, materia_id: UUID) -> Materia:
    row = db.query(Materia).filter(Materia.id == materia_id, Materia.organizacion_id == org_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no existe")
    return row


def actualizar_materia(db: Session, org_id: UUID, materia_id: UUID, nombre: str) -> MateriaOut:
    row = _materia_del_plantel(db, org_id, materia_id)
    nombre = nombre.strip()
    dup = (
        db.query(Materia)
        .filter(Materia.grado_id == row.grado_id, Materia.nombre == nombre, Materia.id != row.id)
        .first()
    )
    if dup:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Materia ya existe")
    row.nombre = nombre
    db.commit()
    db.refresh(row)
    return _materia_out(row)


def borrar_materia(db: Session, org_id: UUID, materia_id: UUID) -> None:
    row = _materia_del_plantel(db, org_id, materia_id)
    if db.query(Nota).filter(Nota.materia_id == row.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La materia tiene notas")
    if db.query(Asistencia).filter(Asistencia.materia_id == row.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La materia tiene asistencia")
    if db.query(AsignacionDocente).filter(AsignacionDocente.materia_id == row.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La materia tiene asignación")
    db.delete(row)
    db.commit()


def asignar_docente(
    db: Session, org_id: UUID, usuario_id: UUID, seccion_id: UUID, materia_id: UUID | None
) -> AsignacionOut:
    seccion = db.query(Seccion).filter(Seccion.id == seccion_id, Seccion.organizacion_id == org_id).first()
    if seccion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no existe")
    if materia_id is not None:
        materia = db.query(Materia).filter(Materia.id == materia_id, Materia.organizacion_id == org_id).first()
        if materia is None or materia.grado_id != seccion.grado_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Materia de otro grado")
    row = AsignacionDocente(
        id=uuid4(),
        organizacion_id=org_id,
        usuario_id=usuario_id,
        seccion_id=seccion.id,
        materia_id=materia_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return AsignacionOut(
        id=row.id,
        usuario_id=row.usuario_id,
        seccion_id=row.seccion_id,
        materia_id=row.materia_id,
    )


def _inscripcion_activa(db: Session, org_id: UUID, inscripcion_id: UUID) -> Inscripcion:
    row = (
        db.query(Inscripcion)
        .filter(Inscripcion.id == inscripcion_id, Inscripcion.organizacion_id == org_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción no existe")
    if row.estado not in {EstadoInscripcion.inscrito, EstadoInscripcion.activo} or row.seccion_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alumno no inscrito")
    return row


def _lapso_abierto(db: Session, org_id: UUID, lapso_id: UUID, *, permitir_cerrado: bool) -> Lapso:
    lapso = db.get(Lapso, lapso_id)
    if lapso is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lapso no existe")
    anio = (
        db.query(AnioEscolar)
        .filter(AnioEscolar.id == lapso.anio_escolar_id, AnioEscolar.organizacion_id == org_id)
        .first()
    )
    if anio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lapso no existe")
    if lapso.cerrado and not permitir_cerrado:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lapso cerrado")
    return lapso


def _puede_cargar(
    db: Session,
    current: CurrentUser,
    org_id: UUID,
    seccion_id: UUID,
    materia_id: UUID | None,
) -> None:
    if current.rol == "direccion":
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No asignado a esta carga")


def cargar_nota(
    db: Session,
    current: CurrentUser,
    org_id: UUID,
    inscripcion_id: UUID,
    lapso_id: UUID,
    materia_id: UUID,
    valor: float,
) -> NotaOut:
    if valor < 1 or valor > 20:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nota debe estar entre 1 y 20")
    ins = _inscripcion_activa(db, org_id, inscripcion_id)
    lapso = _lapso_abierto(db, org_id, lapso_id, permitir_cerrado=False)
    if lapso.anio_escolar_id != ins.anio_escolar_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lapso de otro año")
    materia = db.query(Materia).filter(Materia.id == materia_id, Materia.organizacion_id == org_id).first()
    if materia is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no existe")
    seccion = db.get(Seccion, ins.seccion_id)
    if seccion is None or materia.grado_id != seccion.grado_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Materia de otro grado")
    grado = db.get(Grado, seccion.grado_id)
    if grado is None or grado.esquema_evaluacion != EsquemaEvaluacion.numerico:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El grado no usa notas")
    _puede_cargar(db, current, org_id, seccion.id, materia.id)
    row = (
        db.query(Nota)
        .filter(Nota.inscripcion_id == ins.id, Nota.lapso_id == lapso.id, Nota.materia_id == materia.id)
        .first()
    )
    if row is None:
        row = Nota(
            id=uuid4(),
            organizacion_id=org_id,
            inscripcion_id=ins.id,
            lapso_id=lapso.id,
            materia_id=materia.id,
            valor=valor,
        )
        db.add(row)
    else:
        row.valor = valor
    db.commit()
    return NotaOut(
        materia_id=materia.id,
        materia_nombre=materia.nombre,
        valor=valor,
        aprobada=valor >= MINIMO_APROBATORIO,
    )


def cargar_informe(
    db: Session,
    current: CurrentUser,
    org_id: UUID,
    inscripcion_id: UUID,
    lapso_id: UUID,
    area: AreaInforme,
    juicio: Juicio,
    comentario: str,
) -> InformeOut:
    ins = _inscripcion_activa(db, org_id, inscripcion_id)
    lapso = _lapso_abierto(db, org_id, lapso_id, permitir_cerrado=False)
    if lapso.anio_escolar_id != ins.anio_escolar_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lapso de otro año")
    seccion = db.get(Seccion, ins.seccion_id)
    if seccion is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alumno no inscrito")
    grado = db.get(Grado, seccion.grado_id)
    if grado is None or grado.esquema_evaluacion != EsquemaEvaluacion.informe:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El grado no usa informe")
    _puede_cargar(db, current, org_id, seccion.id, None)
    row = (
        db.query(InformeItem)
        .filter(
            InformeItem.inscripcion_id == ins.id,
            InformeItem.lapso_id == lapso.id,
            InformeItem.area == area,
        )
        .first()
    )
    if row is None:
        row = InformeItem(
            id=uuid4(),
            organizacion_id=org_id,
            inscripcion_id=ins.id,
            lapso_id=lapso.id,
            area=area,
            juicio=juicio,
            comentario=comentario,
        )
        db.add(row)
    else:
        row.juicio = juicio
        row.comentario = comentario
    db.commit()
    return InformeOut(area=area, juicio=juicio, comentario=comentario)


def _persona_inscripcion(db: Session, ins: Inscripcion) -> Persona:
    alumno = db.get(Alumno, ins.alumno_id)
    if alumno is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no existe")
    persona = db.get(Persona, alumno.persona_id)
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no existe")
    return persona


def _puede_ver_boletin(db: Session, current: CurrentUser, org_id: UUID, ins: Inscripcion) -> None:
    if current.rol in {"direccion", "secretaria", "docente"}:
        return
    persona = _persona_inscripcion(db, ins)
    if current.rol == "estudiante" and persona.usuario_id == current.usuario.id:
        return
    if current.rol == "representante":
        from app.models.vinculo import VinculoRepresentante

        yo = (
            db.query(Persona)
            .filter(Persona.usuario_id == current.usuario.id, Persona.organizacion_id == org_id)
            .first()
        )
        if yo is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
        vinculo = (
            db.query(VinculoRepresentante)
            .filter(
                VinculoRepresentante.representante_persona_id == yo.id,
                VinculoRepresentante.alumno_id == ins.alumno_id,
            )
            .first()
        )
        if vinculo:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


def boletin(db: Session, current: CurrentUser, org_id: UUID, inscripcion_id: UUID) -> BoletinOut:
    ins = (
        db.query(Inscripcion)
        .filter(Inscripcion.id == inscripcion_id, Inscripcion.organizacion_id == org_id)
        .first()
    )
    if ins is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción no existe")
    _puede_ver_boletin(db, current, org_id, ins)
    persona = _persona_inscripcion(db, ins)
    seccion = db.get(Seccion, ins.seccion_id) if ins.seccion_id else None
    grado = db.get(Grado, seccion.grado_id) if seccion else None
    esquema = grado.esquema_evaluacion.value if grado else EsquemaEvaluacion.numerico.value
    lapsos = (
        db.query(Lapso)
        .filter(Lapso.anio_escolar_id == ins.anio_escolar_id)
        .order_by(Lapso.numero)
        .all()
    )
    bloques: list[BoletinLapsoOut] = []
    promedios: list[float] = []
    for lapso in lapsos:
        notas = (
            db.query(Nota)
            .filter(Nota.inscripcion_id == ins.id, Nota.lapso_id == lapso.id)
            .all()
        )
        informes = (
            db.query(InformeItem)
            .filter(InformeItem.inscripcion_id == ins.id, InformeItem.lapso_id == lapso.id)
            .all()
        )
        nota_out: list[NotaOut] = []
        for n in notas:
            materia = db.get(Materia, n.materia_id)
            nota_out.append(
                NotaOut(
                    materia_id=n.materia_id,
                    materia_nombre=materia.nombre if materia else "",
                    valor=n.valor,
                    aprobada=n.valor >= MINIMO_APROBATORIO,
                )
            )
        promedio = round(sum(n.valor for n in notas) / len(notas), 2) if notas else None
        if promedio is not None:
            promedios.append(promedio)
        bloques.append(
            BoletinLapsoOut(
                lapso_id=lapso.id,
                lapso_nombre=lapso.nombre,
                cerrado=lapso.cerrado,
                notas=nota_out,
                informes=[
                    InformeOut(area=i.area, juicio=i.juicio, comentario=i.comentario) for i in informes
                ],
                promedio=promedio,
            )
        )
    promedio_final = round(sum(promedios) / len(promedios), 2) if len(promedios) == 3 else None
    return BoletinOut(
        inscripcion_id=ins.id,
        alumno_nombres=persona.nombres,
        alumno_apellidos=persona.apellidos,
        esquema=esquema,
        lapsos=bloques,
        promedio_final=promedio_final,
        necesita_reparacion=promedio_final is not None and promedio_final < MINIMO_APROBATORIO,
    )

from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.anio_escolar import AnioEscolar
from app.models.enums import EsquemaEvaluacion, Nivel, Turno
from app.models.grado import Grado
from app.models.lapso import Lapso
from app.models.seccion import Seccion
from app.schemas.periodo import AnioOut, GradoOut, LapsoOut, SeccionOut


def _lapso_out(l: Lapso) -> LapsoOut:
    return LapsoOut(id=l.id, numero=l.numero, nombre=l.nombre, cerrado=l.cerrado)


def _anio_out(anio: AnioEscolar) -> AnioOut:
    lapsos = sorted(anio.lapsos, key=lambda x: x.numero)
    return AnioOut(
        id=anio.id,
        organizacion_id=anio.organizacion_id,
        nombre=anio.nombre,
        activo=anio.activo,
        lapsos=[_lapso_out(l) for l in lapsos],
    )


def _seccion_out(s: Seccion) -> SeccionOut:
    return SeccionOut(id=s.id, grado_id=s.grado_id, letra=s.letra, turno=s.turno)


def _grado_out(g: Grado) -> GradoOut:
    return GradoOut(
        id=g.id,
        anio_escolar_id=g.anio_escolar_id,
        organizacion_id=g.organizacion_id,
        nivel=g.nivel,
        nombre=g.nombre,
        esquema_evaluacion=g.esquema_evaluacion,
        secciones=[_seccion_out(s) for s in g.secciones],
    )


def _esquema_default(nivel: Nivel, override: EsquemaEvaluacion | None) -> EsquemaEvaluacion:
    if override is not None:
        return override
    if nivel == Nivel.media:
        return EsquemaEvaluacion.numerico
    return EsquemaEvaluacion.informe


def crear_anio(db: Session, org_id: UUID, nombre: str) -> AnioOut:
    exists = (
        db.query(AnioEscolar)
        .filter(AnioEscolar.organizacion_id == org_id, AnioEscolar.nombre == nombre)
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Año ya existe")
    tiene_activo = (
        db.query(AnioEscolar)
        .filter(AnioEscolar.organizacion_id == org_id, AnioEscolar.activo.is_(True))
        .first()
    )
    anio = AnioEscolar(
        id=uuid4(),
        organizacion_id=org_id,
        nombre=nombre,
        activo=tiene_activo is None,
    )
    db.add(anio)
    db.flush()
    for n in (1, 2, 3):
        db.add(Lapso(id=uuid4(), anio_escolar_id=anio.id, numero=n, nombre=f"Lapso {n}"))
    db.commit()
    anio = (
        db.query(AnioEscolar)
        .options(joinedload(AnioEscolar.lapsos))
        .filter(AnioEscolar.id == anio.id)
        .one()
    )
    return _anio_out(anio)


def listar_anios(db: Session, org_id: UUID) -> list[AnioOut]:
    rows = (
        db.query(AnioEscolar)
        .options(joinedload(AnioEscolar.lapsos))
        .filter(AnioEscolar.organizacion_id == org_id)
        .all()
    )
    return [_anio_out(a) for a in rows]


def crear_grado(
    db: Session,
    org_id: UUID,
    anio_escolar_id: UUID,
    nivel: Nivel,
    nombre: str,
    esquema_evaluacion: EsquemaEvaluacion | None,
) -> GradoOut:
    anio = (
        db.query(AnioEscolar)
        .filter(AnioEscolar.id == anio_escolar_id, AnioEscolar.organizacion_id == org_id)
        .first()
    )
    if anio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Año no existe")
    dup = (
        db.query(Grado)
        .filter(Grado.anio_escolar_id == anio.id, Grado.nivel == nivel, Grado.nombre == nombre)
        .first()
    )
    if dup:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Grado ya existe")
    grado = Grado(
        id=uuid4(),
        anio_escolar_id=anio.id,
        organizacion_id=org_id,
        nivel=nivel,
        nombre=nombre,
        esquema_evaluacion=_esquema_default(nivel, esquema_evaluacion),
    )
    db.add(grado)
    db.commit()
    db.refresh(grado)
    return _grado_out(grado)


def listar_grados(db: Session, org_id: UUID, anio_escolar_id: UUID) -> list[GradoOut]:
    anio = (
        db.query(AnioEscolar)
        .filter(AnioEscolar.id == anio_escolar_id, AnioEscolar.organizacion_id == org_id)
        .first()
    )
    if anio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Año no existe")
    rows = (
        db.query(Grado)
        .options(joinedload(Grado.secciones))
        .filter(Grado.anio_escolar_id == anio.id, Grado.organizacion_id == org_id)
        .all()
    )
    return [_grado_out(g) for g in rows]


def crear_seccion(db: Session, org_id: UUID, grado_id: UUID, letra: str, turno: Turno) -> SeccionOut:
    grado = (
        db.query(Grado)
        .filter(Grado.id == grado_id, Grado.organizacion_id == org_id)
        .first()
    )
    if grado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grado no existe")
    dup = (
        db.query(Seccion)
        .filter(Seccion.grado_id == grado.id, Seccion.letra == letra, Seccion.turno == turno)
        .first()
    )
    if dup:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sección ya existe")
    seccion = Seccion(
        id=uuid4(),
        grado_id=grado.id,
        organizacion_id=org_id,
        letra=letra,
        turno=turno,
    )
    db.add(seccion)
    db.commit()
    db.refresh(seccion)
    return _seccion_out(seccion)


def _lapso_del_plantel(db: Session, org_id: UUID, lapso_id: UUID) -> Lapso:
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
    return lapso


def cerrar_lapso(db: Session, org_id: UUID, lapso_id: UUID) -> LapsoOut:
    lapso = _lapso_del_plantel(db, org_id, lapso_id)
    lapso.cerrado = True
    db.commit()
    db.refresh(lapso)
    return _lapso_out(lapso)


def reabrir_lapso(db: Session, org_id: UUID, lapso_id: UUID) -> LapsoOut:
    lapso = _lapso_del_plantel(db, org_id, lapso_id)
    lapso.cerrado = False
    db.commit()
    db.refresh(lapso)
    return _lapso_out(lapso)

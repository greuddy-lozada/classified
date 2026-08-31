import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.anio_escolar import AnioEscolar
from app.models.enums import EsquemaEvaluacion, Nivel, Turno
from app.models.grado import Grado
from app.models.lapso import Lapso
from app.models.organizacion import Organizacion
from app.models.seccion import Seccion


def test_mismo_nombre_de_anio_en_dos_colegios(db: Session) -> None:
    a = Organizacion(id=uuid.uuid4(), nombre="A", rif="J-1")
    b = Organizacion(id=uuid.uuid4(), nombre="B", rif="J-2")
    db.add_all([a, b])
    db.flush()
    db.add_all(
        [
            AnioEscolar(id=uuid.uuid4(), organizacion_id=a.id, nombre="2026-2027", activo=True),
            AnioEscolar(id=uuid.uuid4(), organizacion_id=b.id, nombre="2026-2027", activo=True),
        ]
    )
    db.commit()
    assert db.query(AnioEscolar).count() == 2


def test_nombre_de_anio_unico_en_el_plantel(db: Session, org: Organizacion) -> None:
    db.add(AnioEscolar(id=uuid.uuid4(), organizacion_id=org.id, nombre="2026-2027", activo=True))
    db.commit()
    db.add(AnioEscolar(id=uuid.uuid4(), organizacion_id=org.id, nombre="2026-2027", activo=False))
    with pytest.raises(IntegrityError):
        db.commit()


def test_tres_lapsos_unicos_por_anio(db: Session, org: Organizacion) -> None:
    anio = AnioEscolar(id=uuid.uuid4(), organizacion_id=org.id, nombre="2026-2027", activo=True)
    db.add(anio)
    db.flush()
    db.add_all(
        [
            Lapso(id=uuid.uuid4(), anio_escolar_id=anio.id, numero=1, nombre="Lapso 1"),
            Lapso(id=uuid.uuid4(), anio_escolar_id=anio.id, numero=2, nombre="Lapso 2"),
            Lapso(id=uuid.uuid4(), anio_escolar_id=anio.id, numero=3, nombre="Lapso 3"),
        ]
    )
    db.commit()
    db.add(Lapso(id=uuid.uuid4(), anio_escolar_id=anio.id, numero=1, nombre="Otro"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_seccion_unica_en_el_grado(db: Session, org: Organizacion) -> None:
    anio = AnioEscolar(id=uuid.uuid4(), organizacion_id=org.id, nombre="2026-2027", activo=True)
    db.add(anio)
    db.flush()
    grado = Grado(
        id=uuid.uuid4(),
        anio_escolar_id=anio.id,
        organizacion_id=org.id,
        nivel=Nivel.primaria,
        nombre="4°",
        esquema_evaluacion=EsquemaEvaluacion.numerico,
    )
    db.add(grado)
    db.flush()
    db.add(
        Seccion(
            id=uuid.uuid4(),
            grado_id=grado.id,
            organizacion_id=org.id,
            letra="A",
            turno=Turno.manana,
        )
    )
    db.commit()
    db.add(
        Seccion(
            id=uuid.uuid4(),
            grado_id=grado.id,
            organizacion_id=org.id,
            letra="A",
            turno=Turno.manana,
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()

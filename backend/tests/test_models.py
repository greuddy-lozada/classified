import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import TipoDoc
from app.models.organizacion import Organizacion
from app.models.persona import Persona


def test_mismo_documento_dos_colegios(db: Session) -> None:
    a = Organizacion(id=uuid.uuid4(), nombre="A", rif="J-1")
    b = Organizacion(id=uuid.uuid4(), nombre="B", rif="J-2")
    db.add_all([a, b])
    db.flush()
    db.add_all(
        [
            Persona(
                id=uuid.uuid4(),
                organizacion_id=a.id,
                tipo_doc=TipoDoc.cedula_v,
                numero_doc="12345678",
                nombres="Ana",
                apellidos="Diaz",
            ),
            Persona(
                id=uuid.uuid4(),
                organizacion_id=b.id,
                tipo_doc=TipoDoc.cedula_v,
                numero_doc="12345678",
                nombres="Ana",
                apellidos="Diaz",
            ),
        ]
    )
    db.commit()
    assert db.query(Persona).count() == 2


def test_documento_unico_en_el_mismo_colegio(db: Session, org: Organizacion) -> None:
    db.add(
        Persona(
            id=uuid.uuid4(),
            organizacion_id=org.id,
            tipo_doc=TipoDoc.cedula_v,
            numero_doc="12345678",
            nombres="Ana",
            apellidos="Diaz",
        )
    )
    db.commit()
    db.add(
        Persona(
            id=uuid.uuid4(),
            organizacion_id=org.id,
            tipo_doc=TipoDoc.cedula_v,
            numero_doc="12345678",
            nombres="Otra",
            apellidos="Persona",
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()

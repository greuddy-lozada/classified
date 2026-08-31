import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import Alumno, Membresia, Organizacion, Persona, Trabajador, Usuario, VinculoRepresentante  # noqa: F401


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionTesting = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def org(db: Session) -> Organizacion:
    from app.models.organizacion import Organizacion

    row = Organizacion(id=uuid.uuid4(), nombre="Colegio A", rif="J-111")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import (  # noqa: F401
    Alumno,
    AnioEscolar,
    Grado,
    Lapso,
    Membresia,
    Organizacion,
    Persona,
    Seccion,
    Trabajador,
    Usuario,
    VinculoRepresentante,
)
from app.models.enums import Rol
from app.models.membresia import Membresia
from app.models.usuario import Usuario


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


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def _override() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def secretaria(db: Session, org: Organizacion) -> Usuario:
    user = Usuario(
        id=uuid.uuid4(),
        email="secretaria@a.edu",
        password_hash=hash_password("clave123"),
        es_plataforma=False,
    )
    db.add(user)
    db.flush()
    db.add(
        Membresia(
            id=uuid.uuid4(),
            usuario_id=user.id,
            organizacion_id=org.id,
            rol=Rol.secretaria,
        )
    )
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def org_b(db: Session) -> Organizacion:
    row = Organizacion(id=uuid.uuid4(), nombre="Colegio B", rif="J-222")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@pytest.fixture
def secretaria_b(db: Session, org_b: Organizacion) -> Usuario:
    user = Usuario(
        id=uuid.uuid4(),
        email="secretaria@b.edu",
        password_hash=hash_password("clave123"),
        es_plataforma=False,
    )
    db.add(user)
    db.flush()
    db.add(
        Membresia(
            id=uuid.uuid4(),
            usuario_id=user.id,
            organizacion_id=org_b.id,
            rol=Rol.secretaria,
        )
    )
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def direccion(db: Session, org: Organizacion) -> Usuario:
    user = Usuario(
        id=uuid.uuid4(),
        email="dir@a.edu",
        password_hash=hash_password("clave123"),
        es_plataforma=False,
    )
    db.add(user)
    db.flush()
    db.add(
        Membresia(
            id=uuid.uuid4(),
            usuario_id=user.id,
            organizacion_id=org.id,
            rol=Rol.direccion,
        )
    )
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def plataforma(db: Session) -> Usuario:
    user = Usuario(
        id=uuid.uuid4(),
        email="ops@classified.app",
        password_hash=hash_password("clave123"),
        es_plataforma=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

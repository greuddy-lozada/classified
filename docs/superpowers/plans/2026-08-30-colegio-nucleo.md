# Núcleo Classified (auth + tenant + fichas) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un colegio puede entrar al sistema, crear fichas y no ver las de otro colegio.

**Architecture:** Monolito FastAPI + Postgres compartido. Cada fila de negocio lleva `organizacion_id`. JWT con `sub`, `org_id`, `rol`, `es_plataforma`. Quasar consume `/auth` y `/personas`.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, PyJWT, pwdlib, pytest, PostgreSQL 16, Quasar/Vue 3, Pinia.

**Spec:** `docs/superpowers/specs/2026-08-30-colegio-saas-design.md` (fase 1: sección 11 ítem 1).

**No entra en este plan:** año escolar, inscripción, notas, asistencia, cobro, PDF, signup público.

---

## File map

```
backend/
  requirements.txt
  Dockerfile
  pytest.ini
  alembic.ini
  alembic/env.py
  alembic/versions/001_nucleo.py
  app/main.py
  app/core/config.py
  app/core/security.py
  app/core/deps.py
  app/db/base.py
  app/db/session.py
  app/models/__init__.py
  app/models/enums.py
  app/models/organizacion.py
  app/models/usuario.py
  app/models/membresia.py
  app/models/persona.py
  app/models/alumno.py
  app/models/vinculo.py
  app/models/trabajador.py
  app/schemas/auth.py
  app/schemas/persona.py
  app/modules/identidad/router.py
  app/modules/identidad/service.py
  app/modules/plataforma/router.py
  app/modules/personas/router.py
  app/modules/personas/service.py
  tests/conftest.py
  tests/test_auth.py
  tests/test_tenant.py
  tests/test_personas.py
docker-compose.yml
frontend/src/boot/axios.ts
frontend/src/stores/auth.ts
frontend/src/modules/auth/composables/useAuth.ts
frontend/src/modules/auth/pages/LoginPage.vue
frontend/src/modules/auth/pages/SelectOrgPage.vue
frontend/src/router/routes.ts
frontend/src/router/index.ts
frontend/src/layouts/DashboardLayout.vue
```

Borrar al final: CRUD `/items/` en `main.py`, `routes.ts` (raíz del repo), dependencia `pymongo`.

---

### Task 1: Dependencias y Postgres en Compose

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `docker-compose.yml`
- Modify: `backend/Dockerfile`
- Create: `backend/pytest.ini`

- [ ] **Step 1: Reemplazar requirements**

`backend/requirements.txt`:

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
alembic==1.14.0
psycopg[binary]==3.2.3
pydantic==2.10.3
pydantic-settings==2.7.0
python-multipart==0.0.19
pyjwt==2.10.1
pwdlib[argon2]==0.2.1
email-validator==2.2.0
httpx==0.28.1
pytest==8.3.4
```

- [ ] **Step 2: Compose con Postgres 16**

`docker-compose.yml` — quitar el servicio `mongodb` y el volumen `mongodb_data`. El backend usa:

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+psycopg://classified:classified@postgres:5432/classified
      - JWT_SECRET=dev-only-change-me
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend/app:/app/app
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "9000:9000"
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
      - ./frontend/quasar.config.js:/app/quasar.config.js
      - ./frontend/package.json:/app/package.json
      - ./frontend/index.html:/app/index.html
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
    command: quasar dev
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: classified
      POSTGRES_PASSWORD: classified
      POSTGRES_DB: classified
    volumes:
      - postgres_data:/var/db
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U classified"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

Usar `postgres_data:/var/lib/postgresql/data` (no `/var/db`). El bloque de arriba debe quedar con:

```yaml
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

- [ ] **Step 3: Dockerfile del backend**

`backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

El código vive en paquete `app`, no suelto en `/app/main.py`. Ajustar el volumen de compose a `./backend:/app` para que Alembic y tests existan en el contenedor.

- [ ] **Step 4: pytest.ini**

`backend/pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .
```

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/Dockerfile backend/pytest.ini docker-compose.yml
git commit -m "build: swap Mongo for Postgres and pin API deps"
```

---

### Task 2: Config, sesión y app vacía

**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Test de health**

`backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Correr y ver que falla**

Run: `cd backend && pytest tests/test_health.py -v`

Expected: FAIL (no module `app.main` o no ruta `/health`)

- [ ] **Step 3: Implementar config, db y main**

`backend/app/core/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://classified:classified@localhost:5432/classified"
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_ttl_minutes: int = 30
    refresh_ttl_days: int = 14
    cors_origins: str = "http://localhost:9000"


settings = Settings()
```

`backend/app/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

`backend/app/db/session.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

`backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(title="Classified")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Correr tests**

Run: `cd backend && pytest tests/test_health.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app backend/tests/test_health.py backend/tests/conftest.py
git commit -m "feat: add FastAPI health, settings, and SQLAlchemy session"
```

Si `conftest.py` aún no existe, no lo agregues en este commit; se crea en Task 3.

---

### Task 3: Modelos del núcleo

**Files:**
- Create: `backend/app/models/enums.py`
- Create: `backend/app/models/organizacion.py`
- Create: `backend/app/models/usuario.py`
- Create: `backend/app/models/membresia.py`
- Create: `backend/app/models/persona.py`
- Create: `backend/app/models/alumno.py`
- Create: `backend/app/models/vinculo.py`
- Create: `backend/app/models/trabajador.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/tests/test_models.py`

- [ ] **Step 1: Test de unicidad de documento por plantel**

`backend/tests/conftest.py`:

```python
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
```

`backend/tests/test_models.py`:

```python
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
```

- [ ] **Step 2: Correr y ver que falla**

Run: `cd backend && pytest tests/test_models.py -v`

Expected: FAIL (import error de modelos)

- [ ] **Step 3: Implementar enums y modelos**

`backend/app/models/enums.py`:

```python
from enum import Enum


class Rol(str, Enum):
    direccion = "direccion"
    secretaria = "secretaria"
    docente = "docente"
    representante = "representante"
    estudiante = "estudiante"


class TipoDoc(str, Enum):
    cedula_v = "cedula_v"
    cedula_e = "cedula_e"
    pasaporte = "pasaporte"
    partida = "partida"
    expediente = "expediente"


class Parentesco(str, Enum):
    madre = "madre"
    padre = "padre"
    abuelo = "abuelo"
    tutor = "tutor"
```

`backend/app/models/organizacion.py`:

```python
import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organizacion(Base):
    __tablename__ = "organizacion"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(200))
    rif: Mapped[str | None] = mapped_column(String(20), nullable=True)
    activo: Mapped[bool] = mapped_column(default=True)

    membresias = relationship("Membresia", back_populates="organizacion")
```

`backend/app/models/usuario.py`:

```python
import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(default=True)
    es_plataforma: Mapped[bool] = mapped_column(default=False)

    membresias = relationship("Membresia", back_populates="usuario")
```

`backend/app/models/membresia.py`:

```python
import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Rol


class Membresia(Base):
    __tablename__ = "membresia"
    __table_args__ = (UniqueConstraint("usuario_id", "organizacion_id", "rol"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"))
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"))
    rol: Mapped[Rol] = mapped_column(Enum(Rol, native_enum=False, length=32))
    activo: Mapped[bool] = mapped_column(default=True)

    usuario = relationship("Usuario", back_populates="membresias")
    organizacion = relationship("Organizacion", back_populates="membresias")
```

`backend/app/models/persona.py`:

```python
import uuid
from datetime import date

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TipoDoc


class Persona(Base):
    __tablename__ = "persona"
    __table_args__ = (UniqueConstraint("organizacion_id", "tipo_doc", "numero_doc"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    tipo_doc: Mapped[TipoDoc] = mapped_column(Enum(TipoDoc, native_enum=False, length=32))
    numero_doc: Mapped[str] = mapped_column(String(40))
    nombres: Mapped[str] = mapped_column(String(120))
    apellidos: Mapped[str] = mapped_column(String(120))
    fecha_nacimiento: Mapped[date | None] = mapped_column(nullable=True)
    sexo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(40), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)

    alumno = relationship("Alumno", back_populates="persona", uselist=False)
```

`backend/app/models/alumno.py`:

```python
import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Alumno(Base):
    __tablename__ = "alumno"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    persona_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persona.id"), unique=True)

    persona = relationship("Persona", back_populates="alumno")
    vinculos = relationship("VinculoRepresentante", back_populates="alumno")
```

`backend/app/models/vinculo.py`:

```python
import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Parentesco


class VinculoRepresentante(Base):
    __tablename__ = "vinculo_representante"
    __table_args__ = (UniqueConstraint("representante_persona_id", "alumno_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    representante_persona_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persona.id"))
    alumno_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alumno.id"))
    parentesco: Mapped[Parentesco] = mapped_column(Enum(Parentesco, native_enum=False, length=32))
    es_principal: Mapped[bool] = mapped_column(default=False)

    alumno = relationship("Alumno", back_populates="vinculos")
    representante = relationship("Persona", foreign_keys=[representante_persona_id])
```

`backend/app/models/trabajador.py`:

```python
import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Trabajador(Base):
    __tablename__ = "trabajador"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    persona_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persona.id"), unique=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"))
```

`backend/app/models/__init__.py`:

```python
from app.models.alumno import Alumno
from app.models.membresia import Membresia
from app.models.organizacion import Organizacion
from app.models.persona import Persona
from app.models.trabajador import Trabajador
from app.models.usuario import Usuario
from app.models.vinculo import VinculoRepresentante

__all__ = [
    "Alumno",
    "Membresia",
    "Organizacion",
    "Persona",
    "Trabajador",
    "Usuario",
    "VinculoRepresentante",
]
```

SQLite no aplica `UniqueConstraint` igual que Postgres si el test de IntegrityError falla: ejecutar el mismo test contra Postgres en Task 4. Si el test SQLite no dispara IntegrityError, marcar la columna con `unique` compuesto y usar `db.flush()`; el constraint de SQLAlchemy + SQLite 3 sí falla en `UniqueConstraint` al commit.

- [ ] **Step 4: Correr tests**

Run: `cd backend && pytest tests/test_models.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models backend/tests/conftest.py backend/tests/test_models.py
git commit -m "feat: add core school identity models"
```

---

### Task 4: Alembic

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/001_nucleo.py`

- [ ] **Step 1: alembic.ini** (en `backend/`)

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

- [ ] **Step 2: env.py lee settings**

`backend/alembic/env.py`:

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base
from app.models import Alumno, Membresia, Organizacion, Persona, Trabajador, Usuario, VinculoRepresentante  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Copiar `script.py.mako` estándar de Alembic (`alembic init alembic` desde `backend/` y luego editar `env.py` es válido). Si usas `alembic init`, no reescribas a mano el ini entero: inicia y pega el `env.py` de arriba.

- [ ] **Step 3: Generar y aplicar**

Run:

```bash
cd backend && alembic revision --autogenerate -m "nucleo"
cd backend && alembic upgrade head
```

Expected: tabla `organizacion`, `usuario`, `membresia`, `persona`, `alumno`, `vinculo_representante`, `trabajador` en Postgres.

Renombra el archivo generado a `backend/alembic/versions/001_nucleo.py` solo si el hash de Alembic no se usa como nombre; si Alembic ya creó `xxxx_nucleo.py`, déjalo.

- [ ] **Step 4: Commit**

```bash
git add backend/alembic.ini backend/alembic
git commit -m "feat: add Alembic migration for identity tables"
```

---

### Task 5: Passwords y JWT

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/tests/test_security.py`

- [ ] **Step 1: Tests**

`backend/tests/test_security.py`:

```python
from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_password_roundtrip() -> None:
    hashed = hash_password("secreto")
    assert hashed != "secreto"
    assert verify_password("secreto", hashed)
    assert not verify_password("otra", hashed)


def test_access_token_claims() -> None:
    token = create_access_token(
        sub="11111111-1111-1111-1111-111111111111",
        org_id="22222222-2222-2222-2222-222222222222",
        rol="secretaria",
        es_plataforma=False,
    )
    payload = decode_token(token)
    assert payload["sub"] == "11111111-1111-1111-1111-111111111111"
    assert payload["org_id"] == "22222222-2222-2222-2222-222222222222"
    assert payload["rol"] == "secretaria"
    assert payload["es_plataforma"] is False
    assert payload["typ"] == "access"
```

- [ ] **Step 2: Correr y ver que falla**

Run: `cd backend && pytest tests/test_security.py -v`

Expected: FAIL (`app.core.security` no existe)

- [ ] **Step 3: Implementar**

`backend/app/core/security.py`:

```python
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

_hasher = PasswordHash.recommended()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _hasher.verify(plain, hashed)


def create_access_token(
    *,
    sub: str,
    org_id: str | None,
    rol: str | None,
    es_plataforma: bool,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": sub,
        "org_id": org_id,
        "rol": rol,
        "es_plataforma": es_plataforma,
        "typ": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_ttl_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, sub: str) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": sub,
        "typ": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_ttl_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def as_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    return UUID(value)
```

- [ ] **Step 4: Correr tests**

Run: `cd backend && pytest tests/test_security.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/security.py backend/tests/test_security.py
git commit -m "feat: add password hashing and JWT helpers"
```

---

### Task 6: Login, /me y elegir plantel

**Files:**
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/core/deps.py`
- Create: `backend/app/modules/identidad/service.py`
- Create: `backend/app/modules/identidad/router.py`
- Create: `backend/tests/test_auth.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Fixtures HTTP y test de login**

Añadir a `backend/tests/conftest.py`:

```python
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.main import app
from app.models.enums import Rol
from app.models.membresia import Membresia
from app.models.usuario import Usuario


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
```

`backend/tests/test_auth.py`:

```python
from fastapi.testclient import TestClient

from app.models.usuario import Usuario


def test_login_ok(client: TestClient, secretaria: Usuario) -> None:
    response = client.post("/auth/login", json={"email": "secretaria@a.edu", "password": "clave123"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert len(body["membresias"]) == 1
    assert body["membresias"][0]["rol"] == "secretaria"


def test_login_clave_mala(client: TestClient, secretaria: Usuario) -> None:
    response = client.post("/auth/login", json={"email": "secretaria@a.edu", "password": "no"})
    assert response.status_code == 401


def test_me_requiere_token(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401


def test_me_con_token(client: TestClient, secretaria: Usuario) -> None:
    login = client.post("/auth/login", json={"email": "secretaria@a.edu", "password": "clave123"}).json()
    org_id = login["membresias"][0]["organizacion_id"]
    selected = client.post(
        "/auth/seleccionar",
        json={"organizacion_id": org_id, "rol": "secretaria"},
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert selected.status_code == 200
    token = selected.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "secretaria@a.edu"
    assert me.json()["rol"] == "secretaria"
```

- [ ] **Step 2: Correr y ver que falla**

Run: `cd backend && pytest tests/test_auth.py -v`

Expected: FAIL (404 en `/auth/login`)

- [ ] **Step 3: Schemas, deps, service, router**

`backend/app/schemas/auth.py`:

```python
from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class MembresiaOut(BaseModel):
    organizacion_id: UUID
    organizacion_nombre: str
    rol: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    membresias: list[MembresiaOut]


class SeleccionarIn(BaseModel):
    organizacion_id: UUID
    rol: str


class MeOut(BaseModel):
    id: UUID
    email: str
    es_plataforma: bool
    organizacion_id: UUID | None
    rol: str | None
```

`backend/app/core/deps.py`:

```python
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.usuario import Usuario

bearer = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(
        self,
        usuario: Usuario,
        org_id: UUID | None,
        rol: str | None,
        es_plataforma: bool,
    ) -> None:
        self.usuario = usuario
        self.org_id = org_id
        self.rol = rol
        self.es_plataforma = es_plataforma


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> CurrentUser:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    try:
        payload = decode_token(creds.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc
    if payload.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = db.get(Usuario, UUID(payload["sub"]))
    if user is None or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo")
    org_raw = payload.get("org_id")
    return CurrentUser(
        usuario=user,
        org_id=UUID(org_raw) if org_raw else None,
        rol=payload.get("rol"),
        es_plataforma=bool(payload.get("es_plataforma")),
    )


def require_org(current: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if current.org_id is None or current.rol is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Selecciona un plantel")
    return current
```

`backend/app/modules/identidad/service.py`:

```python
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.models.membresia import Membresia
from app.models.usuario import Usuario
from app.schemas.auth import MembresiaOut, TokenOut


def _membresias_out(user: Usuario) -> list[MembresiaOut]:
    return [
        MembresiaOut(
            organizacion_id=m.organizacion_id,
            organizacion_nombre=m.organizacion.nombre,
            rol=m.rol.value,
        )
        for m in user.membresias
        if m.activo
    ]


def _tokens(user: Usuario, org_id: str | None, rol: str | None) -> TokenOut:
    return TokenOut(
        access_token=create_access_token(
            sub=str(user.id),
            org_id=org_id,
            rol=rol,
            es_plataforma=user.es_plataforma,
        ),
        refresh_token=create_refresh_token(sub=str(user.id)),
        membresias=_membresias_out(user),
    )


def login(db: Session, email: str, password: str) -> TokenOut:
    user = (
        db.query(Usuario)
        .options(joinedload(Usuario.membresias).joinedload(Membresia.organizacion))
        .filter(Usuario.email == email)
        .first()
    )
    if user is None or not user.activo or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    org_id = None
    rol = None
    activas = [m for m in user.membresias if m.activo]
    if len(activas) == 1:
        org_id = str(activas[0].organizacion_id)
        rol = activas[0].rol.value
    return _tokens(user, org_id, rol)


def seleccionar(db: Session, user: Usuario, organizacion_id: UUID, rol: str) -> TokenOut:
    db.refresh(user)
    user = (
        db.query(Usuario)
        .options(joinedload(Usuario.membresias).joinedload(Membresia.organizacion))
        .filter(Usuario.id == user.id)
        .one()
    )
    match = next(
        (
            m
            for m in user.membresias
            if m.activo and m.organizacion_id == organizacion_id and m.rol.value == rol
        ),
        None,
    )
    if match is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin membresía")
    return _tokens(user, str(match.organizacion_id), match.rol.value)
```

`backend/app/modules/identidad/router.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.modules.identidad.service import login, seleccionar
from app.schemas.auth import LoginIn, MeOut, SeleccionarIn, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def auth_login(body: LoginIn, db: Annotated[Session, Depends(get_db)]) -> TokenOut:
    return login(db, body.email, body.password)


@router.post("/seleccionar", response_model=TokenOut)
def auth_seleccionar(
    body: SeleccionarIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> TokenOut:
    return seleccionar(db, current.usuario, body.organizacion_id, body.rol)


@router.get("/me", response_model=MeOut)
def auth_me(current: Annotated[CurrentUser, Depends(get_current_user)]) -> MeOut:
    return MeOut(
        id=current.usuario.id,
        email=current.usuario.email,
        es_plataforma=current.es_plataforma,
        organizacion_id=current.org_id,
        rol=current.rol,
    )
```

En `backend/app/main.py` registrar el router:

```python
from app.modules.identidad.router import router as identidad_router

app.include_router(identidad_router)
```

Añadir `email-validator` si Pydantic `EmailStr` lo exige: `email-validator==2.2.0` en `requirements.txt`.

- [ ] **Step 4: Correr tests**

Run: `cd backend && pytest tests/test_auth.py -v`

Expected: PASS

Si SQLite + `joinedload` falla, en el fixture `db` ejecutar `Base.metadata.create_all` después de importar todos los modelos (ya está en conftest).

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/auth.py backend/app/core/deps.py backend/app/modules/identidad backend/app/main.py backend/tests/conftest.py backend/tests/test_auth.py backend/requirements.txt
git commit -m "feat: add login, plantel selection, and /auth/me"
```

---

### Task 7: Alta de colegio (plataforma)

**Files:**
- Create: `backend/app/modules/plataforma/router.py`
- Create: `backend/app/schemas/plataforma.py`
- Create: `backend/tests/test_plataforma.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Tests**

Añadir fixture a `conftest.py`:

```python
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
```

`backend/tests/test_plataforma.py`:

```python
from fastapi.testclient import TestClient

from app.models.usuario import Usuario


def _token(client: TestClient, email: str) -> str:
    return client.post("/auth/login", json={"email": email, "password": "clave123"}).json()["access_token"]


def test_secretaria_no_crea_colegio(client: TestClient, secretaria: Usuario) -> None:
    token = _token(client, "secretaria@a.edu")
    response = client.post(
        "/plataforma/organizaciones",
        json={
            "nombre": "Colegio B",
            "rif": "J-222",
            "admin_email": "dir@b.edu",
            "admin_password": "clave123",
            "admin_nombres": "Luis",
            "admin_apellidos": "Perez",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_plataforma_crea_colegio_y_admin(client: TestClient, plataforma: Usuario) -> None:
    token = _token(client, "ops@classified.app")
    response = client.post(
        "/plataforma/organizaciones",
        json={
            "nombre": "Colegio B",
            "rif": "J-222",
            "admin_email": "dir@b.edu",
            "admin_password": "clave123",
            "admin_nombres": "Luis",
            "admin_apellidos": "Perez",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["nombre"] == "Colegio B"
    login = client.post("/auth/login", json={"email": "dir@b.edu", "password": "clave123"})
    assert login.status_code == 200
    assert login.json()["membresias"][0]["rol"] == "direccion"
```

- [ ] **Step 2: Correr y ver que falla**

Run: `cd backend && pytest tests/test_plataforma.py -v`

Expected: FAIL (404)

- [ ] **Step 3: Implementar**

`backend/app/schemas/plataforma.py`:

```python
from uuid import UUID

from pydantic import BaseModel, EmailStr


class OrganizacionCreate(BaseModel):
    nombre: str
    rif: str | None = None
    admin_email: EmailStr
    admin_password: str
    admin_nombres: str
    admin_apellidos: str


class OrganizacionOut(BaseModel):
    id: UUID
    nombre: str
    rif: str | None
    admin_usuario_id: UUID
```

`backend/app/modules/plataforma/router.py`:

```python
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user
from app.core.security import hash_password
from app.db.session import get_db
from app.models.enums import Rol, TipoDoc
from app.models.membresia import Membresia
from app.models.organizacion import Organizacion
from app.models.persona import Persona
from app.models.trabajador import Trabajador
from app.models.usuario import Usuario
from app.schemas.plataforma import OrganizacionCreate, OrganizacionOut

router = APIRouter(prefix="/plataforma", tags=["plataforma"])


@router.post("/organizaciones", response_model=OrganizacionOut, status_code=status.HTTP_201_CREATED)
def crear_organizacion(
    body: OrganizacionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> OrganizacionOut:
    if not current.es_plataforma:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo plataforma")
    if db.query(Usuario).filter(Usuario.email == body.admin_email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya existe")
    org = Organizacion(id=uuid4(), nombre=body.nombre, rif=body.rif)
    admin = Usuario(
        id=uuid4(),
        email=body.admin_email,
        password_hash=hash_password(body.admin_password),
    )
    db.add_all([org, admin])
    db.flush()
    persona = Persona(
        id=uuid4(),
        organizacion_id=org.id,
        usuario_id=admin.id,
        tipo_doc=TipoDoc.expediente,
        numero_doc=f"ADM-{admin.id.hex[:8]}",
        nombres=body.admin_nombres,
        apellidos=body.admin_apellidos,
    )
    db.add(persona)
    db.flush()
    db.add(Trabajador(id=uuid4(), persona_id=persona.id, usuario_id=admin.id))
    db.add(
        Membresia(
            id=uuid4(),
            usuario_id=admin.id,
            organizacion_id=org.id,
            rol=Rol.direccion,
        )
    )
    db.commit()
    return OrganizacionOut(id=org.id, nombre=org.nombre, rif=org.rif, admin_usuario_id=admin.id)
```

En `main.py`:

```python
from app.modules.plataforma.router import router as plataforma_router

app.include_router(plataforma_router)
```

- [ ] **Step 4: Correr tests**

Run: `cd backend && pytest tests/test_plataforma.py tests/test_auth.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/plataforma backend/app/schemas/plataforma.py backend/app/main.py backend/tests/conftest.py backend/tests/test_plataforma.py
git commit -m "feat: allow platform to provision a school and first admin"
```

---

### Task 8: Fichas aisladas por plantel

**Files:**
- Create: `backend/app/schemas/persona.py`
- Create: `backend/app/modules/personas/service.py`
- Create: `backend/app/modules/personas/router.py`
- Create: `backend/tests/test_personas.py`
- Create: `backend/tests/test_tenant.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Tests de aislamiento y alta de alumno**

Añadir fixture `secretaria_b` en `conftest.py` (segundo colegio):

```python
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
```

`backend/tests/test_personas.py`:

```python
from fastapi.testclient import TestClient

from app.models.usuario import Usuario


def _auth(client: TestClient, email: str) -> dict[str, str]:
    login = client.post("/auth/login", json={"email": email, "password": "clave123"}).json()
    token = login["access_token"]
    if login["membresias"] and (login.get("membresias")):
        selected = client.post(
            "/auth/seleccionar",
            json={
                "organizacion_id": login["membresias"][0]["organizacion_id"],
                "rol": login["membresias"][0]["rol"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        token = selected.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_crear_alumno_sin_usuario(client: TestClient, secretaria: Usuario) -> None:
    headers = _auth(client, "secretaria@a.edu")
    response = client.post(
        "/personas/alumnos",
        json={
            "tipo_doc": "partida",
            "numero_doc": "PN-001",
            "nombres": "Mateo",
            "apellidos": "Rivas",
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["nombres"] == "Mateo"
    assert body["es_alumno"] is True
    assert body["usuario_id"] is None


def test_partida_permite_inscripcion_sin_cedula(client: TestClient, secretaria: Usuario) -> None:
    headers = _auth(client, "secretaria@a.edu")
    response = client.post(
        "/personas/alumnos",
        json={
            "tipo_doc": "partida",
            "numero_doc": "PN-002",
            "nombres": "Eva",
            "apellidos": "Rivas",
        },
        headers=headers,
    )
    assert response.status_code == 201
```

`backend/tests/test_tenant.py`:

```python
from fastapi.testclient import TestClient

from app.models.usuario import Usuario
from tests.test_personas import _auth


def test_colegio_b_no_ve_ficha_de_a(
    client: TestClient,
    secretaria: Usuario,
    secretaria_b: Usuario,
) -> None:
    created = client.post(
        "/personas/alumnos",
        json={
            "tipo_doc": "cedula_v",
            "numero_doc": "10999888",
            "nombres": "Ana",
            "apellidos": "Diaz",
        },
        headers=_auth(client, "secretaria@a.edu"),
    )
    assert created.status_code == 201
    persona_id = created.json()["id"]
    listed_b = client.get("/personas", headers=_auth(client, "secretaria@b.edu"))
    assert listed_b.status_code == 200
    assert listed_b.json() == []
    stolen = client.get(f"/personas/{persona_id}", headers=_auth(client, "secretaria@b.edu"))
    assert stolen.status_code == 404
```

- [ ] **Step 2: Correr y ver que falla**

Run: `cd backend && pytest tests/test_personas.py tests/test_tenant.py -v`

Expected: FAIL (404)

- [ ] **Step 3: Implementar personas**

`backend/app/schemas/persona.py`:

```python
from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import TipoDoc


class PersonaCreate(BaseModel):
    tipo_doc: TipoDoc
    numero_doc: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date | None = None
    sexo: str | None = None
    telefono: str | None = None
    direccion: str | None = None


class PersonaOut(BaseModel):
    id: UUID
    organizacion_id: UUID
    usuario_id: UUID | None
    tipo_doc: TipoDoc
    numero_doc: str
    nombres: str
    apellidos: str
    es_alumno: bool
```

`backend/app/modules/personas/service.py`:

```python
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.alumno import Alumno
from app.models.enums import TipoDoc
from app.models.persona import Persona
from app.schemas.persona import PersonaOut


def _out(persona: Persona) -> PersonaOut:
    return PersonaOut(
        id=persona.id,
        organizacion_id=persona.organizacion_id,
        usuario_id=persona.usuario_id,
        tipo_doc=persona.tipo_doc,
        numero_doc=persona.numero_doc,
        nombres=persona.nombres,
        apellidos=persona.apellidos,
        es_alumno=persona.alumno is not None,
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
    return _out(persona)


def listar(db: Session, org_id: UUID) -> list[PersonaOut]:
    rows = db.query(Persona).filter(Persona.organizacion_id == org_id).all()
    return [_out(p) for p in rows]


def obtener(db: Session, org_id: UUID, persona_id: UUID) -> PersonaOut:
    persona = (
        db.query(Persona)
        .filter(Persona.id == persona_id, Persona.organizacion_id == org_id)
        .first()
    )
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrada")
    return _out(persona)
```

`backend/app/modules/personas/router.py`:

```python
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_org
from app.db.session import get_db
from app.modules.personas.service import crear_alumno, listar, obtener
from app.schemas.persona import PersonaCreate, PersonaOut

router = APIRouter(prefix="/personas", tags=["personas"])

_STAFF = {"direccion", "secretaria"}


def _staff(current: CurrentUser) -> CurrentUser:
    if current.rol not in _STAFF:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return current


@router.post("/alumnos", response_model=PersonaOut, status_code=status.HTTP_201_CREATED)
def post_alumno(
    body: PersonaCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> PersonaOut:
    _staff(current)
    return crear_alumno(db, current.org_id, **body.model_dump())


@router.get("", response_model=list[PersonaOut])
def get_personas(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> list[PersonaOut]:
    _staff(current)
    return listar(db, current.org_id)


@router.get("/{persona_id}", response_model=PersonaOut)
def get_persona(
    persona_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> PersonaOut:
    _staff(current)
    return obtener(db, current.org_id, persona_id)
```

En `main.py`:

```python
from app.modules.personas.router import router as personas_router

app.include_router(personas_router)
```

`require_org` ya garantiza `org_id`. El service **siempre** filtra por ese id; nunca por querystring.

- [ ] **Step 4: Correr tests**

Run: `cd backend && pytest tests/test_personas.py tests/test_tenant.py tests/test_auth.py tests/test_plataforma.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/persona.py backend/app/modules/personas backend/app/main.py backend/tests
git commit -m "feat: add per-school student records with tenant isolation"
```

---

### Task 9: Representante + pupilos visibles

**Files:**
- Modify: `backend/app/schemas/persona.py`
- Modify: `backend/app/modules/personas/service.py`
- Modify: `backend/app/modules/personas/router.py`
- Create: `backend/tests/test_representante.py`

- [ ] **Step 1: Test**

`backend/tests/test_representante.py`:

```python
from fastapi.testclient import TestClient

from app.models.usuario import Usuario
from tests.test_personas import _auth


def test_representante_solo_ve_sus_pupilos(client: TestClient, secretaria: Usuario) -> None:
    headers = _auth(client, "secretaria@a.edu")
    alumno = client.post(
        "/personas/alumnos",
        json={"tipo_doc": "partida", "numero_doc": "PN-10", "nombres": "Mia", "apellidos": "Gil"},
        headers=headers,
    ).json()
    otro = client.post(
        "/personas/alumnos",
        json={"tipo_doc": "partida", "numero_doc": "PN-11", "nombres": "Leo", "apellidos": "Gil"},
        headers=headers,
    ).json()
    created = client.post(
        "/personas/representantes",
        json={
            "tipo_doc": "cedula_v",
            "numero_doc": "16555111",
            "nombres": "Carla",
            "apellidos": "Gil",
            "email": "carla@mail.com",
            "password": "clave123",
            "alumno_id": alumno["alumno_id"],
            "parentesco": "madre",
            "es_principal": True,
        },
        headers=headers,
    )
    assert created.status_code == 201
    pupilos = client.get("/personas/mis-pupilos", headers=_auth(client, "carla@mail.com"))
    assert pupilos.status_code == 200
    ids = {p["id"] for p in pupilos.json()}
    assert alumno["id"] in ids
    assert otro["id"] not in ids
```

Esto exige que `PersonaOut` de alumno incluya `alumno_id`.

- [ ] **Step 2: Correr y ver que falla**

Run: `cd backend && pytest tests/test_representante.py -v`

Expected: FAIL

- [ ] **Step 3: Extender schema, service y router**

En `PersonaOut` agregar `alumno_id: UUID | None = None`. En `_out`:

```python
alumno_id=persona.alumno.id if persona.alumno else None,
```

Tras `db.refresh(persona)` hay que `db.refresh` o query con relationship cargada. En `crear_alumno`, después del commit:

```python
db.refresh(persona)
if persona.alumno is None:
    persona.alumno = db.query(Alumno).filter(Alumno.persona_id == persona.id).one()
```

`RepresentanteCreate` en `schemas/persona.py`:

```python
from app.models.enums import Parentesco, TipoDoc


class RepresentanteCreate(PersonaCreate):
    email: str
    password: str
    alumno_id: UUID
    parentesco: Parentesco
    es_principal: bool = True
```

En `service.py` agregar `crear_representante` y `mis_pupilos`:

```python
from app.core.security import hash_password
from app.models.enums import Parentesco, Rol
from app.models.membresia import Membresia
from app.models.usuario import Usuario
from app.models.vinculo import VinculoRepresentante


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
    return _out(persona)


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
        persona = db.get(Persona, v.alumno.persona_id)
        if persona and persona.organizacion_id == org_id:
            out.append(_out(persona))
    return out
```

Cargar `v.alumno` (relationship). Si lazy fail, `db.get(Alumno, v.alumno_id)` y luego la persona.

Router: `POST /personas/representantes` (staff) y `GET /personas/mis-pupilos` (rol `representante`). Declarar `/mis-pupilos` y `/representantes` **antes** de `/{persona_id}`.

```python
@router.post("/representantes", response_model=PersonaOut, status_code=201)
def post_representante(body: RepresentanteCreate, db: Annotated[Session, Depends(get_db)], current: Annotated[CurrentUser, Depends(require_org)]) -> PersonaOut:
    _staff(current)
    return crear_representante(db, current.org_id, **body.model_dump())


@router.get("/mis-pupilos", response_model=list[PersonaOut])
def get_mis_pupilos(db: Annotated[Session, Depends(get_db)], current: Annotated[CurrentUser, Depends(require_org)]) -> list[PersonaOut]:
    if current.rol != "representante":
        raise HTTPException(status_code=403, detail="No autorizado")
    return mis_pupilos(db, current.org_id, current.usuario.id)
```

- [ ] **Step 4: Correr tests**

Run: `cd backend && pytest tests/test_representante.py tests/test_personas.py tests/test_tenant.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/persona.py backend/app/modules/personas backend/tests/test_representante.py
git commit -m "feat: link guardians to pupils and hide other students"
```

---

### Task 10: Seed de desarrollo

**Files:**
- Create: `backend/app/modules/identidad/seed.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Script de seed idempotente**

`backend/app/modules/identidad/seed.py`:

```python
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import Rol
from app.models.membresia import Membresia
from app.models.organizacion import Organizacion
from app.models.usuario import Usuario


def seed_if_empty(db: Session) -> None:
    if db.query(Usuario).filter(Usuario.es_plataforma.is_(True)).first():
        return
    ops = Usuario(
        email="ops@classified.app",
        password_hash=hash_password("clave123"),
        es_plataforma=True,
    )
    db.add(ops)
    db.commit()
```

No crear colegios de demo en seed: la plataforma los crea. Usuario de desarrollo: `ops@classified.app` / `clave123`.

- [ ] **Step 2: Llamar seed al arrancar solo si `SEED_DEV=1`**

En `config.py` agregar `seed_dev: bool = False`.

En `main.py`:

```python
from app.db.session import SessionLocal
from app.modules.identidad.seed import seed_if_empty

@app.on_event("startup")
def _seed() -> None:
    if not settings.seed_dev:
        return
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
```

En compose, `SEED_DEV=1` para el backend.

- [ ] **Step 3: Commit**

```bash
git add backend/app/modules/identidad/seed.py backend/app/core/config.py backend/app/main.py docker-compose.yml
git commit -m "feat: seed platform operator in development"
```

---

### Task 11: Frontend — axios y store de auth

**Files:**
- Modify: `frontend/src/boot/axios.ts`
- Create: `frontend/src/stores/auth.ts`
- Modify: `frontend/src/modules/auth/composables/useAuth.ts`

- [ ] **Step 1: Axios contra VITE_API_URL**

`frontend/src/boot/axios.ts` — reemplazar el `baseURL` hardcodeado:

```typescript
import { defineBoot } from '#q-app/wrappers';
import axios, { type AxiosInstance } from 'axios';

declare module 'vue' {
  interface ComponentCustomProperties {
    $axios: AxiosInstance;
    $api: AxiosInstance;
  }
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default defineBoot(({ app }) => {
  app.config.globalProperties.$axios = axios;
  app.config.globalProperties.$api = api;
});

export { api };
```

- [ ] **Step 2: Store Pinia**

`frontend/src/stores/auth.ts`:

```typescript
import { defineStore } from 'pinia';
import { api } from 'src/boot/axios';

export interface Membresia {
  organizacion_id: string;
  organizacion_nombre: string;
  rol: string;
}

export interface Me {
  id: string;
  email: string;
  es_plataforma: boolean;
  organizacion_id: string | null;
  rol: string | null;
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    me: null as Me | null,
    membresias: [] as Membresia[],
  }),
  getters: {
    isAuthenticated: (s) => s.me !== null,
  },
  actions: {
    persist(access: string, refresh: string) {
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
    },
    async login(email: string, password: string) {
      const { data } = await api.post('/auth/login', { email, password });
      this.persist(data.access_token, data.refresh_token);
      this.membresias = data.membresias;
      const { data: me } = await api.get('/auth/me');
      this.me = me;
      return data;
    },
    async seleccionar(organizacion_id: string, rol: string) {
      const { data } = await api.post('/auth/seleccionar', { organizacion_id, rol });
      this.persist(data.access_token, data.refresh_token);
      const { data: me } = await api.get('/auth/me');
      this.me = me;
    },
    async hydrate() {
      if (!localStorage.getItem('access_token')) return;
      const { data } = await api.get('/auth/me');
      this.me = data;
    },
    logout() {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      this.me = null;
      this.membresias = [];
    },
  },
});
```

- [ ] **Step 3: useAuth delgado**

`frontend/src/modules/auth/composables/useAuth.ts` — borrar el bloque comentado y dejar:

```typescript
import { useAuthStore } from 'src/stores/auth';

export function useAuth() {
  return useAuthStore();
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/boot/axios.ts frontend/src/stores/auth.ts frontend/src/modules/auth/composables/useAuth.ts
git commit -m "feat: wire frontend API client and auth store"
```

---

### Task 12: Login, selector de plantel y guardas

**Files:**
- Modify: `frontend/src/modules/auth/pages/LoginPage.vue`
- Create: `frontend/src/modules/auth/pages/SelectOrgPage.vue`
- Modify: `frontend/src/router/routes.ts`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/layouts/DashboardLayout.vue`
- Create: `frontend/src/modules/home/HomePage.vue` (reemplazar vacío)
- Delete: `routes.ts` (raíz del repo)

- [ ] **Step 1: Login llama al store**

En `frontend/src/modules/auth/pages/LoginPage.vue` reemplazar el bloque `<script>` (el template no se toca):

```typescript
<script lang="ts">
import { useQuasar } from 'quasar';
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import ButtonBack from 'src/modules/core/utils/ButtonBack.vue';
import { useAuthStore } from 'src/stores/auth';

export default {
  components: {
    ButtonBack,
  },
  setup() {
    const $q = useQuasar();
    const router = useRouter();
    const auth = useAuthStore();
    const email = ref('');
    const password = ref('');

    const handleSubmit = async () => {
      try {
        await auth.login(email.value, password.value);
        if (auth.me?.es_plataforma) {
          await router.push('/plataforma');
          return;
        }
        if (!auth.me?.organizacion_id || !auth.me?.rol) {
          await router.push('/seleccionar');
          return;
        }
        await router.push('/dashboard');
      } catch {
        $q.notify({ type: 'negative', message: 'Credenciales inválidas', position: 'top' });
      }
    };

    const onReset = () => {
      email.value = '';
      password.value = '';
    };

    return {
      email,
      password,
      handleSubmit,
      onReset,
    };
  },
};
</script>
```

- [ ] **Step 2: SelectOrgPage.vue**

```vue
<template>
  <q-page class="q-pa-lg">
    <q-card class="q-pa-md" style="max-width: 420px; margin: 4rem auto">
      <div class="text-h6 q-mb-md">Elige plantel</div>
      <q-list separator>
        <q-item
          v-for="m in auth.membresias"
          :key="m.organizacion_id + m.rol"
          clickable
          @click="pick(m)"
        >
          <q-item-section>
            <q-item-label>{{ m.organizacion_nombre }}</q-item-label>
            <q-item-label caption>{{ m.rol }}</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore, type Membresia } from 'src/stores/auth';

const auth = useAuthStore();
const router = useRouter();

async function pick(m: Membresia) {
  await auth.seleccionar(m.organizacion_id, m.rol);
  await router.push('/dashboard');
}
</script>
```

- [ ] **Step 3: Rutas**

`frontend/src/router/routes.ts`:

```typescript
import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('../modules/front-facing/hero/HeroPage.vue'),
  },
  {
    path: '/login',
    component: () => import('../modules/auth/pages/LoginPage.vue'),
  },
  {
    path: '/seleccionar',
    component: () => import('../modules/auth/pages/SelectOrgPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard',
    component: () => import('layouts/DashboardLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', component: () => import('../modules/home/HomePage.vue') },
    ],
  },
  {
    path: '/plataforma',
    component: () => import('layouts/DashboardLayout.vue'),
    meta: { requiresAuth: true, plataforma: true },
    children: [
      { path: '', component: () => import('../modules/home/HomePage.vue') },
    ],
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('../modules/error/NotFoundPage.vue'),
  },
];

export default routes;
```

Quitar `/signup` de las rutas de este plan (el colegio no se auto-registra). Dejar el archivo Vue si quieres; no lo enlaces.

En `frontend/src/router/index.ts`, después de crear `Router`:

```typescript
  Router.beforeEach(async (to) => {
    const token = localStorage.getItem('access_token');
    if (to.meta.requiresAuth && !token) {
      return '/login';
    }
    return true;
  });
```

- [ ] **Step 4: Dashboard mínimo**

Reemplazar el `<script>` de `DashboardLayout.vue` (el template de drawer se queda; `linksList` pasa a computarse). Añadir en el toolbar un botón Salir. Template del header: junto al título,

```vue
<q-btn flat label="Salir" @click="logout" />
```

Script:

```typescript
<script lang="ts">
import { computed, defineComponent, ref } from 'vue';
import { useRouter } from 'vue-router';
import DashLink, { type DashLinkProps } from '../modules/dashboard/DashLink.vue';
import { useAuthStore } from 'src/stores/auth';

export default defineComponent({
  name: 'DashboardLayout',
  components: { DashLink },
  setup() {
    const leftDrawerOpen = ref(false);
    const auth = useAuthStore();
    const router = useRouter();
    const linksList = computed<DashLinkProps[]>(() => {
      if (auth.me?.es_plataforma && !auth.me.rol) {
        return [{ title: 'Planteles', caption: 'Alta de colegios', icon: 'apartment', link: '/plataforma' }];
      }
      if (auth.me?.rol === 'representante') {
        return [{ title: 'Mis pupilos', caption: 'Fichas', icon: 'family_restroom', link: '/dashboard' }];
      }
      return [{ title: 'Inicio', caption: 'Plantel', icon: 'school', link: '/dashboard' }];
    });
    return {
      linksList,
      leftDrawerOpen,
      toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value;
      },
      logout() {
        auth.logout();
        void router.push('/login');
      },
    };
  },
});
</script>
```

`DashLink` hoy abre `href` externo. Para rutas internas, en este plan cambia el componente para usar `router-link` cuando `link` empieza con `/`:

```vue
<q-item
  clickable
  :tag="link.startsWith('/') ? 'router-link' : 'a'"
  :to="link.startsWith('/') ? link : undefined"
  :href="link.startsWith('/') ? undefined : link"
  :target="link.startsWith('/') ? undefined : '_blank'"
>
```

`HomePage.vue`:

```vue
<template>
  <q-page class="q-pa-lg">
    <div class="text-h5">{{ greeting }}</div>
    <div class="text-caption">{{ auth.me?.email }} · {{ auth.me?.rol ?? 'plataforma' }}</div>
  </q-page>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useAuthStore } from 'src/stores/auth';

const auth = useAuthStore();
const greeting = computed(() => {
  if (auth.me?.es_plataforma && !auth.me.rol) return 'Plataforma';
  if (auth.me?.rol === 'representante') return 'Tus pupilos';
  return 'Plantel';
});
</script>
```

- [ ] **Step 5: Borrar `routes.ts` de la raíz del repo** (duplicado muerto).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/modules/auth/pages frontend/src/router frontend/src/layouts/DashboardLayout.vue frontend/src/modules/home/HomePage.vue
git rm -f routes.ts
git commit -m "feat: add login, plantel picker, and role home"
```

---

### Task 13: Limpieza y verificación

**Files:**
- Modify: `README.md`

- [ ] **Step 1: README**

Reemplazar el README raíz para que describa el stack real:

```markdown
# Classified

SIS para colegios privados en Venezuela.

## Stack

- Quasar (Vue 3)
- FastAPI
- PostgreSQL 16

## Desarrollo

```bash
docker compose up --build
```

API: http://localhost:8000  
Cliente: http://localhost:9000

Usuario de plataforma (si `SEED_DEV=1`): `ops@classified.app` / `clave123`

Migraciones (dentro de `backend/` o el contenedor):

```bash
alembic upgrade head
```

Tests:

```bash
cd backend && pytest -v
```
```

- [ ] **Step 2: Suite completa**

Run: `cd backend && pytest -v`

Expected: PASS en `test_health`, `test_models`, `test_security`, `test_auth`, `test_plataforma`, `test_personas`, `test_tenant`, `test_representante`.

- [ ] **Step 3: Prueba manual**

1. `docker compose up --build`
2. `alembic upgrade head` y seed
3. Login plataforma → crear colegio B
4. Login dirección del colegio B
5. Crear alumno con partida
6. Crear representante
7. Login representante → solo ese pupilo
8. Repetir en otro colegio: la lista de personas está vacía

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: describe Postgres stack and local login"
```

---

## Planes siguientes (no este documento)

Cada uno produce software usable y tiene su propio plan:

2. Año escolar — período, 3 lapsos, nivel, grado, sección, turno
3. Inscripción — cupo, recaudos, representante obligatorio
4. Evaluación — inicial / primaria / media, cierre de lapso, boletín
5. Asistencia — por sección (inicial/primaria) y por materia (media)
6. Cobro mínimo — matrícula y mensualidad como estado
7. PDF — boletín e informe

---

## Cobertura del spec (fase 1)

| Spec | Tarea |
|---|---|
| Una Postgres, `organizacion_id` | 1, 3, 8 |
| JWT + elegir plantel | 5, 6, 12 |
| Plataforma crea colegio y admin | 7, 10 |
| Ficha por colegio, documento VE | 3, 8 |
| Alumno sin usuario (partida) | 8 |
| Representante ve solo pupilos | 9, 12 |
| Tres portales (entrada) | 12 |
| Año escolar, notas, asistencia, cobro | Fuera — planes 2–6 |

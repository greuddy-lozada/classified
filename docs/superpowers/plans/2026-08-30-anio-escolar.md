# Año escolar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dirección configura el año escolar, sus 3 lapsos, grados y secciones; otro colegio no los ve.

**Architecture:** Módulo `periodo` en el FastAPI actual. Un `anio_escolar` por plantel (nombre tipo `2026-2027`) crea exactamente 3 lapsos. Grados cuelgan del año + nivel; secciones cuelgan del grado + letra + turno. Toda fila lleva `organizacion_id` o se alcanza por FK al año del plantel.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, pytest, Quasar/Vue 3. Tests con `/tmp/classified-venv/bin/pytest` (Python 3.11).

**Spec:** `docs/superpowers/specs/2026-08-30-colegio-saas-design.md` sección 3.

**No entra:** inscripción del alumno a la sección, materias, notas, cierre de lapso, asistencia, cobro.

**Patrones a copiar:** `backend/app/modules/personas/`, `_auth` en `backend/tests/test_personas.py`, fixtures en `backend/tests/conftest.py`. Staff de escritura: solo `direccion`. Secretaría **lista**. Representante y plataforma: 403 en escritura.

---

## File map

```
backend/app/models/enums.py          (añadir Nivel, Turno, EsquemaEvaluacion)
backend/app/models/anio_escolar.py
backend/app/models/lapso.py
backend/app/models/grado.py
backend/app/models/seccion.py
backend/app/models/__init__.py
backend/alembic/versions/002_anio_escolar.py
backend/app/schemas/periodo.py
backend/app/modules/periodo/service.py
backend/app/modules/periodo/router.py
backend/app/modules/periodo/__init__.py
backend/app/main.py
backend/tests/conftest.py
backend/tests/test_periodo_models.py
backend/tests/test_periodo.py
frontend/src/modules/periodo/PeriodoPage.vue
frontend/src/router/routes.ts
frontend/src/layouts/DashboardLayout.vue
```

---

### Task 1: Enums y modelos

**Files:**
- Modify: `backend/app/models/enums.py`
- Create: `backend/app/models/anio_escolar.py`
- Create: `backend/app/models/lapso.py`
- Create: `backend/app/models/grado.py`
- Create: `backend/app/models/seccion.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/tests/test_periodo_models.py`
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Test de unicidad**

Añadir imports de los modelos nuevos al fixture `db` en `backend/tests/conftest.py` (la línea `# noqa: F401`) para que `Base.metadata.create_all` los cree:

```python
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
```

`backend/tests/test_periodo_models.py`:

```python
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
```

- [ ] **Step 2: Correr y ver que falla**

Run: `cd /home/davidlozada/Documents/Dev/classified/backend && /tmp/classified-venv/bin/pytest tests/test_periodo_models.py -v`

Expected: FAIL (import error de `AnioEscolar` / `Nivel`)

- [ ] **Step 3: Enums y modelos**

Añadir al final de `backend/app/models/enums.py`:

```python
class Nivel(str, Enum):
    inicial = "inicial"
    primaria = "primaria"
    media = "media"


class Turno(str, Enum):
    manana = "manana"
    tarde = "tarde"


class EsquemaEvaluacion(str, Enum):
    informe = "informe"
    numerico = "numerico"
```

`backend/app/models/anio_escolar.py`:

```python
import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnioEscolar(Base):
    __tablename__ = "anio_escolar"
    __table_args__ = (UniqueConstraint("organizacion_id", "nombre"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(32))
    activo: Mapped[bool] = mapped_column(default=True)

    lapsos = relationship("Lapso", back_populates="anio_escolar", order_by="Lapso.numero")
    grados = relationship("Grado", back_populates="anio_escolar")
```

`backend/app/models/lapso.py`:

```python
import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Lapso(Base):
    __tablename__ = "lapso"
    __table_args__ = (UniqueConstraint("anio_escolar_id", "numero"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    anio_escolar_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("anio_escolar.id"), index=True)
    numero: Mapped[int] = mapped_column(Integer)
    nombre: Mapped[str] = mapped_column(String(40))
    cerrado: Mapped[bool] = mapped_column(default=False)

    anio_escolar = relationship("AnioEscolar", back_populates="lapsos")
```

`cerrado` nace en `False`. Cerrar el lapso (bloquear notas) es el plan de evaluación; el campo evita otra migración.

`backend/app/models/grado.py`:

```python
import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EsquemaEvaluacion, Nivel


class Grado(Base):
    __tablename__ = "grado"
    __table_args__ = (UniqueConstraint("anio_escolar_id", "nivel", "nombre"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    anio_escolar_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("anio_escolar.id"), index=True)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    nivel: Mapped[Nivel] = mapped_column(Enum(Nivel, native_enum=False, length=32))
    nombre: Mapped[str] = mapped_column(String(40))
    esquema_evaluacion: Mapped[EsquemaEvaluacion] = mapped_column(
        Enum(EsquemaEvaluacion, native_enum=False, length=32)
    )

    anio_escolar = relationship("AnioEscolar", back_populates="grados")
    secciones = relationship("Seccion", back_populates="grado")
```

`backend/app/models/seccion.py`:

```python
import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Turno


class Seccion(Base):
    __tablename__ = "seccion"
    __table_args__ = (UniqueConstraint("grado_id", "letra", "turno"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    grado_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grado.id"), index=True)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    letra: Mapped[str] = mapped_column(String(8))
    turno: Mapped[Turno] = mapped_column(Enum(Turno, native_enum=False, length=16))

    grado = relationship("Grado", back_populates="secciones")
```

Reemplazar `backend/app/models/__init__.py`:

```python
from app.models.alumno import Alumno
from app.models.anio_escolar import AnioEscolar
from app.models.grado import Grado
from app.models.lapso import Lapso
from app.models.membresia import Membresia
from app.models.organizacion import Organizacion
from app.models.persona import Persona
from app.models.seccion import Seccion
from app.models.trabajador import Trabajador
from app.models.usuario import Usuario
from app.models.vinculo import VinculoRepresentante

__all__ = [
    "Alumno",
    "AnioEscolar",
    "Grado",
    "Lapso",
    "Membresia",
    "Organizacion",
    "Persona",
    "Seccion",
    "Trabajador",
    "Usuario",
    "VinculoRepresentante",
]
```

- [ ] **Step 4: Correr tests**

Run: `cd /home/davidlozada/Documents/Dev/classified/backend && /tmp/classified-venv/bin/pytest tests/test_periodo_models.py tests/test_models.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models backend/tests/test_periodo_models.py backend/tests/conftest.py
git commit -m "feat: add school-year, lapse, grade, and section models"
```

---

### Task 2: Migración Alembic

**Files:**
- Create: `backend/alembic/versions/` (nuevo revision file)

- [ ] **Step 1: Generar revisión**

Run from `backend/` with Python 3.11 (same as Task 4 del núcleo). `down_revision` debe ser `74d31bc22cce`.

```bash
cd /home/davidlozada/Documents/Dev/classified/backend
# si el host es 3.14, usa el venv 3.11 o un contenedor python:3.11-slim
/tmp/classified-venv/bin/alembic revision --autogenerate -m "anio_escolar"
```

Si autogenerate no puede conectar a Postgres, escribe a mano `backend/alembic/versions/002_anio_escolar.py` (el nombre puede llevar hash de Alembic). Contenido mínimo:

```python
"""anio_escolar

Revision ID: 002anioesc
Revises: 74d31bc22cce
Create Date: 2026-08-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002anioesc"
down_revision: Union[str, None] = "74d31bc22cce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "anio_escolar",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organizacion_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=32), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizacion.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organizacion_id", "nombre"),
    )
    op.create_index(op.f("ix_anio_escolar_organizacion_id"), "anio_escolar", ["organizacion_id"], unique=False)
    op.create_table(
        "lapso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("anio_escolar_id", sa.Uuid(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=40), nullable=False),
        sa.Column("cerrado", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["anio_escolar_id"], ["anio_escolar.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("anio_escolar_id", "numero"),
    )
    op.create_index(op.f("ix_lapso_anio_escolar_id"), "lapso", ["anio_escolar_id"], unique=False)
    op.create_table(
        "grado",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("anio_escolar_id", sa.Uuid(), nullable=False),
        sa.Column("organizacion_id", sa.Uuid(), nullable=False),
        sa.Column("nivel", sa.Enum("inicial", "primaria", "media", name="nivel", native_enum=False, length=32), nullable=False),
        sa.Column("nombre", sa.String(length=40), nullable=False),
        sa.Column(
            "esquema_evaluacion",
            sa.Enum("informe", "numerico", name="esquemaevaluacion", native_enum=False, length=32),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["anio_escolar_id"], ["anio_escolar.id"]),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizacion.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("anio_escolar_id", "nivel", "nombre"),
    )
    op.create_index(op.f("ix_grado_anio_escolar_id"), "grado", ["anio_escolar_id"], unique=False)
    op.create_index(op.f("ix_grado_organizacion_id"), "grado", ["organizacion_id"], unique=False)
    op.create_table(
        "seccion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("grado_id", sa.Uuid(), nullable=False),
        sa.Column("organizacion_id", sa.Uuid(), nullable=False),
        sa.Column("letra", sa.String(length=8), nullable=False),
        sa.Column("turno", sa.Enum("manana", "tarde", name="turno", native_enum=False, length=16), nullable=False),
        sa.ForeignKeyConstraint(["grado_id"], ["grado.id"]),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizacion.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("grado_id", "letra", "turno"),
    )
    op.create_index(op.f("ix_seccion_grado_id"), "seccion", ["grado_id"], unique=False)
    op.create_index(op.f("ix_seccion_organizacion_id"), "seccion", ["organizacion_id"], unique=False)


def downgrade() -> None:
    op.drop_table("seccion")
    op.drop_table("grado")
    op.drop_table("lapso")
    op.drop_table("anio_escolar")
```

Si `alembic revision --autogenerate` ya creó un archivo con hash, **no** crees `002_anio_escolar.py` además. Usa el generado y verifica que `down_revision == "74d31bc22cce"` y que existan las 4 tablas.

- [ ] **Step 2: Commit**

```bash
git add backend/alembic/versions
git commit -m "feat: migrate school-year calendar tables"
```

No hace falta `alembic upgrade head` para que los tests SQLite pasen. Si Postgres del compose está arriba, aplícala.

---

### Task 3: API de año y lapsos

**Files:**
- Create: `backend/app/schemas/periodo.py`
- Create: `backend/app/modules/periodo/__init__.py` (vacío)
- Create: `backend/app/modules/periodo/service.py`
- Create: `backend/app/modules/periodo/router.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_periodo.py`
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Fixture dirección y tests**

Añadir a `backend/tests/conftest.py`:

```python
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
```

`backend/tests/test_periodo.py`:

```python
from fastapi.testclient import TestClient

from app.models.usuario import Usuario
from tests.test_personas import _auth


def test_crear_anio_trae_tres_lapsos(client: TestClient, direccion: Usuario) -> None:
    headers = _auth(client, "dir@a.edu")
    response = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["nombre"] == "2026-2027"
    assert body["activo"] is True
    assert [l["numero"] for l in body["lapsos"]] == [1, 2, 3]
    assert [l["cerrado"] for l in body["lapsos"]] == [False, False, False]


def test_secretaria_no_crea_anio(client: TestClient, secretaria: Usuario) -> None:
    headers = _auth(client, "secretaria@a.edu")
    response = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers)
    assert response.status_code == 403


def test_colegio_b_no_ve_anio_de_a(
    client: TestClient, direccion: Usuario, secretaria_b: Usuario
) -> None:
    created = client.post(
        "/periodo/anios",
        json={"nombre": "2026-2027"},
        headers=_auth(client, "dir@a.edu"),
    )
    assert created.status_code == 201
    listed = client.get("/periodo/anios", headers=_auth(client, "secretaria@b.edu"))
    assert listed.status_code == 200
    assert listed.json() == []
```

- [ ] **Step 2: Correr y ver que falla**

Run: `cd /home/davidlozada/Documents/Dev/classified/backend && /tmp/classified-venv/bin/pytest tests/test_periodo.py -v`

Expected: FAIL (404 en `/periodo/anios`)

- [ ] **Step 3: Schemas, service, router**

`backend/app/schemas/periodo.py`:

```python
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import EsquemaEvaluacion, Nivel, Turno


class AnioCreate(BaseModel):
    nombre: str = Field(min_length=4, max_length=32)


class LapsoOut(BaseModel):
    id: UUID
    numero: int
    nombre: str
    cerrado: bool


class AnioOut(BaseModel):
    id: UUID
    organizacion_id: UUID
    nombre: str
    activo: bool
    lapsos: list[LapsoOut]


class GradoCreate(BaseModel):
    anio_escolar_id: UUID
    nivel: Nivel
    nombre: str = Field(min_length=1, max_length=40)
    esquema_evaluacion: EsquemaEvaluacion | None = None


class SeccionOut(BaseModel):
    id: UUID
    grado_id: UUID
    letra: str
    turno: Turno


class GradoOut(BaseModel):
    id: UUID
    anio_escolar_id: UUID
    organizacion_id: UUID
    nivel: Nivel
    nombre: str
    esquema_evaluacion: EsquemaEvaluacion
    secciones: list[SeccionOut] = []


class SeccionCreate(BaseModel):
    grado_id: UUID
    letra: str = Field(min_length=1, max_length=8)
    turno: Turno
```

`backend/app/modules/periodo/service.py`:

```python
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
```

`backend/app/modules/periodo/router.py`:

```python
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_org
from app.db.session import get_db
from app.modules.periodo.service import crear_anio, crear_grado, crear_seccion, listar_anios, listar_grados
from app.schemas.periodo import AnioCreate, AnioOut, GradoCreate, GradoOut, SeccionCreate, SeccionOut

router = APIRouter(prefix="/periodo", tags=["periodo"])

_WRITE = {"direccion"}
_READ = {"direccion", "secretaria"}


def _org_id(current: CurrentUser) -> UUID:
    if current.org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Selecciona un plantel")
    return current.org_id


def _require_write(current: CurrentUser) -> None:
    if current.rol not in _WRITE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


def _require_read(current: CurrentUser) -> None:
    if current.rol not in _READ:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


@router.post("/anios", response_model=AnioOut, status_code=status.HTTP_201_CREATED)
def post_anio(
    body: AnioCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> AnioOut:
    _require_write(current)
    return crear_anio(db, _org_id(current), body.nombre)


@router.get("/anios", response_model=list[AnioOut])
def get_anios(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> list[AnioOut]:
    _require_read(current)
    return listar_anios(db, _org_id(current))


@router.post("/grados", response_model=GradoOut, status_code=status.HTTP_201_CREATED)
def post_grado(
    body: GradoCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> GradoOut:
    _require_write(current)
    return crear_grado(
        db,
        _org_id(current),
        body.anio_escolar_id,
        body.nivel,
        body.nombre,
        body.esquema_evaluacion,
    )


@router.get("/grados", response_model=list[GradoOut])
def get_grados(
    anio_escolar_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> list[GradoOut]:
    _require_read(current)
    return listar_grados(db, _org_id(current), anio_escolar_id)


@router.post("/secciones", response_model=SeccionOut, status_code=status.HTTP_201_CREATED)
def post_seccion(
    body: SeccionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_org)],
) -> SeccionOut:
    _require_write(current)
    return crear_seccion(db, _org_id(current), body.grado_id, body.letra, body.turno)
```

En `backend/app/main.py` registrar:

```python
from app.modules.periodo.router import router as periodo_router

app.include_router(periodo_router)
```

- [ ] **Step 4: Correr tests**

Run: `cd /home/davidlozada/Documents/Dev/classified/backend && /tmp/classified-venv/bin/pytest tests/test_periodo.py tests/test_auth.py tests/test_personas.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/periodo.py backend/app/modules/periodo backend/app/main.py backend/tests/conftest.py backend/tests/test_periodo.py
git commit -m "feat: add school-year API with three lapses and tenant isolation"
```

---

### Task 4: Grados y secciones (tests de API)

**Files:**
- Modify: `backend/tests/test_periodo.py`

Los endpoints ya están en Task 3. Esta tarea solo cubre el comportamiento de grado/sección.

- [ ] **Step 1: Tests**

Añadir al final de `backend/tests/test_periodo.py`:

```python
def test_grado_media_usa_esquema_numerico(client: TestClient, direccion: Usuario) -> None:
    headers = _auth(client, "dir@a.edu")
    anio = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers).json()
    grado = client.post(
        "/periodo/grados",
        json={"anio_escolar_id": anio["id"], "nivel": "media", "nombre": "3er año"},
        headers=headers,
    )
    assert grado.status_code == 201
    assert grado.json()["esquema_evaluacion"] == "numerico"
    assert grado.json()["nivel"] == "media"


def test_grado_inicial_usa_informe(client: TestClient, direccion: Usuario) -> None:
    headers = _auth(client, "dir@a.edu")
    anio = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers).json()
    grado = client.post(
        "/periodo/grados",
        json={"anio_escolar_id": anio["id"], "nivel": "inicial", "nombre": "3er nivel"},
        headers=headers,
    )
    assert grado.status_code == 201
    assert grado.json()["esquema_evaluacion"] == "informe"


def test_primaria_puede_elegir_esquema(client: TestClient, direccion: Usuario) -> None:
    headers = _auth(client, "dir@a.edu")
    anio = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers).json()
    grado = client.post(
        "/periodo/grados",
        json={
            "anio_escolar_id": anio["id"],
            "nivel": "primaria",
            "nombre": "6°",
            "esquema_evaluacion": "numerico",
        },
        headers=headers,
    )
    assert grado.status_code == 201
    assert grado.json()["esquema_evaluacion"] == "numerico"


def test_crear_seccion_y_listar(client: TestClient, direccion: Usuario) -> None:
    headers = _auth(client, "dir@a.edu")
    anio = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers).json()
    grado = client.post(
        "/periodo/grados",
        json={"anio_escolar_id": anio["id"], "nivel": "primaria", "nombre": "4°"},
        headers=headers,
    ).json()
    seccion = client.post(
        "/periodo/secciones",
        json={"grado_id": grado["id"], "letra": "A", "turno": "manana"},
        headers=headers,
    )
    assert seccion.status_code == 201
    listed = client.get(f"/periodo/grados?anio_escolar_id={anio['id']}", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["secciones"][0]["letra"] == "A"
    assert listed.json()[0]["secciones"][0]["turno"] == "manana"


def test_no_usa_grado_de_otro_colegio(
    client: TestClient, direccion: Usuario, secretaria_b: Usuario
) -> None:
    grado = None
    headers_a = _auth(client, "dir@a.edu")
    anio = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers_a).json()
    grado = client.post(
        "/periodo/grados",
        json={"anio_escolar_id": anio["id"], "nivel": "media", "nombre": "1er año"},
        headers=headers_a,
    ).json()
    stolen = client.get(
        f"/periodo/grados?anio_escolar_id={anio['id']}",
        headers=_auth(client, "secretaria@b.edu"),
    )
    assert stolen.status_code == 404
```

- [ ] **Step 2: Correr tests**

Run: `cd /home/davidlozada/Documents/Dev/classified/backend && /tmp/classified-venv/bin/pytest tests/test_periodo.py -v`

Expected: PASS (la implementación ya está en Task 3). Si `listar_grados` de un año ajeno no da 404, el filtro `organizacion_id` del año ya lo cubre — no cambies el contrato: 404 si el año no es del plantel.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_periodo.py
git commit -m "test: cover grades, sections, and evaluation scheme defaults"
```

---

### Task 5: Pantalla de período

**Files:**
- Create: `frontend/src/modules/periodo/PeriodoPage.vue`
- Modify: `frontend/src/router/routes.ts`
- Modify: `frontend/src/layouts/DashboardLayout.vue`

- [ ] **Step 1: Página**

`frontend/src/modules/periodo/PeriodoPage.vue`:

```vue
<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Año escolar</div>

    <q-form class="row q-col-gutter-sm q-mb-lg" @submit.prevent="crearAnio">
      <div class="col-8">
        <q-input v-model="nuevoAnio" outlined dense label="Nombre (ej. 2026-2027)" />
      </div>
      <div class="col-4">
        <q-btn type="submit" color="primary" label="Crear año" class="full-width" />
      </div>
    </q-form>

    <div v-for="anio in anios" :key="anio.id" class="q-mb-lg">
      <div class="text-subtitle1">{{ anio.nombre }} <q-badge v-if="anio.activo" color="positive" label="activo" /></div>
      <div class="text-caption q-mb-sm">
        Lapsos: {{ anio.lapsos.map((l) => l.nombre).join(', ') }}
      </div>

      <q-form class="row q-col-gutter-sm q-mb-sm" @submit.prevent="crearGrado(anio.id)">
        <div class="col-3">
          <q-select v-model="formGrado.nivel" outlined dense :options="niveles" label="Nivel" />
        </div>
        <div class="col-4">
          <q-input v-model="formGrado.nombre" outlined dense label="Grado (4°, 3er año)" />
        </div>
        <div class="col-3">
          <q-select
            v-model="formGrado.esquema"
            outlined
            dense
            :options="esquemas"
            label="Esquema"
            clearable
          />
        </div>
        <div class="col-2">
          <q-btn type="submit" color="secondary" label="Grado" class="full-width" />
        </div>
      </q-form>

      <q-list bordered separator>
        <q-item v-for="g in gradosPorAnio[anio.id] ?? []" :key="g.id">
          <q-item-section>
            <q-item-label>{{ g.nivel }} · {{ g.nombre }}</q-item-label>
            <q-item-label caption>
              {{ g.esquema_evaluacion }} ·
              {{ g.secciones.map((s) => s.letra + ' ' + s.turno).join(', ') || 'sin sección' }}
            </q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-btn dense flat label="+ A mañana" @click="crearSeccion(g.id, 'A', 'manana')" />
          </q-item-section>
        </q-item>
      </q-list>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';

interface Lapso {
  id: string;
  numero: number;
  nombre: string;
  cerrado: boolean;
}
interface Seccion {
  id: string;
  letra: string;
  turno: string;
}
interface Grado {
  id: string;
  nivel: string;
  nombre: string;
  esquema_evaluacion: string;
  secciones: Seccion[];
}
interface Anio {
  id: string;
  nombre: string;
  activo: boolean;
  lapsos: Lapso[];
}

const $q = useQuasar();
const anios = ref<Anio[]>([]);
const gradosPorAnio = ref<Record<string, Grado[]>>({});
const nuevoAnio = ref('2026-2027');
const niveles = ['inicial', 'primaria', 'media'];
const esquemas = ['informe', 'numerico'];
const formGrado = reactive({ nivel: 'primaria', nombre: '', esquema: null as string | null });

async function cargar() {
  const { data } = await api.get<Anio[]>('/periodo/anios');
  anios.value = data;
  for (const anio of data) {
    const res = await api.get<Grado[]>('/periodo/grados', { params: { anio_escolar_id: anio.id } });
    gradosPorAnio.value[anio.id] = res.data;
  }
}

async function crearAnio() {
  try {
    await api.post('/periodo/anios', { nombre: nuevoAnio.value });
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo crear el año' });
  }
}

async function crearGrado(anioId: string) {
  try {
    await api.post('/periodo/grados', {
      anio_escolar_id: anioId,
      nivel: formGrado.nivel,
      nombre: formGrado.nombre,
      esquema_evaluacion: formGrado.esquema,
    });
    formGrado.nombre = '';
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo crear el grado' });
  }
}

async function crearSeccion(gradoId: string, letra: string, turno: string) {
  try {
    await api.post('/periodo/secciones', { grado_id: gradoId, letra, turno });
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo crear la sección' });
  }
}

onMounted(cargar);
</script>
```

`Pydantic` trata `esquema_evaluacion: null` como omitido si el front manda `null`. Si FastAPI rechaza `null`, en `crearGrado` no envíes la clave cuando `formGrado.esquema` es `null`:

```typescript
    const payload: Record<string, unknown> = {
      anio_escolar_id: anioId,
      nivel: formGrado.nivel,
      nombre: formGrado.nombre,
    };
    if (formGrado.esquema) payload.esquema_evaluacion = formGrado.esquema;
    await api.post('/periodo/grados', payload);
```

Usa ese payload (no mandes `null`).

- [ ] **Step 2: Ruta y menú**

En `frontend/src/router/routes.ts`, dentro de `children` de `/dashboard`, añadir:

```typescript
      { path: 'periodo', component: () => import('../modules/periodo/PeriodoPage.vue') },
```

En `frontend/src/layouts/DashboardLayout.vue`, el `linksList` computed: para `secretaria` y `direccion` incluir el link de período. Reemplazar el `return` default:

```typescript
      return [
        { title: 'Inicio', caption: 'Plantel', icon: 'school', link: '/dashboard' },
        { title: 'Año escolar', caption: 'Lapsos, grados, secciones', icon: 'event', link: '/dashboard/periodo' },
      ];
```

El representante no ve ese ítem (sigue el `if` de representante). Plataforma no entra a `/dashboard/periodo`.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/modules/periodo/PeriodoPage.vue frontend/src/router/routes.ts frontend/src/layouts/DashboardLayout.vue
git commit -m "feat: add school-year setup screen for plantel staff"
```

---

### Task 6: Suite

- [ ] **Step 1: Correr todo**

Run: `cd /home/davidlozada/Documents/Dev/classified/backend && /tmp/classified-venv/bin/pytest -v`

Expected: PASS, incluyendo los tests viejos (health, auth, personas, tenant, representante, plataforma) y `test_periodo` + `test_periodo_models`.

- [ ] **Step 2: Commit solo si algo se corrigió.** Si la suite ya pasaba, no hay commit.

---

## Cobertura del spec (sección 3)

| Spec | Tarea |
|---|---|
| Año escolar, no semestre | 1, 3 |
| Exactamente 3 lapsos | 3 |
| Nivel inicial / primaria / media | 1, 4 |
| Grado + sección + turno mañana/tarde | 1, 4, 5 |
| Mismos lapsos para los tres niveles | 3 (lapsos del año, no del nivel) |
| Primaria elige esquema por grado | 4 (`informe` / `numerico`) |
| Aislamiento por plantel | 3, 4 |
| Alumno se inscribe a una sección | Plan siguiente (inscripción) |
| Docente a sección/materia | Plan de evaluación / asistencia |
| Cerrar lapso | Plan de evaluación (`cerrado` ya existe) |

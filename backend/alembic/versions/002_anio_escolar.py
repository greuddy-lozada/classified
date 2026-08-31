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
        sa.Column(
            "nivel",
            sa.Enum("inicial", "primaria", "media", name="nivel", native_enum=False, length=32),
            nullable=False,
        ),
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

"""inscripcion

Revision ID: 003inscrip
Revises: 002anioesc
Create Date: 2026-08-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003inscrip"
down_revision: Union[str, None] = "002anioesc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inscripcion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organizacion_id", sa.Uuid(), nullable=False),
        sa.Column("alumno_id", sa.Uuid(), nullable=False),
        sa.Column("anio_escolar_id", sa.Uuid(), nullable=False),
        sa.Column("seccion_id", sa.Uuid(), nullable=True),
        sa.Column(
            "estado",
            sa.Enum(
                "preinscrito",
                "inscrito",
                "activo",
                "retirado",
                name="estadoinscripcion",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "estado_matricula",
            sa.Enum("pendiente", "pagada", "morosa", name="estadomatricula", native_enum=False, length=32),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["alumno_id"], ["alumno.id"]),
        sa.ForeignKeyConstraint(["anio_escolar_id"], ["anio_escolar.id"]),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizacion.id"]),
        sa.ForeignKeyConstraint(["seccion_id"], ["seccion.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alumno_id", "anio_escolar_id"),
    )
    op.create_index(op.f("ix_inscripcion_organizacion_id"), "inscripcion", ["organizacion_id"], unique=False)
    op.create_index(op.f("ix_inscripcion_alumno_id"), "inscripcion", ["alumno_id"], unique=False)
    op.create_index(op.f("ix_inscripcion_anio_escolar_id"), "inscripcion", ["anio_escolar_id"], unique=False)
    op.create_table(
        "recaudo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("inscripcion_id", sa.Uuid(), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum(
                "partida",
                "cedula_alumno",
                "cedula_representante",
                "fotos",
                name="tiporecaudo",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "estado",
            sa.Enum("faltante", "entregado", name="estadorecaudo", native_enum=False, length=32),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["inscripcion_id"], ["inscripcion.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inscripcion_id", "tipo"),
    )
    op.create_index(op.f("ix_recaudo_inscripcion_id"), "recaudo", ["inscripcion_id"], unique=False)


def downgrade() -> None:
    op.drop_table("recaudo")
    op.drop_table("inscripcion")

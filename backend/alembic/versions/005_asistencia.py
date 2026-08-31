"""asistencia

Revision ID: 005asist
Revises: 004eval
Create Date: 2026-08-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005asist"
down_revision: Union[str, None] = "004eval"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "asistencia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organizacion_id", sa.Uuid(), nullable=False),
        sa.Column("inscripcion_id", sa.Uuid(), nullable=False),
        sa.Column("seccion_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column(
            "estado",
            sa.Enum(
                "presente",
                "ausente",
                "justificado",
                "tardanza",
                name="estadoasistencia",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["inscripcion_id"], ["inscripcion.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizacion.id"]),
        sa.ForeignKeyConstraint(["seccion_id"], ["seccion.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inscripcion_id", "fecha", "materia_id"),
    )
    op.create_index(op.f("ix_asistencia_organizacion_id"), "asistencia", ["organizacion_id"], unique=False)
    op.create_index(op.f("ix_asistencia_inscripcion_id"), "asistencia", ["inscripcion_id"], unique=False)
    op.create_index(op.f("ix_asistencia_seccion_id"), "asistencia", ["seccion_id"], unique=False)
    op.create_index(op.f("ix_asistencia_fecha"), "asistencia", ["fecha"], unique=False)


def downgrade() -> None:
    op.drop_table("asistencia")

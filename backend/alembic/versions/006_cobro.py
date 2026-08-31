"""cobro

Revision ID: 006cobro
Revises: 005asist
Create Date: 2026-08-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006cobro"
down_revision: Union[str, None] = "005asist"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cargo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organizacion_id", sa.Uuid(), nullable=False),
        sa.Column("inscripcion_id", sa.Uuid(), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum("matricula", "mensualidad", name="tipocargo", native_enum=False, length=32),
            nullable=False,
        ),
        sa.Column("periodo", sa.String(length=7), nullable=False),
        sa.Column("concepto", sa.String(length=80), nullable=False),
        sa.Column(
            "estado",
            sa.Enum("pendiente", "pagada", "morosa", name="estadomatricula", native_enum=False, length=32),
            nullable=False,
        ),
        sa.Column("fecha_pago", sa.Date(), nullable=True),
        sa.Column("nota", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["inscripcion_id"], ["inscripcion.id"]),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizacion.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inscripcion_id", "tipo", "periodo"),
    )
    op.create_index(op.f("ix_cargo_organizacion_id"), "cargo", ["organizacion_id"], unique=False)
    op.create_index(op.f("ix_cargo_inscripcion_id"), "cargo", ["inscripcion_id"], unique=False)


def downgrade() -> None:
    op.drop_table("cargo")

"""evaluacion

Revision ID: 004eval
Revises: 003inscrip
Create Date: 2026-08-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004eval"
down_revision: Union[str, None] = "003inscrip"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "materia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organizacion_id", sa.Uuid(), nullable=False),
        sa.Column("grado_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=80), nullable=False),
        sa.ForeignKeyConstraint(["grado_id"], ["grado.id"]),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizacion.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("grado_id", "nombre"),
    )
    op.create_index(op.f("ix_materia_organizacion_id"), "materia", ["organizacion_id"], unique=False)
    op.create_index(op.f("ix_materia_grado_id"), "materia", ["grado_id"], unique=False)
    op.create_table(
        "asignacion_docente",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organizacion_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("seccion_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizacion.id"]),
        sa.ForeignKeyConstraint(["seccion_id"], ["seccion.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "seccion_id", "materia_id"),
    )
    op.create_index(op.f("ix_asignacion_docente_organizacion_id"), "asignacion_docente", ["organizacion_id"], unique=False)
    op.create_index(op.f("ix_asignacion_docente_usuario_id"), "asignacion_docente", ["usuario_id"], unique=False)
    op.create_index(op.f("ix_asignacion_docente_seccion_id"), "asignacion_docente", ["seccion_id"], unique=False)
    op.create_table(
        "nota",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organizacion_id", sa.Uuid(), nullable=False),
        sa.Column("inscripcion_id", sa.Uuid(), nullable=False),
        sa.Column("lapso_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["inscripcion_id"], ["inscripcion.id"]),
        sa.ForeignKeyConstraint(["lapso_id"], ["lapso.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizacion.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inscripcion_id", "lapso_id", "materia_id"),
    )
    op.create_index(op.f("ix_nota_organizacion_id"), "nota", ["organizacion_id"], unique=False)
    op.create_index(op.f("ix_nota_inscripcion_id"), "nota", ["inscripcion_id"], unique=False)
    op.create_index(op.f("ix_nota_lapso_id"), "nota", ["lapso_id"], unique=False)
    op.create_table(
        "informe_item",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organizacion_id", sa.Uuid(), nullable=False),
        sa.Column("inscripcion_id", sa.Uuid(), nullable=False),
        sa.Column("lapso_id", sa.Uuid(), nullable=False),
        sa.Column(
            "area",
            sa.Enum(
                "lenguaje",
                "socioemocional",
                "psicomotor",
                "exploracion",
                name="areainforme",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "juicio",
            sa.Enum("logrado", "en_proceso", "iniciado", name="juicio", native_enum=False, length=32),
            nullable=False,
        ),
        sa.Column("comentario", sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(["inscripcion_id"], ["inscripcion.id"]),
        sa.ForeignKeyConstraint(["lapso_id"], ["lapso.id"]),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizacion.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inscripcion_id", "lapso_id", "area"),
    )
    op.create_index(op.f("ix_informe_item_organizacion_id"), "informe_item", ["organizacion_id"], unique=False)
    op.create_index(op.f("ix_informe_item_inscripcion_id"), "informe_item", ["inscripcion_id"], unique=False)
    op.create_index(op.f("ix_informe_item_lapso_id"), "informe_item", ["lapso_id"], unique=False)


def downgrade() -> None:
    op.drop_table("informe_item")
    op.drop_table("nota")
    op.drop_table("asignacion_docente")
    op.drop_table("materia")

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AsignacionDocente(Base):
    __tablename__ = "asignacion_docente"
    __table_args__ = (UniqueConstraint("usuario_id", "seccion_id", "materia_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"), index=True)
    seccion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seccion.id"), index=True)
    materia_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("materia.id"), nullable=True)

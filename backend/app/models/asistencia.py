import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import EstadoAsistencia


class Asistencia(Base):
    __tablename__ = "asistencia"
    __table_args__ = (UniqueConstraint("inscripcion_id", "fecha", "materia_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    inscripcion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inscripcion.id"), index=True)
    seccion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seccion.id"), index=True)
    materia_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("materia.id"), nullable=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    estado: Mapped[EstadoAsistencia] = mapped_column(
        Enum(EstadoAsistencia, native_enum=False, length=32)
    )

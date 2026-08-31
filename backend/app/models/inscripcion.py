import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EstadoInscripcion, EstadoMatricula


class Inscripcion(Base):
    __tablename__ = "inscripcion"
    __table_args__ = (UniqueConstraint("alumno_id", "anio_escolar_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    alumno_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alumno.id"), index=True)
    anio_escolar_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("anio_escolar.id"), index=True)
    seccion_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("seccion.id"), nullable=True)
    estado: Mapped[EstadoInscripcion] = mapped_column(
        Enum(EstadoInscripcion, native_enum=False, length=32)
    )
    estado_matricula: Mapped[EstadoMatricula] = mapped_column(
        Enum(EstadoMatricula, native_enum=False, length=32),
        default=EstadoMatricula.pendiente,
    )

    recaudos = relationship("Recaudo", back_populates="inscripcion")

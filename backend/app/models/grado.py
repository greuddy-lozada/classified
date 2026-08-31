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

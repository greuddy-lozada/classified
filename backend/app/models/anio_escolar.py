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

import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Turno


class Seccion(Base):
    __tablename__ = "seccion"
    __table_args__ = (UniqueConstraint("grado_id", "letra", "turno"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    grado_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grado.id"), index=True)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    letra: Mapped[str] = mapped_column(String(8))
    turno: Mapped[Turno] = mapped_column(Enum(Turno, native_enum=False, length=16))

    grado = relationship("Grado", back_populates="secciones")

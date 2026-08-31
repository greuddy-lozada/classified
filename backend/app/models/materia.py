import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Materia(Base):
    __tablename__ = "materia"
    __table_args__ = (UniqueConstraint("grado_id", "nombre"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    grado_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grado.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(80))

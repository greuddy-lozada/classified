import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organizacion(Base):
    __tablename__ = "organizacion"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(200))
    rif: Mapped[str | None] = mapped_column(String(20), nullable=True)
    activo: Mapped[bool] = mapped_column(default=True)

    membresias = relationship("Membresia", back_populates="organizacion")

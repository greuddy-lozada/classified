import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Alumno(Base):
    __tablename__ = "alumno"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    persona_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persona.id"), unique=True)

    persona = relationship("Persona", back_populates="alumno")
    vinculos = relationship("VinculoRepresentante", back_populates="alumno")

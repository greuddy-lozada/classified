import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Parentesco


class VinculoRepresentante(Base):
    __tablename__ = "vinculo_representante"
    __table_args__ = (UniqueConstraint("representante_persona_id", "alumno_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    representante_persona_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persona.id"))
    alumno_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alumno.id"))
    parentesco: Mapped[Parentesco] = mapped_column(Enum(Parentesco, native_enum=False, length=32))
    es_principal: Mapped[bool] = mapped_column(default=False)

    alumno = relationship("Alumno", back_populates="vinculos")
    representante = relationship("Persona", foreign_keys=[representante_persona_id])

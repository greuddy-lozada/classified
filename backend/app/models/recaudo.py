import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EstadoRecaudo, TipoRecaudo


class Recaudo(Base):
    __tablename__ = "recaudo"
    __table_args__ = (UniqueConstraint("inscripcion_id", "tipo"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    inscripcion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inscripcion.id"), index=True)
    tipo: Mapped[TipoRecaudo] = mapped_column(Enum(TipoRecaudo, native_enum=False, length=32))
    estado: Mapped[EstadoRecaudo] = mapped_column(Enum(EstadoRecaudo, native_enum=False, length=32))

    inscripcion = relationship("Inscripcion", back_populates="recaudos")

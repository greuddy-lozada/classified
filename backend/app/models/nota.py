import uuid

from sqlalchemy import Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Nota(Base):
    __tablename__ = "nota"
    __table_args__ = (UniqueConstraint("inscripcion_id", "lapso_id", "materia_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    inscripcion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inscripcion.id"), index=True)
    lapso_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lapso.id"), index=True)
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materia.id"))
    valor: Mapped[float] = mapped_column(Float)

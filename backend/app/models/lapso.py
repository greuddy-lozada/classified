import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Lapso(Base):
    __tablename__ = "lapso"
    __table_args__ = (UniqueConstraint("anio_escolar_id", "numero"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    anio_escolar_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("anio_escolar.id"), index=True)
    numero: Mapped[int] = mapped_column(Integer)
    nombre: Mapped[str] = mapped_column(String(40))
    cerrado: Mapped[bool] = mapped_column(default=False)

    anio_escolar = relationship("AnioEscolar", back_populates="lapsos")

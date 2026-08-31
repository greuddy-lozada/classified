import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import EstadoMatricula, TipoCargo


class Cargo(Base):
    __tablename__ = "cargo"
    __table_args__ = (UniqueConstraint("inscripcion_id", "tipo", "periodo"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    inscripcion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inscripcion.id"), index=True)
    tipo: Mapped[TipoCargo] = mapped_column(Enum(TipoCargo, native_enum=False, length=32))
    periodo: Mapped[str] = mapped_column(String(7), default="")
    concepto: Mapped[str] = mapped_column(String(80))
    estado: Mapped[EstadoMatricula] = mapped_column(
        Enum(EstadoMatricula, native_enum=False, length=32)
    )
    fecha_pago: Mapped[date | None] = mapped_column(Date, nullable=True)
    nota: Mapped[str | None] = mapped_column(String(200), nullable=True)

import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AreaInforme, Juicio


class InformeItem(Base):
    __tablename__ = "informe_item"
    __table_args__ = (UniqueConstraint("inscripcion_id", "lapso_id", "area"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    inscripcion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inscripcion.id"), index=True)
    lapso_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lapso.id"), index=True)
    area: Mapped[AreaInforme] = mapped_column(Enum(AreaInforme, native_enum=False, length=32))
    juicio: Mapped[Juicio] = mapped_column(Enum(Juicio, native_enum=False, length=32))
    comentario: Mapped[str] = mapped_column(String(500), default="")

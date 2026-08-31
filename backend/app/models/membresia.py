import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Rol


class Membresia(Base):
    __tablename__ = "membresia"
    __table_args__ = (UniqueConstraint("usuario_id", "organizacion_id", "rol"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"))
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"))
    rol: Mapped[Rol] = mapped_column(Enum(Rol, native_enum=False, length=32))
    activo: Mapped[bool] = mapped_column(default=True)

    usuario = relationship("Usuario", back_populates="membresias")
    organizacion = relationship("Organizacion", back_populates="membresias")

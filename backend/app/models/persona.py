import uuid
from datetime import date

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TipoDoc


class Persona(Base):
    __tablename__ = "persona"
    __table_args__ = (UniqueConstraint("organizacion_id", "tipo_doc", "numero_doc"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizacion.id"), index=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    tipo_doc: Mapped[TipoDoc] = mapped_column(Enum(TipoDoc, native_enum=False, length=32))
    numero_doc: Mapped[str] = mapped_column(String(40))
    nombres: Mapped[str] = mapped_column(String(120))
    apellidos: Mapped[str] = mapped_column(String(120))
    fecha_nacimiento: Mapped[date | None] = mapped_column(nullable=True)
    sexo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(40), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)

    alumno = relationship("Alumno", back_populates="persona", uselist=False)

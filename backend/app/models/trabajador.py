import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Trabajador(Base):
    __tablename__ = "trabajador"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    persona_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persona.id"), unique=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"))

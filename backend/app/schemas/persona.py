from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import TipoDoc


class PersonaCreate(BaseModel):
    tipo_doc: TipoDoc
    numero_doc: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date | None = None
    sexo: str | None = None
    telefono: str | None = None
    direccion: str | None = None


class PersonaOut(BaseModel):
    id: UUID
    organizacion_id: UUID
    usuario_id: UUID | None
    tipo_doc: TipoDoc
    numero_doc: str
    nombres: str
    apellidos: str
    es_alumno: bool

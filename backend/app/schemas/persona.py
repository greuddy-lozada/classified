from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import Parentesco, TipoDoc


class PersonaCreate(BaseModel):
    tipo_doc: TipoDoc
    numero_doc: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date | None = None
    sexo: str | None = None
    telefono: str | None = None
    direccion: str | None = None


class PersonaUpdate(BaseModel):
    tipo_doc: TipoDoc
    numero_doc: str
    nombres: str
    apellidos: str


class PersonaOut(BaseModel):
    id: UUID
    organizacion_id: UUID
    usuario_id: UUID | None
    tipo_doc: TipoDoc
    numero_doc: str
    nombres: str
    apellidos: str
    es_alumno: bool
    es_trabajador: bool = False
    alumno_id: UUID | None = None


class RepresentanteCreate(PersonaCreate):
    email: str
    password: str
    alumno_id: UUID
    parentesco: Parentesco
    es_principal: bool = True


class DocenteCreate(PersonaCreate):
    email: str
    password: str

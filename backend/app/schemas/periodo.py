from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import EsquemaEvaluacion, Nivel, Turno


class AnioCreate(BaseModel):
    nombre: str = Field(min_length=4, max_length=32)


class AnioUpdate(BaseModel):
    nombre: str = Field(min_length=4, max_length=32)


class GradoUpdate(BaseModel):
    nombre: str = Field(min_length=1, max_length=40)


class SeccionUpdate(BaseModel):
    letra: str = Field(min_length=1, max_length=8)
    turno: Turno


class LapsoOut(BaseModel):
    id: UUID
    numero: int
    nombre: str
    cerrado: bool


class AnioOut(BaseModel):
    id: UUID
    organizacion_id: UUID
    nombre: str
    activo: bool
    lapsos: list[LapsoOut]


class GradoCreate(BaseModel):
    anio_escolar_id: UUID
    nivel: Nivel
    nombre: str = Field(min_length=1, max_length=40)
    esquema_evaluacion: EsquemaEvaluacion | None = None


class SeccionOut(BaseModel):
    id: UUID
    grado_id: UUID
    letra: str
    turno: Turno


class GradoOut(BaseModel):
    id: UUID
    anio_escolar_id: UUID
    organizacion_id: UUID
    nivel: Nivel
    nombre: str
    esquema_evaluacion: EsquemaEvaluacion
    secciones: list[SeccionOut] = []


class SeccionCreate(BaseModel):
    grado_id: UUID
    letra: str = Field(min_length=1, max_length=8)
    turno: Turno

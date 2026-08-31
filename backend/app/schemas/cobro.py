from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import EstadoMatricula, TipoCargo


class GenerarIn(BaseModel):
    anio_escolar_id: UUID
    periodos: list[str] = Field(default_factory=list)


class CargoPatch(BaseModel):
    estado: EstadoMatricula
    fecha_pago: date | None = None
    nota: str | None = None


class CargoOut(BaseModel):
    id: UUID
    inscripcion_id: UUID
    alumno_nombres: str
    alumno_apellidos: str
    tipo: TipoCargo
    periodo: str
    concepto: str
    estado: EstadoMatricula
    fecha_pago: date | None
    nota: str | None

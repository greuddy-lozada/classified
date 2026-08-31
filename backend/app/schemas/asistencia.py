from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import EstadoAsistencia


class AsistenciaIn(BaseModel):
    inscripcion_id: UUID
    fecha: date
    estado: EstadoAsistencia
    materia_id: UUID | None = None


class ListaItemOut(BaseModel):
    inscripcion_id: UUID
    alumno_nombres: str
    alumno_apellidos: str
    estado: EstadoAsistencia | None


class ResumenOut(BaseModel):
    inscripcion_id: UUID
    alumno_nombres: str
    alumno_apellidos: str
    materia_id: UUID | None
    total: int
    presentes: int
    ausentes: int
    justificados: int
    tardanzas: int
    porcentaje: float | None

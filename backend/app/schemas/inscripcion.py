from uuid import UUID

from pydantic import BaseModel

from app.models.enums import EstadoInscripcion, EstadoMatricula, EstadoRecaudo, TipoRecaudo


class InscripcionCreate(BaseModel):
    alumno_id: UUID
    anio_escolar_id: UUID


class AsignarSeccionIn(BaseModel):
    seccion_id: UUID


class RecaudoPatch(BaseModel):
    tipo: TipoRecaudo
    estado: EstadoRecaudo


class MatriculaPatch(BaseModel):
    estado_matricula: EstadoMatricula


class RecaudoOut(BaseModel):
    tipo: TipoRecaudo
    estado: EstadoRecaudo


class InscripcionOut(BaseModel):
    id: UUID
    organizacion_id: UUID
    alumno_id: UUID
    alumno_nombres: str
    alumno_apellidos: str
    anio_escolar_id: UUID
    seccion_id: UUID | None
    estado: EstadoInscripcion
    estado_matricula: EstadoMatricula
    recaudos: list[RecaudoOut]
    recaudos_pendientes: bool

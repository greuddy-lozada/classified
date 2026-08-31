from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import AreaInforme, Juicio


class MateriaCreate(BaseModel):
    grado_id: UUID
    nombre: str = Field(min_length=1, max_length=80)


class MateriaUpdate(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)


class MateriaOut(BaseModel):
    id: UUID
    grado_id: UUID
    nombre: str


class AsignacionCreate(BaseModel):
    usuario_id: UUID
    seccion_id: UUID
    materia_id: UUID | None = None


class AsignacionOut(BaseModel):
    id: UUID
    usuario_id: UUID
    usuario_email: str
    seccion_id: UUID
    materia_id: UUID | None
    materia_nombre: str | None = None


class DocenteOut(BaseModel):
    usuario_id: UUID
    email: str
    persona_id: UUID | None = None
    nombres: str = ""
    apellidos: str = ""
    tipo_doc: str | None = None
    numero_doc: str | None = None


class NotaIn(BaseModel):
    inscripcion_id: UUID
    lapso_id: UUID
    materia_id: UUID
    valor: float


class NotaOut(BaseModel):
    materia_id: UUID
    materia_nombre: str
    valor: float
    aprobada: bool


class InformeIn(BaseModel):
    inscripcion_id: UUID
    lapso_id: UUID
    area: AreaInforme
    juicio: Juicio
    comentario: str = ""


class InformeOut(BaseModel):
    area: AreaInforme
    juicio: Juicio
    comentario: str


class BoletinLapsoOut(BaseModel):
    lapso_id: UUID
    lapso_nombre: str
    cerrado: bool
    notas: list[NotaOut]
    informes: list[InformeOut]
    promedio: float | None


class BoletinOut(BaseModel):
    inscripcion_id: UUID
    alumno_nombres: str
    alumno_apellidos: str
    esquema: str
    lapsos: list[BoletinLapsoOut]
    promedio_final: float | None
    necesita_reparacion: bool

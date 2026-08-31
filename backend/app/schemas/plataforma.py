from uuid import UUID

from pydantic import BaseModel, EmailStr


class OrganizacionCreate(BaseModel):
    nombre: str
    rif: str | None = None
    admin_email: EmailStr
    admin_password: str
    admin_nombres: str
    admin_apellidos: str


class OrganizacionOut(BaseModel):
    id: UUID
    nombre: str
    rif: str | None
    admin_usuario_id: UUID


class OrganizacionListaOut(BaseModel):
    id: UUID
    nombre: str
    rif: str | None

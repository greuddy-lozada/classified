from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class MembresiaOut(BaseModel):
    organizacion_id: UUID
    organizacion_nombre: str
    rol: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    membresias: list[MembresiaOut]


class SeleccionarIn(BaseModel):
    organizacion_id: UUID
    rol: str


class MeOut(BaseModel):
    id: UUID
    email: str
    es_plataforma: bool
    organizacion_id: UUID | None
    rol: str | None

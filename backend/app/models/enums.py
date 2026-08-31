from enum import Enum


class Rol(str, Enum):
    direccion = "direccion"
    secretaria = "secretaria"
    docente = "docente"
    representante = "representante"
    estudiante = "estudiante"


class TipoDoc(str, Enum):
    cedula_v = "cedula_v"
    cedula_e = "cedula_e"
    pasaporte = "pasaporte"
    partida = "partida"
    expediente = "expediente"


class Parentesco(str, Enum):
    madre = "madre"
    padre = "padre"
    abuelo = "abuelo"
    tutor = "tutor"


class Nivel(str, Enum):
    inicial = "inicial"
    primaria = "primaria"
    media = "media"


class Turno(str, Enum):
    manana = "manana"
    tarde = "tarde"


class EsquemaEvaluacion(str, Enum):
    informe = "informe"
    numerico = "numerico"

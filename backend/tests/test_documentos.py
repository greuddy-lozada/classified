from fastapi.testclient import TestClient

from app.models.usuario import Usuario
from tests.test_evaluacion import _media_inscrito
from tests.test_personas import _auth


def test_pdf_boletin_media(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    ctx = _media_inscrito(client)
    client.post(
        "/evaluacion/notas",
        json={
            "inscripcion_id": ctx["ins"]["id"],
            "lapso_id": ctx["lapso_id"],
            "materia_id": ctx["materia"]["id"],
            "valor": 16,
        },
        headers=ctx["dir"],
    )
    pdf = client.get(
        f"/evaluacion/boletines/{ctx['ins']['id']}/pdf",
        headers=_auth(client, "carla-ev@mail.com"),
    )
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content.startswith(b"%PDF")
    assert b"Mia Gil" in pdf.content
    assert b"Boletin de calificaciones" in pdf.content


def test_pdf_informe_inicial(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    dir_h = _auth(client, "dir@a.edu")
    sec_h = _auth(client, "secretaria@a.edu")
    anio = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=dir_h).json()
    grado = client.post(
        "/periodo/grados",
        json={"anio_escolar_id": anio["id"], "nivel": "inicial", "nombre": "3er nivel"},
        headers=dir_h,
    ).json()
    seccion = client.post(
        "/periodo/secciones",
        json={"grado_id": grado["id"], "letra": "A", "turno": "manana"},
        headers=dir_h,
    ).json()
    alumno = client.post(
        "/personas/alumnos",
        json={"tipo_doc": "partida", "numero_doc": "PN-PDF1", "nombres": "Eva", "apellidos": "Gil"},
        headers=sec_h,
    ).json()
    client.post(
        "/personas/representantes",
        json={
            "tipo_doc": "cedula_v",
            "numero_doc": "16999333",
            "nombres": "Rosa",
            "apellidos": "Gil",
            "email": "rosa-pdf@mail.com",
            "password": "clave123",
            "alumno_id": alumno["alumno_id"],
            "parentesco": "madre",
            "es_principal": True,
        },
        headers=sec_h,
    )
    ins = client.post(
        "/inscripciones",
        json={"alumno_id": alumno["alumno_id"], "anio_escolar_id": anio["id"]},
        headers=sec_h,
    ).json()
    client.post(f"/inscripciones/{ins['id']}/seccion", json={"seccion_id": seccion["id"]}, headers=sec_h)
    client.post(
        "/evaluacion/informes",
        json={
            "inscripcion_id": ins["id"],
            "lapso_id": anio["lapsos"][0]["id"],
            "area": "lenguaje",
            "juicio": "en_proceso",
            "comentario": "Participa en ronda",
        },
        headers=dir_h,
    )
    pdf = client.get(f"/evaluacion/boletines/{ins['id']}/pdf", headers=_auth(client, "rosa-pdf@mail.com"))
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert b"Informe descriptivo" in pdf.content
    assert b"Eva Gil" in pdf.content
    assert b"lenguaje" in pdf.content


def test_colegio_b_no_descarga_pdf(
    client: TestClient, direccion: Usuario, secretaria: Usuario, secretaria_b: Usuario
) -> None:
    ctx = _media_inscrito(client)
    stolen = client.get(
        f"/evaluacion/boletines/{ctx['ins']['id']}/pdf",
        headers=_auth(client, "secretaria@b.edu"),
    )
    assert stolen.status_code == 404

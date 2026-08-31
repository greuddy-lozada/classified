from fastapi.testclient import TestClient

from app.models.usuario import Usuario
from tests.test_evaluacion import _media_inscrito
from tests.test_personas import _auth


def test_media_requiere_materia(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    ctx = _media_inscrito(client)
    listed = client.get(
        f"/asistencia/lista?seccion_id={ctx['seccion']['id']}&fecha=2026-10-01",
        headers=ctx["dir"],
    )
    assert listed.status_code == 409
    listed = client.get(
        f"/asistencia/lista?seccion_id={ctx['seccion']['id']}&fecha=2026-10-01&materia_id={ctx['materia']['id']}",
        headers=ctx["dir"],
    )
    assert listed.status_code == 200
    assert listed.json()[0]["inscripcion_id"] == ctx["ins"]["id"]
    assert listed.json()[0]["estado"] is None


def test_pasar_lista_media_y_porcentaje(
    client: TestClient, direccion: Usuario, secretaria: Usuario
) -> None:
    ctx = _media_inscrito(client)
    marked = client.put(
        "/asistencia",
        json={
            "inscripcion_id": ctx["ins"]["id"],
            "fecha": "2026-10-01",
            "estado": "presente",
            "materia_id": ctx["materia"]["id"],
        },
        headers=ctx["dir"],
    )
    assert marked.status_code == 200
    client.put(
        "/asistencia",
        json={
            "inscripcion_id": ctx["ins"]["id"],
            "fecha": "2026-10-02",
            "estado": "ausente",
            "materia_id": ctx["materia"]["id"],
        },
        headers=ctx["dir"],
    )
    resumen = client.get(
        f"/asistencia/{ctx['ins']['id']}?materia_id={ctx['materia']['id']}",
        headers=ctx["dir"],
    )
    assert resumen.status_code == 200
    assert resumen.json()["total"] == 2
    assert resumen.json()["ausentes"] == 1
    assert resumen.json()["porcentaje"] == 50.0
    mias = client.get("/asistencia/mias", headers=_auth(client, "carla-ev@mail.com"))
    assert mias.status_code == 200
    assert mias.json()[0]["inscripcion_id"] == ctx["ins"]["id"]


def test_retirado_no_aparece(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    ctx = _media_inscrito(client)
    client.post(f"/inscripciones/{ctx['ins']['id']}/retirar", headers=ctx["sec"])
    listed = client.get(
        f"/asistencia/lista?seccion_id={ctx['seccion']['id']}&fecha=2026-10-01&materia_id={ctx['materia']['id']}",
        headers=ctx["dir"],
    )
    assert listed.status_code == 200
    assert listed.json() == []


def test_representante_no_marca(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    ctx = _media_inscrito(client)
    forbidden = client.put(
        "/asistencia",
        json={
            "inscripcion_id": ctx["ins"]["id"],
            "fecha": "2026-10-01",
            "estado": "justificado",
            "materia_id": ctx["materia"]["id"],
        },
        headers=_auth(client, "carla-ev@mail.com"),
    )
    assert forbidden.status_code == 403


def test_inicial_lista_sin_materia(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
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
        json={"tipo_doc": "partida", "numero_doc": "PN-AS1", "nombres": "Eva", "apellidos": "Gil"},
        headers=sec_h,
    ).json()
    client.post(
        "/personas/representantes",
        json={
            "tipo_doc": "cedula_v",
            "numero_doc": "16999111",
            "nombres": "Rosa",
            "apellidos": "Gil",
            "email": "rosa-as@mail.com",
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
    marked = client.put(
        "/asistencia",
        json={"inscripcion_id": ins["id"], "fecha": "2026-10-01", "estado": "tardanza"},
        headers=dir_h,
    )
    assert marked.status_code == 200
    listed = client.get(
        f"/asistencia/lista?seccion_id={seccion['id']}&fecha=2026-10-01",
        headers=dir_h,
    )
    assert listed.status_code == 200
    assert listed.json()[0]["estado"] == "tardanza"

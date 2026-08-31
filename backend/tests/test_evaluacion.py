from fastapi.testclient import TestClient

from app.models.usuario import Usuario
from tests.test_personas import _auth


def _media_inscrito(client: TestClient) -> dict:
    dir_h = _auth(client, "dir@a.edu")
    sec_h = _auth(client, "secretaria@a.edu")
    anio = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=dir_h).json()
    grado = client.post(
        "/periodo/grados",
        json={"anio_escolar_id": anio["id"], "nivel": "media", "nombre": "3er año"},
        headers=dir_h,
    ).json()
    seccion = client.post(
        "/periodo/secciones",
        json={"grado_id": grado["id"], "letra": "A", "turno": "manana"},
        headers=dir_h,
    ).json()
    alumno = client.post(
        "/personas/alumnos",
        json={"tipo_doc": "partida", "numero_doc": "PN-EV1", "nombres": "Mia", "apellidos": "Gil"},
        headers=sec_h,
    ).json()
    client.post(
        "/personas/representantes",
        json={
            "tipo_doc": "cedula_v",
            "numero_doc": "16999001",
            "nombres": "Carla",
            "apellidos": "Gil",
            "email": "carla-ev@mail.com",
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
    materia = client.post(
        "/evaluacion/materias",
        json={"grado_id": grado["id"], "nombre": "Matemática"},
        headers=dir_h,
    ).json()
    return {
        "dir": dir_h,
        "sec": sec_h,
        "anio": anio,
        "grado": grado,
        "seccion": seccion,
        "ins": ins,
        "materia": materia,
        "lapso_id": anio["lapsos"][0]["id"],
    }


def test_nota_media_y_boletin(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    ctx = _media_inscrito(client)
    nota = client.post(
        "/evaluacion/notas",
        json={
            "inscripcion_id": ctx["ins"]["id"],
            "lapso_id": ctx["lapso_id"],
            "materia_id": ctx["materia"]["id"],
            "valor": 16,
        },
        headers=ctx["dir"],
    )
    assert nota.status_code == 200
    assert nota.json()["aprobada"] is True
    boletin = client.get(f"/evaluacion/boletines/{ctx['ins']['id']}", headers=_auth(client, "carla-ev@mail.com"))
    assert boletin.status_code == 200
    assert boletin.json()["esquema"] == "numerico"
    assert boletin.json()["lapsos"][0]["promedio"] == 16
    assert boletin.json()["necesita_reparacion"] is False


def test_no_edita_lapso_cerrado(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    ctx = _media_inscrito(client)
    closed = client.post(f"/periodo/lapsos/{ctx['lapso_id']}/cerrar", headers=ctx["dir"])
    assert closed.status_code == 200
    assert closed.json()["cerrado"] is True
    blocked = client.post(
        "/evaluacion/notas",
        json={
            "inscripcion_id": ctx["ins"]["id"],
            "lapso_id": ctx["lapso_id"],
            "materia_id": ctx["materia"]["id"],
            "valor": 12,
        },
        headers=ctx["dir"],
    )
    assert blocked.status_code == 409
    client.post(f"/periodo/lapsos/{ctx['lapso_id']}/reabrir", headers=ctx["dir"])
    ok = client.post(
        "/evaluacion/notas",
        json={
            "inscripcion_id": ctx["ins"]["id"],
            "lapso_id": ctx["lapso_id"],
            "materia_id": ctx["materia"]["id"],
            "valor": 12,
        },
        headers=ctx["dir"],
    )
    assert ok.status_code == 200


def test_docente_solo_su_materia(
    client: TestClient, direccion: Usuario, secretaria: Usuario, docente: Usuario
) -> None:
    ctx = _media_inscrito(client)
    client.post(
        "/evaluacion/asignaciones",
        json={
            "usuario_id": str(docente.id),
            "seccion_id": ctx["seccion"]["id"],
            "materia_id": ctx["materia"]["id"],
        },
        headers=ctx["dir"],
    )
    ok = client.post(
        "/evaluacion/notas",
        json={
            "inscripcion_id": ctx["ins"]["id"],
            "lapso_id": ctx["lapso_id"],
            "materia_id": ctx["materia"]["id"],
            "valor": 14,
        },
        headers=_auth(client, "docente@a.edu"),
    )
    assert ok.status_code == 200
    forbidden = client.post(
        "/evaluacion/notas",
        json={
            "inscripcion_id": ctx["ins"]["id"],
            "lapso_id": ctx["lapso_id"],
            "materia_id": ctx["materia"]["id"],
            "valor": 9,
        },
        headers=ctx["sec"],
    )
    assert forbidden.status_code == 403


def test_informe_inicial(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
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
        json={"tipo_doc": "partida", "numero_doc": "PN-EV2", "nombres": "Eva", "apellidos": "Gil"},
        headers=sec_h,
    ).json()
    client.post(
        "/personas/representantes",
        json={
            "tipo_doc": "cedula_v",
            "numero_doc": "16999002",
            "nombres": "Rosa",
            "apellidos": "Gil",
            "email": "rosa-ev@mail.com",
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
    bad_materia = client.post(
        "/evaluacion/materias",
        json={"grado_id": grado["id"], "nombre": "Mate"},
        headers=dir_h,
    )
    assert bad_materia.status_code == 409
    informe = client.post(
        "/evaluacion/informes",
        json={
            "inscripcion_id": ins["id"],
            "lapso_id": anio["lapsos"][0]["id"],
            "area": "lenguaje",
            "juicio": "en_proceso",
            "comentario": "Participa más en ronda",
        },
        headers=dir_h,
    )
    assert informe.status_code == 200
    boletin = client.get(f"/evaluacion/boletines/{ins['id']}", headers=_auth(client, "rosa-ev@mail.com"))
    assert boletin.status_code == 200
    assert boletin.json()["esquema"] == "informe"
    assert boletin.json()["lapsos"][0]["informes"][0]["area"] == "lenguaje"


def test_asignacion_docente_lista_y_borra(
    client: TestClient, direccion: Usuario, secretaria: Usuario, docente: Usuario
) -> None:
    ctx = _media_inscrito(client)
    created = client.post(
        "/evaluacion/asignaciones",
        json={
            "usuario_id": str(docente.id),
            "seccion_id": ctx["seccion"]["id"],
            "materia_id": ctx["materia"]["id"],
        },
        headers=ctx["dir"],
    )
    assert created.status_code == 201
    assert created.json()["usuario_email"] == "docente@a.edu"
    listed = client.get(
        f"/evaluacion/asignaciones?seccion_id={ctx['seccion']['id']}",
        headers=ctx["dir"],
    )
    assert listed.status_code == 200
    assert listed.json()[0]["materia_nombre"] == "Matemática"
    docs = client.get("/evaluacion/docentes", headers=ctx["dir"])
    assert docs.status_code == 200
    assert docs.json()[0]["email"] == "docente@a.edu"
    gone = client.delete(f"/evaluacion/asignaciones/{created.json()['id']}", headers=ctx["dir"])
    assert gone.status_code == 204


def test_materia_crud(client: TestClient, direccion: Usuario, secretaria: Usuario, docente: Usuario) -> None:
    ctx = _media_inscrito(client)
    listed = client.get(f"/evaluacion/materias?grado_id={ctx['grado']['id']}", headers=ctx["dir"])
    assert listed.status_code == 200
    assert listed.json()[0]["nombre"] == "Matemática"
    renamed = client.patch(
        f"/evaluacion/materias/{ctx['materia']['id']}",
        json={"nombre": "Matemática I"},
        headers=ctx["sec"],
    )
    assert renamed.status_code == 200
    assert renamed.json()["nombre"] == "Matemática I"
    extra = client.post(
        "/evaluacion/materias",
        json={"grado_id": ctx["grado"]["id"], "nombre": "Castellano"},
        headers=ctx["dir"],
    )
    assert extra.status_code == 201
    gone = client.delete(f"/evaluacion/materias/{extra.json()['id']}", headers=ctx["dir"])
    assert gone.status_code == 204
    forbidden = client.patch(
        f"/evaluacion/materias/{ctx['materia']['id']}",
        json={"nombre": "Física"},
        headers=_auth(client, "docente@a.edu"),
    )
    assert forbidden.status_code == 403


def test_no_borra_materia_con_nota(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    ctx = _media_inscrito(client)
    client.post(
        "/evaluacion/notas",
        json={
            "inscripcion_id": ctx["ins"]["id"],
            "lapso_id": ctx["lapso_id"],
            "materia_id": ctx["materia"]["id"],
            "valor": 15,
        },
        headers=ctx["dir"],
    )
    blocked = client.delete(f"/evaluacion/materias/{ctx['materia']['id']}", headers=ctx["dir"])
    assert blocked.status_code == 409


def test_colegio_b_no_edita_materia(
    client: TestClient, direccion: Usuario, secretaria: Usuario, secretaria_b: Usuario
) -> None:
    ctx = _media_inscrito(client)
    stolen = client.patch(
        f"/evaluacion/materias/{ctx['materia']['id']}",
        json={"nombre": "Robada"},
        headers=_auth(client, "secretaria@b.edu"),
    )
    assert stolen.status_code == 404


def test_colegio_b_no_ve_boletin(
    client: TestClient, direccion: Usuario, secretaria: Usuario, secretaria_b: Usuario
) -> None:
    ctx = _media_inscrito(client)
    stolen = client.get(
        f"/evaluacion/boletines/{ctx['ins']['id']}",
        headers=_auth(client, "secretaria@b.edu"),
    )
    assert stolen.status_code == 404

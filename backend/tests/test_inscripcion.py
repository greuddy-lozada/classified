from fastapi.testclient import TestClient

from app.models.usuario import Usuario
from tests.test_personas import _auth


def _abrir_seccion(client: TestClient) -> tuple[dict[str, str], str, str]:
    headers = _auth(client, "dir@a.edu")
    anio = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers).json()
    grado = client.post(
        "/periodo/grados",
        json={"anio_escolar_id": anio["id"], "nivel": "primaria", "nombre": "4°"},
        headers=headers,
    ).json()
    seccion = client.post(
        "/periodo/secciones",
        json={"grado_id": grado["id"], "letra": "A", "turno": "manana"},
        headers=headers,
    ).json()
    return _auth(client, "secretaria@a.edu"), anio["id"], seccion["id"]


def _alumno(client: TestClient, headers: dict[str, str], doc: str, nombre: str) -> dict:
    return client.post(
        "/personas/alumnos",
        json={"tipo_doc": "partida", "numero_doc": doc, "nombres": nombre, "apellidos": "Gil"},
        headers=headers,
    ).json()


def test_preinscrito_sin_seccion(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    sec_headers, anio_id, _seccion_id = _abrir_seccion(client)
    alumno = _alumno(client, sec_headers, "PN-20", "Mia")
    created = client.post(
        "/inscripciones",
        json={"alumno_id": alumno["alumno_id"], "anio_escolar_id": anio_id},
        headers=sec_headers,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["estado"] == "preinscrito"
    assert body["seccion_id"] is None
    assert body["estado_matricula"] == "pendiente"
    assert body["recaudos_pendientes"] is True


def test_sin_representante_no_cierra_inscripcion(
    client: TestClient, direccion: Usuario, secretaria: Usuario
) -> None:
    sec_headers, anio_id, seccion_id = _abrir_seccion(client)
    alumno = _alumno(client, sec_headers, "PN-21", "Leo")
    ins = client.post(
        "/inscripciones",
        json={"alumno_id": alumno["alumno_id"], "anio_escolar_id": anio_id},
        headers=sec_headers,
    ).json()
    assigned = client.post(
        f"/inscripciones/{ins['id']}/seccion",
        json={"seccion_id": seccion_id},
        headers=sec_headers,
    )
    assert assigned.status_code == 409
    assert assigned.json()["detail"] == "Sin representante principal"


def test_con_representante_queda_inscrito_aunque_falten_recaudos(
    client: TestClient, direccion: Usuario, secretaria: Usuario
) -> None:
    sec_headers, anio_id, seccion_id = _abrir_seccion(client)
    alumno = _alumno(client, sec_headers, "PN-22", "Eva")
    created_rep = client.post(
        "/personas/representantes",
        json={
            "tipo_doc": "cedula_v",
            "numero_doc": "16555222",
            "nombres": "Carla",
            "apellidos": "Gil",
            "email": "carla2@mail.com",
            "password": "clave123",
            "alumno_id": alumno["alumno_id"],
            "parentesco": "madre",
            "es_principal": True,
        },
        headers=sec_headers,
    )
    assert created_rep.status_code == 201
    ins = client.post(
        "/inscripciones",
        json={"alumno_id": alumno["alumno_id"], "anio_escolar_id": anio_id},
        headers=sec_headers,
    ).json()
    assigned = client.post(
        f"/inscripciones/{ins['id']}/seccion",
        json={"seccion_id": seccion_id},
        headers=sec_headers,
    )
    assert assigned.status_code == 200
    body = assigned.json()
    assert body["estado"] == "inscrito"
    assert body["seccion_id"] == seccion_id
    assert body["recaudos_pendientes"] is True
    pupilos = client.get("/inscripciones/mias", headers=_auth(client, "carla2@mail.com"))
    assert pupilos.status_code == 200
    assert pupilos.json()[0]["id"] == ins["id"]


def test_un_alumno_una_inscripcion_por_anio(
    client: TestClient, direccion: Usuario, secretaria: Usuario
) -> None:
    sec_headers, anio_id, _seccion_id = _abrir_seccion(client)
    alumno = _alumno(client, sec_headers, "PN-23", "Nico")
    first = client.post(
        "/inscripciones",
        json={"alumno_id": alumno["alumno_id"], "anio_escolar_id": anio_id},
        headers=sec_headers,
    )
    assert first.status_code == 201
    second = client.post(
        "/inscripciones",
        json={"alumno_id": alumno["alumno_id"], "anio_escolar_id": anio_id},
        headers=sec_headers,
    )
    assert second.status_code == 409


def test_colegio_b_no_ve_inscripcion_de_a(
    client: TestClient, direccion: Usuario, secretaria: Usuario, secretaria_b: Usuario
) -> None:
    sec_headers, anio_id, _seccion_id = _abrir_seccion(client)
    alumno = _alumno(client, sec_headers, "PN-24", "Ana")
    client.post(
        "/inscripciones",
        json={"alumno_id": alumno["alumno_id"], "anio_escolar_id": anio_id},
        headers=sec_headers,
    )
    listed = client.get("/inscripciones", headers=_auth(client, "secretaria@b.edu"))
    assert listed.status_code == 200
    assert listed.json() == []


def test_activar_retirar_y_recaudo(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    sec_headers, anio_id, seccion_id = _abrir_seccion(client)
    alumno = _alumno(client, sec_headers, "PN-26", "Sol")
    client.post(
        "/personas/representantes",
        json={
            "tipo_doc": "cedula_v",
            "numero_doc": "16555444",
            "nombres": "Ana",
            "apellidos": "Gil",
            "email": "ana-ins@mail.com",
            "password": "clave123",
            "alumno_id": alumno["alumno_id"],
            "parentesco": "madre",
            "es_principal": True,
        },
        headers=sec_headers,
    )
    ins = client.post(
        "/inscripciones",
        json={"alumno_id": alumno["alumno_id"], "anio_escolar_id": anio_id},
        headers=sec_headers,
    ).json()
    client.post(f"/inscripciones/{ins['id']}/seccion", json={"seccion_id": seccion_id}, headers=sec_headers)
    recaudo = client.patch(
        f"/inscripciones/{ins['id']}/recaudos",
        json={"tipo": "partida", "estado": "entregado"},
        headers=sec_headers,
    )
    assert recaudo.status_code == 200
    assert recaudo.json()["recaudos_pendientes"] is True
    assert any(r["tipo"] == "partida" and r["estado"] == "entregado" for r in recaudo.json()["recaudos"])
    too_soon = client.post(f"/inscripciones/{ins['id']}/activar", headers=sec_headers)
    # already inscrito with seccion — activar should work
    assert too_soon.status_code == 200
    assert too_soon.json()["estado"] == "activo"
    withdrawn = client.post(f"/inscripciones/{ins['id']}/retirar", headers=sec_headers)
    assert withdrawn.status_code == 200
    assert withdrawn.json()["estado"] == "retirado"


def test_representante_no_asigna_seccion(
    client: TestClient, direccion: Usuario, secretaria: Usuario
) -> None:
    sec_headers, anio_id, seccion_id = _abrir_seccion(client)
    alumno = _alumno(client, sec_headers, "PN-25", "Luz")
    client.post(
        "/personas/representantes",
        json={
            "tipo_doc": "cedula_v",
            "numero_doc": "16555333",
            "nombres": "Rosa",
            "apellidos": "Gil",
            "email": "rosa@mail.com",
            "password": "clave123",
            "alumno_id": alumno["alumno_id"],
            "parentesco": "madre",
            "es_principal": True,
        },
        headers=sec_headers,
    )
    ins = client.post(
        "/inscripciones",
        json={"alumno_id": alumno["alumno_id"], "anio_escolar_id": anio_id},
        headers=sec_headers,
    ).json()
    forbidden = client.post(
        f"/inscripciones/{ins['id']}/seccion",
        json={"seccion_id": seccion_id},
        headers=_auth(client, "rosa@mail.com"),
    )
    assert forbidden.status_code == 403

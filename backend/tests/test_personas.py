from fastapi.testclient import TestClient

from app.models.usuario import Usuario


def _auth(client: TestClient, email: str) -> dict[str, str]:
    login = client.post("/auth/login", json={"email": email, "password": "clave123"}).json()
    token = login["access_token"]
    if login["membresias"] and (login.get("membresias")):
        selected = client.post(
            "/auth/seleccionar",
            json={
                "organizacion_id": login["membresias"][0]["organizacion_id"],
                "rol": login["membresias"][0]["rol"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        token = selected.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_crear_alumno_sin_usuario(client: TestClient, secretaria: Usuario) -> None:
    headers = _auth(client, "secretaria@a.edu")
    response = client.post(
        "/personas/alumnos",
        json={
            "tipo_doc": "partida",
            "numero_doc": "PN-001",
            "nombres": "Mateo",
            "apellidos": "Rivas",
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["nombres"] == "Mateo"
    assert body["es_alumno"] is True
    assert body["usuario_id"] is None


def test_catalogo_docente(client: TestClient, secretaria: Usuario, direccion: Usuario) -> None:
    headers = _auth(client, "secretaria@a.edu")
    created = client.post(
        "/personas/docentes",
        json={
            "tipo_doc": "cedula_v",
            "numero_doc": "14555111",
            "nombres": "Luis",
            "apellidos": "Mora",
            "email": "luis.mora@a.edu",
            "password": "clave123",
        },
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["es_trabajador"] is True
    listed = client.get("/evaluacion/docentes", headers=_auth(client, "dir@a.edu"))
    assert listed.status_code == 200
    assert listed.json()[0]["nombres"] == "Luis"
    assert listed.json()[0]["email"] == "luis.mora@a.edu"
    login = client.post("/auth/login", json={"email": "luis.mora@a.edu", "password": "clave123"})
    assert login.status_code == 200
    gone = client.delete(f"/personas/{created.json()['id']}", headers=headers)
    assert gone.status_code == 204


def test_edita_y_borra_alumno_sin_cupo(client: TestClient, secretaria: Usuario) -> None:
    headers = _auth(client, "secretaria@a.edu")
    created = client.post(
        "/personas/alumnos",
        json={"tipo_doc": "partida", "numero_doc": "PN-010", "nombres": "Mia", "apellidos": "Gil"},
        headers=headers,
    )
    assert created.status_code == 201
    patched = client.patch(
        f"/personas/{created.json()['id']}",
        json={"tipo_doc": "partida", "numero_doc": "PN-011", "nombres": "Mia", "apellidos": "Rivas"},
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["apellidos"] == "Rivas"
    assert patched.json()["numero_doc"] == "PN-011"
    gone = client.delete(f"/personas/{created.json()['id']}", headers=headers)
    assert gone.status_code == 204


def test_partida_permite_inscripcion_sin_cedula(client: TestClient, secretaria: Usuario) -> None:
    headers = _auth(client, "secretaria@a.edu")
    response = client.post(
        "/personas/alumnos",
        json={
            "tipo_doc": "partida",
            "numero_doc": "PN-002",
            "nombres": "Eva",
            "apellidos": "Rivas",
        },
        headers=headers,
    )
    assert response.status_code == 201

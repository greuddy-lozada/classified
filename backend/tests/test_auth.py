from fastapi.testclient import TestClient

from app.models.usuario import Usuario


def test_login_ok(client: TestClient, secretaria: Usuario) -> None:
    response = client.post("/auth/login", json={"email": "secretaria@a.edu", "password": "clave123"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert len(body["membresias"]) == 1
    assert body["membresias"][0]["rol"] == "secretaria"


def test_login_clave_mala(client: TestClient, secretaria: Usuario) -> None:
    response = client.post("/auth/login", json={"email": "secretaria@a.edu", "password": "no"})
    assert response.status_code == 401


def test_me_requiere_token(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401


def test_me_con_token(client: TestClient, secretaria: Usuario) -> None:
    login = client.post("/auth/login", json={"email": "secretaria@a.edu", "password": "clave123"}).json()
    org_id = login["membresias"][0]["organizacion_id"]
    selected = client.post(
        "/auth/seleccionar",
        json={"organizacion_id": org_id, "rol": "secretaria"},
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert selected.status_code == 200
    token = selected.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "secretaria@a.edu"
    assert me.json()["rol"] == "secretaria"

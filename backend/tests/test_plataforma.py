from fastapi.testclient import TestClient

from app.models.usuario import Usuario


def _token(client: TestClient, email: str) -> str:
    return client.post("/auth/login", json={"email": email, "password": "clave123"}).json()["access_token"]


def test_secretaria_no_crea_colegio(client: TestClient, secretaria: Usuario) -> None:
    token = _token(client, "secretaria@a.edu")
    response = client.post(
        "/plataforma/organizaciones",
        json={
            "nombre": "Colegio B",
            "rif": "J-222",
            "admin_email": "dir@b.edu",
            "admin_password": "clave123",
            "admin_nombres": "Luis",
            "admin_apellidos": "Perez",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_plataforma_crea_colegio_y_admin(client: TestClient, plataforma: Usuario) -> None:
    token = _token(client, "ops@classified.app")
    response = client.post(
        "/plataforma/organizaciones",
        json={
            "nombre": "Colegio B",
            "rif": "J-222",
            "admin_email": "dir@b.edu",
            "admin_password": "clave123",
            "admin_nombres": "Luis",
            "admin_apellidos": "Perez",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["nombre"] == "Colegio B"
    login = client.post("/auth/login", json={"email": "dir@b.edu", "password": "clave123"})
    assert login.status_code == 200
    assert login.json()["membresias"][0]["rol"] == "direccion"

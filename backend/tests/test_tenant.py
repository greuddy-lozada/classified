from fastapi.testclient import TestClient

from app.models.usuario import Usuario
from tests.test_personas import _auth


def test_colegio_b_no_ve_ficha_de_a(
    client: TestClient,
    secretaria: Usuario,
    secretaria_b: Usuario,
) -> None:
    created = client.post(
        "/personas/alumnos",
        json={
            "tipo_doc": "cedula_v",
            "numero_doc": "10999888",
            "nombres": "Ana",
            "apellidos": "Diaz",
        },
        headers=_auth(client, "secretaria@a.edu"),
    )
    assert created.status_code == 201
    persona_id = created.json()["id"]
    listed_b = client.get("/personas", headers=_auth(client, "secretaria@b.edu"))
    assert listed_b.status_code == 200
    assert listed_b.json() == []
    stolen = client.get(f"/personas/{persona_id}", headers=_auth(client, "secretaria@b.edu"))
    assert stolen.status_code == 404

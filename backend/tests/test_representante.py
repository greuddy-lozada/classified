from fastapi.testclient import TestClient

from app.models.usuario import Usuario
from tests.test_personas import _auth


def test_representante_solo_ve_sus_pupilos(client: TestClient, secretaria: Usuario) -> None:
    headers = _auth(client, "secretaria@a.edu")
    alumno = client.post(
        "/personas/alumnos",
        json={"tipo_doc": "partida", "numero_doc": "PN-10", "nombres": "Mia", "apellidos": "Gil"},
        headers=headers,
    ).json()
    otro = client.post(
        "/personas/alumnos",
        json={"tipo_doc": "partida", "numero_doc": "PN-11", "nombres": "Leo", "apellidos": "Gil"},
        headers=headers,
    ).json()
    created = client.post(
        "/personas/representantes",
        json={
            "tipo_doc": "cedula_v",
            "numero_doc": "16555111",
            "nombres": "Carla",
            "apellidos": "Gil",
            "email": "carla@mail.com",
            "password": "clave123",
            "alumno_id": alumno["alumno_id"],
            "parentesco": "madre",
            "es_principal": True,
        },
        headers=headers,
    )
    assert created.status_code == 201
    pupilos = client.get("/personas/mis-pupilos", headers=_auth(client, "carla@mail.com"))
    assert pupilos.status_code == 200
    ids = {p["id"] for p in pupilos.json()}
    assert alumno["id"] in ids
    assert otro["id"] not in ids

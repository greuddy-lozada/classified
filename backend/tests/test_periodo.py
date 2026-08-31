from fastapi.testclient import TestClient

from app.models.usuario import Usuario
from tests.test_personas import _auth


def test_crear_anio_trae_tres_lapsos(client: TestClient, direccion: Usuario) -> None:
    headers = _auth(client, "dir@a.edu")
    response = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["nombre"] == "2026-2027"
    assert body["activo"] is True
    assert [l["numero"] for l in body["lapsos"]] == [1, 2, 3]
    assert [l["cerrado"] for l in body["lapsos"]] == [False, False, False]


def test_secretaria_no_crea_anio(client: TestClient, secretaria: Usuario) -> None:
    headers = _auth(client, "secretaria@a.edu")
    response = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers)
    assert response.status_code == 403


def test_colegio_b_no_ve_anio_de_a(
    client: TestClient, direccion: Usuario, secretaria_b: Usuario
) -> None:
    created = client.post(
        "/periodo/anios",
        json={"nombre": "2026-2027"},
        headers=_auth(client, "dir@a.edu"),
    )
    assert created.status_code == 201
    listed = client.get("/periodo/anios", headers=_auth(client, "secretaria@b.edu"))
    assert listed.status_code == 200
    assert listed.json() == []


def test_grado_media_usa_esquema_numerico(client: TestClient, direccion: Usuario) -> None:
    headers = _auth(client, "dir@a.edu")
    anio = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers).json()
    grado = client.post(
        "/periodo/grados",
        json={"anio_escolar_id": anio["id"], "nivel": "media", "nombre": "3er año"},
        headers=headers,
    )
    assert grado.status_code == 201
    assert grado.json()["esquema_evaluacion"] == "numerico"
    assert grado.json()["nivel"] == "media"


def test_grado_inicial_usa_informe(client: TestClient, direccion: Usuario) -> None:
    headers = _auth(client, "dir@a.edu")
    anio = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers).json()
    grado = client.post(
        "/periodo/grados",
        json={"anio_escolar_id": anio["id"], "nivel": "inicial", "nombre": "3er nivel"},
        headers=headers,
    )
    assert grado.status_code == 201
    assert grado.json()["esquema_evaluacion"] == "informe"


def test_primaria_puede_elegir_esquema(client: TestClient, direccion: Usuario) -> None:
    headers = _auth(client, "dir@a.edu")
    anio = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers).json()
    grado = client.post(
        "/periodo/grados",
        json={
            "anio_escolar_id": anio["id"],
            "nivel": "primaria",
            "nombre": "6°",
            "esquema_evaluacion": "numerico",
        },
        headers=headers,
    )
    assert grado.status_code == 201
    assert grado.json()["esquema_evaluacion"] == "numerico"


def test_crear_seccion_y_listar(client: TestClient, direccion: Usuario) -> None:
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
    )
    assert seccion.status_code == 201
    listed = client.get(f"/periodo/grados?anio_escolar_id={anio['id']}", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["secciones"][0]["letra"] == "A"
    assert listed.json()[0]["secciones"][0]["turno"] == "manana"


def test_no_usa_grado_de_otro_colegio(
    client: TestClient, direccion: Usuario, secretaria_b: Usuario
) -> None:
    headers_a = _auth(client, "dir@a.edu")
    anio = client.post("/periodo/anios", json={"nombre": "2026-2027"}, headers=headers_a).json()
    client.post(
        "/periodo/grados",
        json={"anio_escolar_id": anio["id"], "nivel": "media", "nombre": "1er año"},
        headers=headers_a,
    )
    stolen = client.get(
        f"/periodo/grados?anio_escolar_id={anio['id']}",
        headers=_auth(client, "secretaria@b.edu"),
    )
    assert stolen.status_code == 404

from fastapi.testclient import TestClient

from app.models.usuario import Usuario
from tests.test_evaluacion import _media_inscrito
from tests.test_personas import _auth


def _generar(client: TestClient, ctx: dict, periodos: list[str] | None = None):
    return client.post(
        "/cobro/generar",
        json={"anio_escolar_id": ctx["anio"]["id"], "periodos": periodos or ["2026-09", "2026-10"]},
        headers=ctx["sec"],
    )


def test_generar_matricula_y_meses(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    ctx = _media_inscrito(client)
    first = _generar(client, ctx)
    assert first.status_code == 200
    body = first.json()
    assert len(body) == 3
    tipos = sorted(c["tipo"] for c in body)
    assert tipos == ["matricula", "mensualidad", "mensualidad"]
    second = _generar(client, ctx)
    assert second.status_code == 200
    assert second.json() == []


def test_marcar_pago_y_representante_ve(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    ctx = _media_inscrito(client)
    cargos = _generar(client, ctx).json()
    mensual = next(c for c in cargos if c["periodo"] == "2026-10")
    paid = client.patch(
        f"/cobro/{mensual['id']}",
        json={"estado": "pagada", "fecha_pago": "2026-10-05", "nota": "transferencia"},
        headers=ctx["sec"],
    )
    assert paid.status_code == 200
    assert paid.json()["estado"] == "pagada"
    assert paid.json()["fecha_pago"] == "2026-10-05"
    assert paid.json()["nota"] == "transferencia"
    mios = client.get("/cobro/mios", headers=_auth(client, "carla-ev@mail.com"))
    assert mios.status_code == 200
    octu = next(c for c in mios.json() if c["periodo"] == "2026-10")
    assert octu["estado"] == "pagada"
    matricula = next(c for c in cargos if c["tipo"] == "matricula")
    client.patch(f"/cobro/{matricula['id']}", json={"estado": "pagada", "nota": "efectivo"}, headers=ctx["sec"])
    ins = client.get("/inscripciones", headers=ctx["sec"]).json()
    assert ins[0]["estado_matricula"] == "pagada"


def test_representante_no_marca(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    ctx = _media_inscrito(client)
    cargo = _generar(client, ctx, ["2026-09"]).json()[0]
    forbidden = client.patch(
        f"/cobro/{cargo['id']}",
        json={"estado": "pagada"},
        headers=_auth(client, "carla-ev@mail.com"),
    )
    assert forbidden.status_code == 403


def test_retirado_no_genera(client: TestClient, direccion: Usuario, secretaria: Usuario) -> None:
    ctx = _media_inscrito(client)
    client.post(f"/inscripciones/{ctx['ins']['id']}/retirar", headers=ctx["sec"])
    created = _generar(client, ctx)
    assert created.status_code == 200
    assert created.json() == []


def test_colegio_b_no_ve_cargos(
    client: TestClient, direccion: Usuario, secretaria: Usuario, secretaria_b: Usuario
) -> None:
    ctx = _media_inscrito(client)
    _generar(client, ctx)
    listed = client.get("/cobro", headers=_auth(client, "secretaria@b.edu"))
    assert listed.status_code == 200
    assert listed.json() == []

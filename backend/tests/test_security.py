from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_password_roundtrip() -> None:
    hashed = hash_password("secreto")
    assert hashed != "secreto"
    assert verify_password("secreto", hashed)
    assert not verify_password("otra", hashed)


def test_access_token_claims() -> None:
    token = create_access_token(
        sub="11111111-1111-1111-1111-111111111111",
        org_id="22222222-2222-2222-2222-222222222222",
        rol="secretaria",
        es_plataforma=False,
    )
    payload = decode_token(token)
    assert payload["sub"] == "11111111-1111-1111-1111-111111111111"
    assert payload["org_id"] == "22222222-2222-2222-2222-222222222222"
    assert payload["rol"] == "secretaria"
    assert payload["es_plataforma"] is False
    assert payload["typ"] == "access"

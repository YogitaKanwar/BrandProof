"""Exercise the single-origin package and hosted database URL compatibility."""

import pytest
from brandproof.db import make_engine
from brandproof.main import create_app
from fastapi.testclient import TestClient
from pydantic import ValidationError


def test_built_ui_and_real_api_share_origin_without_exposing_private_files(tmp_path, monkeypatch):
    public = tmp_path / "dist"
    public.mkdir()
    (public / "index.html").write_text('<div id="root">Built BrandProof</div>')
    (public / "assets").mkdir()
    (public / "assets" / "app.js").write_text("console.log('built')")
    (tmp_path / ".env").write_text("PRIVATE=not-public")
    monkeypatch.setenv("BRANDPROOF_FRONTEND_DIST", str(public))
    with TestClient(create_app(database_url=f"sqlite:///{tmp_path / 'api.db'}")) as client:
        assert "Built BrandProof" in client.get("/").text
        assert client.get("/assets/app.js").status_code == 200
        assert client.get("/api/v1/health").json()["database"] == "ok"
        assert client.get("/api/v1/campaigns").status_code == 401
        for path in ["/.env", "/api/v1/missing", "/backend/brandproof/config.py"]:
            response = client.get(path)
            assert response.status_code == 404
            assert "Built BrandProof" not in response.text
        created = client.post("/api/v1/demo-sessions").json()
        resumed = client.post(
            "/api/v1/demo-sessions/resume", headers={"X-BrandProof-Session": "resume"}
        )
        assert resumed.status_code == 200
        assert resumed.json() == created


def test_configured_frontend_requires_an_actual_build(tmp_path, monkeypatch):
    monkeypatch.setenv("BRANDPROOF_FRONTEND_DIST", str(tmp_path / "missing"))
    with pytest.raises(RuntimeError, match="built index.html"):
        create_app(database_url="sqlite:///:memory:")


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+psycopg"])
def test_hosted_postgres_urls_use_installed_driver_without_connecting(scheme):
    engine = make_engine(f"{scheme}://demo:password@localhost/brandproof?sslmode=require")
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
        assert engine.url.query["sslmode"] == "require"
    finally:
        engine.dispose()


@pytest.mark.parametrize("endpoint", ["/api/v1/demo-sessions", "/api/v1/demo-sessions/resume"])
def test_render_https_origin_works_behind_http_proxy_without_trusting_headers(
    tmp_path, monkeypatch, endpoint
):
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://brandproof-example.onrender.com")
    monkeypatch.setenv("BRANDPROOF_CORS_ORIGINS", "[]")
    with TestClient(create_app(database_url=f"sqlite:///{tmp_path / 'proxy.db'}")) as client:
        created = client.post(
            "/api/v1/demo-sessions",
            headers={"Origin": "https://brandproof-example.onrender.com"},
        )
        assert created.status_code == 201
        response = client.post(
            endpoint,
            headers={
                "Origin": "https://brandproof-example.onrender.com",
                "X-BrandProof-Session": "resume",
            },
        )
        assert response.status_code == (201 if endpoint.endswith("sessions") else 200)
        forged = client.post(
            endpoint,
            headers={
                "Origin": "https://attacker.example",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "attacker.example",
                "X-BrandProof-Session": "resume",
            },
        )
        assert forged.status_code == 403


def test_explicit_public_origin_takes_priority_over_platform_url(monkeypatch):
    from brandproof.config import Settings

    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://original.onrender.com")
    monkeypatch.setenv("BRANDPROOF_PUBLIC_ORIGIN", "https://custom.example/")
    assert Settings().public_origin == "https://custom.example"


@pytest.mark.parametrize(
    "value",
    [
        "*",
        "null",
        "https://*.example.com",
        "https://user:password@example.com",
        "https://example.com/path",
        "https://example.com?query=1",
        "https://example.com#fragment",
    ],
)
def test_public_origin_rejects_non_origins(monkeypatch, value):
    from brandproof.config import Settings

    monkeypatch.setenv("BRANDPROOF_PUBLIC_ORIGIN", value)
    with pytest.raises(ValidationError):
        Settings()


def test_unconfigured_tls_origin_is_not_inferred_from_forwarded_headers(client):
    response = client.post(
        "/api/v1/demo-sessions",
        headers={
            "Origin": "https://attacker.example",
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Host": "attacker.example",
        },
    )
    assert response.status_code == 403

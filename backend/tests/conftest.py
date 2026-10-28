import pytest
from brandproof.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def offline_provider_environment(monkeypatch):
    import httpx

    def blocked(*args, **kwargs):
        raise RuntimeError("Network access is disabled in tests; use an explicit MockTransport")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked)
    # Tests must not read local .env files, including credentials or cookie overrides.
    from brandproof.config import Settings

    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("BRANDPROOF_DEMO_COOKIE_SECURE", "false")
    # Real credentials may exist locally. Only explicit MockTransport tests opt in.
    for key, value in {
        "BRANDPROOF_AI_PROVIDER": "none",
        "BRANDPROOF_AI_MODEL": "",
        "BRANDPROOF_AI_API_KEY": "",
        "BRANDPROOF_EXTERNAL_AI_ENABLED": "false",
    }.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(database_url=f"sqlite:///{tmp_path / 'api.db'}")) as client:
        yield client


@pytest.fixture
def demo(client):
    response = client.post("/api/v1/demo-sessions")
    assert response.status_code == 201, response.text
    return response.json()


def headers(demo, role="owner"):
    return {"Authorization": f"Bearer {demo['actors'][role]['access_token']}"}


@pytest.fixture
def owner(demo):
    return headers(demo)


@pytest.fixture
def campaign(client, owner):
    response = client.post(
        "/api/v1/campaigns",
        headers=owner,
        json={"name": "Workshop campaign", "publication_date": "2026-11-12"},
    )
    assert response.status_code == 201, response.text
    return response.json()

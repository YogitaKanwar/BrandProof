import pytest
from brandproof.main import create_app
from fastapi.testclient import TestClient


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

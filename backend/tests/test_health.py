from brandproof.main import create_app
from fastapi.testclient import TestClient


def test_health_checks_a_real_database(tmp_path):
    app = create_app(database_url=f"sqlite:///{tmp_path / 'test.db'}")
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "version": "0.1.0"}

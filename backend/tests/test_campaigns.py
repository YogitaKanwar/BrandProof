from brandproof.main import create_app
from fastapi.testclient import TestClient


def test_campaign_persists_after_restarting_app(tmp_path):
    url = f"sqlite:///{tmp_path / 'persistent.db'}"
    with TestClient(create_app(database_url=url)) as client:
        response = client.post("/api/v1/demo-sessions")
        assert response.status_code == 201
        demo = response.json()
        auth = {"Authorization": f"Bearer {demo['actors']['owner']['access_token']}"}
        response = client.post(
            "/api/v1/campaigns",
            headers=auth,
            json={"name": "Launch", "publication_date": "2026-11-12"},
        )
        assert response.status_code == 201, response.text
        campaign = response.json()
    with TestClient(create_app(database_url=url)) as restarted:
        response = restarted.get(f"/api/v1/campaigns/{campaign['id']}", headers=auth)
        assert response.status_code == 200
        assert response.json()["name"] == "Launch"
        assert response.json()["publication_date"] == "2026-11-12"
        assert response.json()["workspace_id"] == demo["workspace_id"]

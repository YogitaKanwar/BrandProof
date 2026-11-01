from datetime import timedelta

import pytest
from brandproof.demo_cleanup import cleanup_expired
from brandproof.demo_session_models import DemoBrowserSession
from brandproof.main import create_app
from brandproof.models import Actor, Campaign, Workspace, utcnow
from conftest import headers
from fastapi.testclient import TestClient
from sqlalchemy import select, update

BASE = "/api/v1/demo-sessions"
ACTION = {"X-BrandProof-Session": "resume"}


def test_logout_revokes_every_bearer_and_recovery_cookie_without_erasing_history(
    client, demo, campaign
):
    cookie = client.cookies.get("brandproof_demo_session")
    response = client.post(BASE + "/logout", headers={**ACTION, **headers(demo, "creator")})
    assert response.status_code == 200
    assert response.json() == {"logged_out": True}
    assert response.headers["cache-control"] == "no-store"
    assert client.cookies.get("brandproof_demo_session") is None
    for role in ("owner", "creator", "reviewer"):
        assert client.get("/api/v1/campaigns", headers=headers(demo, role)).status_code == 401
    client.cookies.set("brandproof_demo_session", cookie, domain="testserver.local", path=BASE)
    assert client.post(BASE + "/resume", headers=ACTION).status_code == 401
    with client.app.state.sessions() as session:
        assert session.get(Campaign, campaign["id"]) is not None
        assert len(session.scalars(select(Actor)).all()) == 3


def test_logout_supports_blocked_cookie_and_is_idempotent(client, demo):
    client.cookies.clear()
    for _ in range(2):
        assert client.post(BASE + "/logout", headers={**ACTION, **headers(demo)}).status_code == 200
    assert client.get("/api/v1/campaigns", headers=headers(demo)).status_code == 401
    assert client.post(BASE + "/logout", headers=ACTION).status_code == 200


@pytest.mark.parametrize("endpoint", ["logout", "reset"])
@pytest.mark.parametrize(
    "unsafe",
    [{}, {**ACTION, "Origin": "https://evil.example"}, {**ACTION, "Sec-Fetch-Site": "cross-site"}],
)
def test_session_actions_reject_csrf_before_revocation(client, demo, endpoint, unsafe):
    assert client.post(BASE + "/" + endpoint, headers=unsafe).status_code == 403
    assert client.get("/api/v1/campaigns", headers=headers(demo)).status_code == 200


def test_reset_isolates_judges_and_revokes_old_roles(client, demo, campaign):
    cookie = client.cookies.get("brandproof_demo_session")
    other = client.post(BASE).json()
    client.cookies.clear()
    client.cookies.set("brandproof_demo_session", cookie, domain="testserver.local", path=BASE)
    response = client.post(BASE + "/reset", headers={**ACTION, **headers(demo)})
    assert response.status_code == 201
    replacement = response.json()
    assert replacement["workspace_id"] not in {demo["workspace_id"], other["workspace_id"]}
    resumed = client.post(BASE + "/resume", headers=ACTION)
    assert resumed.status_code == 200
    assert resumed.json()["workspace_id"] == replacement["workspace_id"]
    assert client.get("/api/v1/campaigns", headers=headers(replacement)).json() == []
    assert (
        client.get(f"/api/v1/campaigns/{campaign['id']}", headers=headers(replacement)).status_code
        == 404
    )
    for role in ("owner", "creator", "reviewer"):
        assert client.get("/api/v1/campaigns", headers=headers(demo, role)).status_code == 401
    assert client.get("/api/v1/campaigns", headers=headers(other)).status_code == 200
    with client.app.state.sessions() as session:
        assert session.get(Campaign, campaign["id"]) is not None


def test_foreign_bearer_cannot_revoke_cookie_workspace(client, demo):
    other = client.post(BASE).json()
    assert client.post(BASE + "/logout", headers={**ACTION, **headers(demo)}).status_code == 403
    for identity in (demo, other):
        assert client.get("/api/v1/campaigns", headers=headers(identity)).status_code == 200


def test_invalid_credentials_are_rejected_without_creating_workspace(client):
    assert (
        client.get(
            "/api/v1/campaigns", headers={"Authorization": "Bearer wrong-password"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            BASE + "/resume", headers={**ACTION, "Cookie": "brandproof_demo_session=forged"}
        ).status_code
        == 401
    )
    with client.app.state.sessions() as session:
        assert session.scalars(select(Workspace)).all() == []


def test_rate_limit_bounds_sessions_and_expensive_operations(monkeypatch, tmp_path):
    monkeypatch.setenv("BRANDPROOF_DEMO_SESSIONS_HOURLY_LIMIT", "2")
    monkeypatch.setenv("BRANDPROOF_DEMO_OPERATIONS_HOURLY_LIMIT", "1")
    with TestClient(create_app(database_url=f"sqlite:///{tmp_path / 'limits.db'}")) as client:
        demo = client.post(BASE).json()
        assert client.post(BASE).status_code == 201
        limited = client.post(BASE, headers={"X-Forwarded-For": "203.0.113.9"})
        assert limited.status_code == 429 and int(limited.headers["retry-after"]) > 0
        payload = {"name": "Demo", "publication_date": "2026-11-12"}
        assert (
            client.post("/api/v1/campaigns", headers=headers(demo), json=payload).status_code == 201
        )
        assert (
            client.post("/api/v1/campaigns", headers=headers(demo), json=payload).status_code == 429
        )
        # A crowded demo must still permit revocation.
        client.cookies.clear()
        assert client.post(BASE + "/logout", headers={**ACTION, **headers(demo)}).status_code == 200


def test_cleanup_dry_run_then_removes_only_expired_synthetic_data(client, demo, campaign, owner):
    # Include real source/content/review/audit descendants in the retention test.
    base = f"/api/v1/campaigns/{campaign['id']}"
    source = client.post(
        base + "/sources",
        headers=owner,
        json={
            "title": "Approved price",
            "rule": {"kind": "price", "amount": "899", "currency": "INR"},
        },
    ).json()
    assert (
        client.post(
            base + f"/sources/{source['id']}/confirm", headers=owner, json={"expected_version": 1}
        ).status_code
        == 200
    )
    assert (
        client.put(
            base + "/caption",
            headers=headers(demo, "creator"),
            json={"text": "Book for INR 599.", "expected_revision": 1},
        ).status_code
        == 200
    )
    latest = client.get(base, headers=owner).json()
    review = client.post(
        base + "/reviews",
        headers=headers(demo, "creator"),
        json={
            "expected_content_revision": latest["content_revision"],
            "expected_source_revision": latest["source_revision"],
            "external_ai_consent": False,
        },
    )
    assert review.status_code == 201
    assert any(
        f["evidence_status"] == "contradicted" and "899" in str(f["evidence"])
        for f in review.json()["findings"]
    )
    other = client.post(BASE).json()
    with client.app.state.sessions.begin() as session:
        private = Workspace()
        session.add(private)
        session.flush()
        private_id = private.id
        expired = utcnow() - timedelta(days=8)
        session.execute(
            update(Actor)
            .where(Actor.workspace_id == demo["workspace_id"])
            .values(expires_at=expired)
        )
        session.execute(
            update(DemoBrowserSession)
            .where(DemoBrowserSession.workspace_id == demo["workspace_id"])
            .values(expires_at=expired)
        )
    report = cleanup_expired(client.app.state.sessions)
    assert report["expired_workspaces"] == 1 and report["rows"]["review_runs"] == 1
    with client.app.state.sessions() as session:
        assert session.get(Campaign, campaign["id"]) is not None
    assert cleanup_expired(client.app.state.sessions, apply=True)["expired_workspaces"] == 1
    with client.app.state.sessions() as session:
        assert session.get(Workspace, demo["workspace_id"]) is None
        assert session.get(Workspace, private_id) is not None
        assert session.get(Workspace, other["workspace_id"]) is not None
    assert client.get("/api/v1/campaigns", headers=headers(other)).status_code == 200

import secrets
from datetime import UTC, datetime, timedelta

import pytest
from brandproof.demo_session_models import DemoBrowserSession
from brandproof.models import Actor
from conftest import headers
from fastapi.testclient import TestClient
from sqlalchemy import select

BASE = "/api/v1/demo-sessions"
COOKIE = "brandproof_demo_session"
RESUME_HEADERS = {"X-BrandProof-Session": "resume"}


def database_snapshot(client):
    with client.app.state.engine.connect() as connection:
        return "\n".join(connection.connection.driver_connection.iterdump())


@pytest.mark.parametrize("endpoint", [BASE, BASE + "/resume"])
@pytest.mark.parametrize(
    "unsafe_headers",
    [
        {"Origin": "https://attacker.example"},
        {"Origin": "null"},
        {"Origin": "http://localhost:5173.attacker.example"},
        {"Origin": "http://testserver/"},
        {"Sec-Fetch-Site": "cross-site"},
        {"Origin": "http://localhost:5173", "Sec-Fetch-Site": "cross-site"},
    ],
)
def test_unsafe_browser_context_rejected_before_writes_or_tokens(
    client, demo, endpoint, unsafe_headers
):
    before = database_snapshot(client)
    response = client.post(endpoint, headers={**RESUME_HEADERS, **unsafe_headers})
    assert response.status_code == 403
    assert "actors" not in response.json()
    assert "set-cookie" not in response.headers
    assert (
        "access-control-allow-origin" not in response.headers
        or response.headers["access-control-allow-origin"] == "http://localhost:5173"
    )
    assert database_snapshot(client) == before


@pytest.mark.parametrize("value", [None, "", "Resume", "resume, resume", "create", " resume"])
def test_resume_requires_exact_custom_header(client, demo, value):
    before = database_snapshot(client)
    response = client.post(
        BASE + "/resume", headers={} if value is None else {"X-BrandProof-Session": value}
    )
    assert response.status_code == 403
    assert database_snapshot(client) == before


@pytest.mark.parametrize("origin", ["http://testserver", "http://localhost:5173", None])
def test_trusted_origins_or_native_client_can_resume(client, demo, origin):
    request_headers = dict(RESUME_HEADERS)
    if origin:
        request_headers["Origin"] = origin
    response = client.post(BASE + "/resume", headers=request_headers)
    assert response.status_code == 200
    assert response.json() == demo


@pytest.mark.parametrize(
    "invalid",
    [None, "forged", "", "not a token", "é" * 43, "a" * 10000],
    ids=["missing", "forged", "empty", "spaces", "non-ascii", "oversized"],
)
def test_missing_forged_and_malformed_cookies_do_not_mutate_database(client, demo, invalid):
    client.cookies.clear()
    before = database_snapshot(client)
    request_headers = dict(RESUME_HEADERS)
    if invalid is not None:
        # HTTP permits latin-1 cookie octets; raw header avoids client cookie normalization.
        request_headers["Cookie"] = f"{COOKIE}={invalid}".encode("latin-1")
    response = client.post(BASE + "/resume", headers=request_headers)
    assert response.status_code == 401
    assert "actors" not in response.json()
    assert "set-cookie" not in response.headers
    assert database_snapshot(client) == before


def test_expired_cookie_does_not_create_or_extend_session(client, demo):
    with client.app.state.sessions() as session:
        row = session.get(DemoBrowserSession, demo["workspace_id"])
        row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()
    before = database_snapshot(client)
    response = client.post(BASE + "/resume", headers=RESUME_HEADERS)
    assert response.status_code == 401
    assert database_snapshot(client) == before


def actor_snapshot(client):
    with client.app.state.sessions() as session:
        return [
            (row.id, row.workspace_id, row.role, row.token_hash, row.expires_at)
            for row in session.scalars(select(Actor).order_by(Actor.id))
        ]


@pytest.mark.parametrize("role", ["owner", "creator", "reviewer"])
@pytest.mark.parametrize("damage", ["missing", "hash", "role", "expiry", "expired"])
def test_resume_rejects_inconsistent_actors_without_repair(client, demo, role, damage):
    with client.app.state.sessions() as session:
        row = session.scalar(
            select(Actor).where(Actor.workspace_id == demo["workspace_id"], Actor.role == role)
        )
        if damage == "missing":
            session.delete(row)
        elif damage == "hash":
            row.token_hash = "0" * 64
        elif damage == "role":
            row.role = "unknown"
        elif damage == "expiry":
            row.expires_at += timedelta(seconds=1)
        else:
            row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()
    before = database_snapshot(client)
    response = client.post(BASE + "/resume", headers=RESUME_HEADERS)
    assert response.status_code == 401
    assert database_snapshot(client) == before


def test_refresh_resumes_same_workspace_bearers_and_actor_ids(client, demo, owner, campaign):
    before = actor_snapshot(client)
    expected_campaigns = client.get("/api/v1/campaigns", headers=owner).json()
    assert [row["id"] for row in expected_campaigns] == [campaign["id"]]
    secret = client.cookies.get(COOKIE)
    assert secret is not None
    with TestClient(client.app) as refreshed:
        refreshed.cookies.set(COOKIE, secret)
        response = refreshed.post(BASE + "/resume", headers=RESUME_HEADERS)
        assert response.status_code == 200, response.text
        assert response.json() == demo
        assert (
            refreshed.get("/api/v1/campaigns", headers=headers(response.json())).json()
            == expected_campaigns
        )
        assert refreshed.get("/api/v1/campaigns").status_code == 401
    assert actor_snapshot(client) == before
    assert client.get("/api/v1/campaigns", headers=owner).json() == expected_campaigns


@pytest.mark.parametrize(
    ("endpoint", "request_headers", "clear_cookie", "status"),
    [
        (BASE, {}, False, 201),
        (BASE + "/resume", RESUME_HEADERS, False, 200),
        (BASE + "/resume", RESUME_HEADERS, True, 401),
        (BASE + "/resume", {}, False, 403),
        (BASE, {"Origin": "https://attacker.example"}, False, 403),
    ],
)
def test_session_responses_cannot_be_cached(
    client, demo, endpoint, request_headers, clear_cookie, status
):
    if clear_cookie:
        client.cookies.clear()
    response = client.post(endpoint, headers=request_headers)
    assert response.status_code == status
    assert response.headers.get("cache-control") == "no-store"
    assert response.headers.get("pragma") == "no-cache"


@pytest.mark.parametrize("endpoint", [BASE, BASE + "/resume"])
def test_allowed_frontend_can_send_credentialed_session_requests(client, demo, endpoint):
    origin = "http://localhost:5173"
    preflight = client.options(
        endpoint,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-BrandProof-Session",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == origin
    assert preflight.headers.get("access-control-allow-credentials") == "true"
    assert "x-brandproof-session" in preflight.headers["access-control-allow-headers"].lower()
    response = client.post(endpoint, headers={"Origin": origin, **RESUME_HEADERS})
    assert response.status_code == (201 if endpoint == BASE else 200)
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.parametrize("origin", ["*", "https://*.example.com", "null"])
def test_credentialed_cors_configuration_rejects_non_exact_origins(origin):
    from brandproof.config import Settings
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(_env_file=None, cors_origins=["https://brandproof.example", origin])


@pytest.mark.parametrize("secure", [True, False])
def test_cookie_flags_and_secure_default(monkeypatch, tmp_path, secure):
    from http.cookies import SimpleCookie

    from brandproof.main import create_app

    if secure:
        monkeypatch.delenv("BRANDPROOF_DEMO_COOKIE_SECURE", raising=False)
    else:
        monkeypatch.setenv("BRANDPROOF_DEMO_COOKIE_SECURE", "false")
    with TestClient(create_app(database_url=f"sqlite:///{tmp_path / 'flags.db'}")) as browser:
        response = browser.post(BASE)
        assert response.status_code == 201
        parsed = SimpleCookie()
        parsed.load(response.headers["set-cookie"])
        cookie = parsed[COOKIE]
        assert cookie["httponly"]
        assert bool(cookie["secure"]) is secure
        assert cookie["samesite"] == "strict"
        assert cookie["path"] == BASE
        assert cookie["max-age"] == "86400"
        assert cookie["domain"] == ""
        assert cookie.value not in response.text
        dump = database_snapshot(browser)
        assert cookie.value not in dump
        for actor in response.json()["actors"].values():
            assert actor["access_token"] not in dump


def test_resume_neither_rotates_cookie_nor_extends_expiry(client, demo):
    before = database_snapshot(client)
    secret = client.cookies.get(COOKIE)
    for _ in range(3):
        response = client.post(BASE + "/resume", headers=RESUME_HEADERS)
        assert response.status_code == 200
        assert response.json() == demo
        assert "set-cookie" not in response.headers
        assert client.cookies.get(COOKIE) == secret
    assert database_snapshot(client) == before


def test_valid_format_but_unknown_cookie_cannot_resume(client, demo):
    client.cookies.clear()
    client.cookies.set(COOKIE, secrets.token_urlsafe(32))
    before = database_snapshot(client)
    response = client.post(BASE + "/resume", headers=RESUME_HEADERS)
    assert response.status_code == 401
    assert database_snapshot(client) == before


def test_resuming_content_author_cannot_bypass_self_approval(client, demo, owner, campaign):
    from test_approval_guards import setup_request

    _, run, base, payload = setup_request(client, demo, owner, campaign)
    resumed = client.post(BASE + "/resume", headers=RESUME_HEADERS)
    assert resumed.status_code == 200
    response = client.post(
        f"{base}/reviews/{run['id']}/approvals", headers=headers(resumed.json()), json=payload
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "self_approval"


def test_concurrent_tabs_resume_without_changing_old_tab_identity(client, demo, owner, campaign):
    from concurrent.futures import ThreadPoolExecutor
    from contextlib import ExitStack

    before = database_snapshot(client)
    expected = client.get(f"/api/v1/campaigns/{campaign['id']}", headers=owner).json()
    secret = client.cookies.get(COOKIE)
    assert secret is not None
    with ExitStack() as stack:
        browsers = [stack.enter_context(TestClient(client.app)) for _ in range(4)]
        for browser in browsers:
            browser.cookies.set(COOKIE, secret)

        def resume(browser):
            response = browser.post(BASE + "/resume", headers=RESUME_HEADERS)
            return response.status_code == 200 and response.json() == demo

        with ThreadPoolExecutor(max_workers=4) as pool:
            assert all(pool.map(resume, browsers))
    assert database_snapshot(client) == before
    response = client.get(f"/api/v1/campaigns/{campaign['id']}", headers=owner)
    assert response.status_code == 200
    assert response.json() == expected


def test_new_app_restores_session_and_campaign_from_same_database(tmp_path):
    from brandproof.main import create_app

    database_url = f"sqlite:///{tmp_path / 'restart.db'}"
    with TestClient(create_app(database_url=database_url)) as original:
        created = original.post(BASE).json()
        secret = original.cookies.get(COOKIE)
        campaign_response = original.post(
            "/api/v1/campaigns",
            headers=headers(created),
            json={"name": "Restart continuity", "publication_date": "2026-11-12"},
        )
        assert campaign_response.status_code == 201
        saved = original.get(
            f"/api/v1/campaigns/{campaign_response.json()['id']}", headers=headers(created)
        ).json()
        before = actor_snapshot(original)
    with TestClient(create_app(database_url=database_url)) as restarted:
        assert secret is not None
        restarted.cookies.set(COOKIE, secret)
        response = restarted.post(BASE + "/resume", headers=RESUME_HEADERS)
        assert response.status_code == 200
        assert response.json() == created
        assert actor_snapshot(restarted) == before
        readback = restarted.get(
            f"/api/v1/campaigns/{saved['id']}", headers=headers(response.json())
        )
        assert readback.status_code == 200
        assert readback.json() == saved

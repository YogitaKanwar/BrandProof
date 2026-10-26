"""Provider admission is exercised with simulated HTTP, never live inference."""

import httpx
from test_contextual_integration import configured, start_current
from test_reviews import add_source, review_copy


def prepare(client, owner, campaign):
    add_source(client, owner, campaign, {"kind": "tone", "guidance": "Be respectful."})
    review_copy(client, owner, campaign, "Our workshop invitation")
    configured(client)
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [{"finish_reason": "stop", "message": {"content": '{"findings":[]}'}}]
            },
        )

    client.app.state.contextual_transport = httpx.MockTransport(handle)
    return calls


def test_workspace_budget_blocks_provider_and_preserves_exact_review(client, owner, campaign):
    calls = prepare(client, owner, campaign)
    client.app.state.settings.ai_workspace_hourly_limit = 1
    first = start_current(client, owner, campaign)
    assert first.status_code == 201, first.text
    assert len(calls) == 1
    denied = start_current(client, owner, campaign)
    assert denied.status_code == 201, denied.text
    assert len(calls) == 1
    assert denied.json()["checks"]["contextual"]["status"] == "unavailable"
    assert denied.json()["checks"]["contextual"]["reason"] == "workspace_hourly_limit"
    assert denied.json()["status"] == "partial"
    base = f"/api/v1/campaigns/{campaign['id']}"
    assert (
        client.get(base + "/reviews/" + denied.json()["id"], headers=owner).json()["checks"]
        == denied.json()["checks"]
    )


def test_global_budget_applies_across_fresh_demo_sessions(client, owner, campaign):
    from conftest import headers

    calls = prepare(client, owner, campaign)
    client.app.state.settings.ai_global_hourly_limit = 1
    assert start_current(client, owner, campaign).status_code == 201
    other_owner = headers(client.post("/api/v1/demo-sessions").json())
    other = client.post(
        "/api/v1/campaigns",
        headers=other_owner,
        json={"name": "Another fictional workspace", "publication_date": "2026-11-12"},
    ).json()
    add_source(client, other_owner, other, {"kind": "tone", "guidance": "Be calm."})
    review_copy(client, other_owner, other, "Another workshop invitation")
    denied = start_current(client, other_owner, other)
    assert denied.status_code == 201, denied.text
    assert denied.json()["checks"]["contextual"]["reason"] == "global_hourly_limit"
    assert len(calls) == 1


def test_disabled_or_unconsented_reviews_do_not_reserve_provider_budget(client, owner, campaign):
    from brandproof.quota import AIAdmission
    from sqlalchemy import func, select

    calls = prepare(client, owner, campaign)
    assert start_current(client, owner, campaign, consent=False).status_code == 201
    client.app.state.settings.external_ai_enabled = False
    assert start_current(client, owner, campaign).status_code == 201
    with client.app.state.sessions() as session:
        assert session.scalar(select(func.count()).select_from(AIAdmission)) == 0
    assert calls == []


def test_failed_provider_attempt_still_consumes_budget(client, owner, campaign):
    calls = prepare(client, owner, campaign)
    client.app.state.settings.ai_workspace_hourly_limit = 1

    def quota_failure(request):
        calls.append(request)
        return httpx.Response(429, json={"error": "provider quota exhausted"})

    client.app.state.contextual_transport = httpx.MockTransport(quota_failure)
    first = start_current(client, owner, campaign)
    assert first.status_code == 201
    assert first.json()["checks"]["contextual"]["status"] == "unavailable"
    denied = start_current(client, owner, campaign)
    assert denied.json()["checks"]["contextual"]["reason"] == "workspace_hourly_limit"
    assert len(calls) == 1


def test_concurrent_reviews_admit_only_one_workspace_provider_call(client, owner, campaign):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    calls = prepare(client, owner, campaign)
    entered, release = Event(), Event()

    def blocked(request):
        calls.append(request)
        entered.set()
        assert release.wait(8)
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"findings":[]}'}}]})

    client.app.state.contextual_transport = httpx.MockTransport(blocked)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(start_current, client, owner, campaign)
        assert entered.wait(8)
        try:
            second = pool.submit(start_current, client, owner, campaign).result(timeout=5)
            assert second.status_code == 201, second.text
            assert second.json()["checks"]["contextual"]["reason"] == "workspace_provider_busy"
            assert len(calls) == 1
        finally:
            release.set()
        assert first.result(timeout=8).status_code == 201


def test_budget_survives_app_recreation(client, owner, campaign):
    from brandproof.main import create_app
    from fastapi.testclient import TestClient

    calls = prepare(client, owner, campaign)
    assert start_current(client, owner, campaign).status_code == 201
    app = create_app(database_url=str(client.app.state.engine.url))
    with TestClient(app) as restarted:
        configured(restarted)
        restarted.app.state.settings.ai_workspace_hourly_limit = 1
        restarted.app.state.contextual_transport = client.app.state.contextual_transport
        denied = start_current(restarted, owner, campaign)
    assert denied.status_code == 201, denied.text
    assert denied.json()["checks"]["contextual"]["reason"] == "workspace_hourly_limit"
    assert len(calls) == 1


def test_old_reservation_rolls_out_of_hourly_budget(client, owner, campaign):
    from datetime import timedelta

    from brandproof.models import utcnow
    from brandproof.quota import AIAdmission
    from sqlalchemy import select

    calls = prepare(client, owner, campaign)
    client.app.state.settings.ai_workspace_hourly_limit = 1
    assert start_current(client, owner, campaign).status_code == 201
    with client.app.state.sessions() as session:
        row = session.scalar(select(AIAdmission))
        row.created_at = utcnow() - timedelta(hours=2)
        session.commit()
    allowed = start_current(client, owner, campaign)
    assert allowed.status_code == 201
    assert allowed.json()["checks"]["contextual"]["status"] == "completed"
    assert len(calls) == 2

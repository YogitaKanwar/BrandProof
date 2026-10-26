"""Independent operational edge checks. No real provider I/O."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import httpx
import pytest
from brandproof.config import Settings
from brandproof.quota import AIAdmission
from conftest import headers
from sqlalchemy import func, select
from test_ai_quota import prepare
from test_contextual_integration import start_current
from test_reviews import add_source, review_copy


@pytest.mark.parametrize(
    "field,reason",
    [
        ("ai_workspace_hourly_limit", "workspace_hourly_limit"),
        ("ai_global_hourly_limit", "global_hourly_limit"),
    ],
)
def test_zero_caps_fail_closed(client, owner, campaign, field, reason):
    calls = prepare(client, owner, campaign)
    setattr(client.app.state.settings, field, 0)
    response = start_current(client, owner, campaign)
    assert response.status_code == 201, response.text
    assert response.json()["checks"]["contextual"]["reason"] == reason
    assert response.json()["checks"]["contextual"]["status"] == "unavailable"
    assert response.json()["status"] == "partial"
    assert not calls
    with client.app.state.sessions() as session:
        assert session.scalar(select(func.count()).select_from(AIAdmission)) == 0


def new_campaign(client, owner):
    campaign = client.post(
        "/api/v1/campaigns",
        headers=owner,
        json={"name": "Independent fictional campaign", "publication_date": "2026-11-12"},
    ).json()
    add_source(client, owner, campaign, {"kind": "tone", "guidance": "Be respectful."})
    review_copy(client, owner, campaign, "Our workshop invitation")
    return campaign


def test_workspace_concurrency_spans_campaigns(client, owner, campaign):
    prepare(client, owner, campaign)
    other = new_campaign(client, owner)
    entered, release = Event(), Event()
    calls = []

    def handle(request):
        calls.append(request)
        entered.set()
        assert release.wait(8)
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"findings":[]}'}}]})

    client.app.state.contextual_transport = httpx.MockTransport(handle)
    with ThreadPoolExecutor(max_workers=2) as pool:
        running = pool.submit(start_current, client, owner, campaign)
        assert entered.wait(8)
        try:
            denied = start_current(client, owner, other)
            assert denied.status_code == 201, denied.text
            assert denied.json()["checks"]["contextual"]["reason"] == "workspace_provider_busy"
            assert len(calls) == 1
        finally:
            release.set()
        assert running.result(timeout=8).status_code == 201


def test_global_concurrency_spans_workspaces_and_releases(client, owner, campaign):
    prepare(client, owner, campaign)
    owners = [owner] + [headers(client.post("/api/v1/demo-sessions").json()) for _ in range(2)]
    campaigns = [campaign] + [new_campaign(client, other) for other in owners[1:]]
    entered = [Event(), Event()]
    release = Event()
    calls = []

    def handle(request):
        index = len(calls)
        calls.append(request)
        if index < 2:
            entered[index].set()
            assert release.wait(8)
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"findings":[]}'}}]})

    client.app.state.contextual_transport = httpx.MockTransport(handle)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = []
        try:
            for i in range(2):
                jobs.append(pool.submit(start_current, client, owners[i], campaigns[i]))
                assert entered[i].wait(8)
            denied = start_current(client, owners[2], campaigns[2])
            assert denied.status_code == 201, denied.text
            assert denied.json()["checks"]["contextual"]["reason"] == "global_provider_busy"
            assert len(calls) == 2
        finally:
            release.set()
        assert all(job.result(timeout=8).status_code == 201 for job in jobs)
    allowed = start_current(client, owners[2], campaigns[2])
    assert allowed.status_code == 201, allowed.text
    assert allowed.json()["checks"]["contextual"]["status"] == "completed"
    assert len(calls) == 3
    with client.app.state.sessions() as session:
        assert session.scalar(select(func.count()).select_from(AIAdmission)) == 3
        assert session.connection().exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_config_bounds_reject_invalid_caps():
    from pydantic import ValidationError

    for field in ["ai_workspace_hourly_limit", "ai_global_hourly_limit"]:
        for value in [-1, 10001, "NaN"]:
            with pytest.raises(ValidationError):
                Settings(_env_file=None, **{field: value})
    for field in ["ai_workspace_concurrency_limit", "ai_global_concurrency_limit"]:
        for value in [0, -1, 17, "NaN"]:
            with pytest.raises(ValidationError):
                Settings(_env_file=None, **{field: value})

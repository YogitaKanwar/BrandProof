"""Read-only review probes: isolated temporary test DBs, no network."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from conftest import headers
from test_approval_guards import setup_request
from test_reviews import add_source, review_copy
from test_workflow import expectation


def test_workspace_and_campaign_scope(client, demo, owner, campaign):
    _, run, base, approval = setup_request(client, demo, owner, campaign, "Join our workshop.")
    finding = run["findings"][0]
    foreign = headers(client.post("/api/v1/demo-sessions").json())
    decision = {
        **expectation(run),
        "expected_decision_version": 0,
        "decision": "exception",
        "reason": "Explicit isolated test exception.",
    }
    paths = [
        "/receipt",
        "/comments",
        "/revisions",
        f"/reviews/{run['id']}/findings/{finding['id']}/decisions",
    ]
    for path in paths:
        response = client.get(base + path, headers=foreign)
        assert response.status_code == 404, (path, response.text)
    posts = [
        ("/comments", {**expectation(run), "text": "Scoped comment."}),
        (f"/reviews/{run['id']}/requests", expectation(run)),
        (f"/reviews/{run['id']}/approvals", approval),
        (f"/reviews/{run['id']}/findings/{finding['id']}/decisions", decision),
        (f"/reviews/{run['id']}/findings/{finding['id']}/apply", expectation(run)),
    ]
    for path, payload in posts:
        response = client.post(base + path, headers=foreign, json=payload)
        assert response.status_code == 404, (path, response.text)
    second = client.post(
        "/api/v1/campaigns",
        headers=owner,
        json={"name": "Second", "publication_date": "2026-11-12"},
    ).json()
    second_base = f"/api/v1/campaigns/{second['id']}"
    second_expect = {"expected_content_revision": 1, "expected_source_revision": 0}
    for path, payload in posts:
        payload = {**payload, **second_expect}
        if path == "/comments":
            payload["review_id"] = run["id"]
        response = client.post(second_base + path, headers=owner, json=payload)
        assert response.status_code == 404, (path, response.text)


def test_exact_span_unicode_repeated_quote_and_mismatch(client, demo, owner, campaign):
    add_source(
        client, owner, campaign, {"kind": "terminology", "term": "cheap", "preferred": "affordable"}
    )
    run = review_copy(client, owner, campaign, "🎉 cheap! cheap.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    findings = run["findings"]
    assert len(findings) == 2
    response = client.post(
        f"{base}/reviews/{run['id']}/findings/{findings[1]['id']}/apply",
        headers=headers(demo, "creator"),
        json=expectation(run),
    )
    assert response.status_code == 200, response.text
    assert response.json()["caption"] == "🎉 cheap! affordable."
    from brandproof.review_models import ReviewRun

    current = response.json()
    run = client.post(
        base + "/reviews",
        headers=owner,
        json={
            "expected_content_revision": current["content_revision"],
            "expected_source_revision": current["source_revision"],
        },
    ).json()
    with client.app.state.sessions() as session:
        row = session.get(ReviewRun, run["id"])
        items = [dict(f) for f in row.findings]
        items[0] = {**items[0], "location": {**items[0]["location"], "quote": "WRONG"}}
        row.findings = items
        session.commit()
    response = client.post(
        f"{base}/reviews/{run['id']}/findings/{run['findings'][0]['id']}/apply",
        headers=headers(demo, "creator"),
        json=expectation(run),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "suggestion_conflict"
    assert client.get(base, headers=owner).json()["caption"] == "🎉 cheap! affordable."


def test_manual_coverage_requires_exact_incomplete_keys(client, demo, owner, campaign):
    _, run, base, payload = setup_request(client, demo, owner, campaign)
    from brandproof.review_models import ReviewRun

    with client.app.state.sessions() as session:
        row = session.get(ReviewRun, run["id"])
        row.checks = {**row.checks, "exact_text": {"status": "partial"}}
        session.commit()
    url = f"{base}/reviews/{run['id']}/approvals"
    notes = "Reviewer explicitly checked this incomplete category against approved sources."
    for keys in [[], ["contextual"], ["exact_text"], ["exact_text", "contextual", "poster"]]:
        response = client.post(
            url,
            headers=headers(demo, "reviewer"),
            json={**payload, "manual_checks": {key: notes for key in keys}},
        )
        assert response.status_code == 409, response.text
        assert response.json()["error"]["code"] == "checks_incomplete"
    response = client.post(
        url,
        headers=headers(demo, "reviewer"),
        json={
            **payload,
            "manual_checks": {
                key: notes for key in ["exact_text", "contextual", "advertising_risk"]
            },
        },
    )
    assert response.status_code == 201, response.text
    receipt = client.get(base + "/receipt", headers=owner).json()
    assert receipt["readiness"] == "approved_with_manual_checks"
    assert receipt["checks"]["exact_text"]["status"] == "partial"


def test_history_endpoints_append_only(client, demo, owner, campaign):
    _, run, base, payload = setup_request(client, demo, owner, campaign, "Join our workshop.")
    path = f"{base}/reviews/{run['id']}/findings/{run['findings'][0]['id']}/decisions"
    for version, choice in [(0, "exception"), (1, "reopen"), (2, "dismiss")]:
        response = client.post(
            path,
            headers=headers(demo, "reviewer"),
            json={
                **expectation(run),
                "expected_decision_version": version,
                "decision": choice,
                "reason": "Explicit immutable historical decision.",
            },
        )
        assert response.status_code == 201, response.text
    original = client.get(path, headers=owner).json()
    assert [row["version"] for row in original] == [1, 2, 3]
    comment = client.post(
        base + "/comments",
        headers=owner,
        json={**expectation(run), "text": "Original historical comment."},
    ).json()
    approval = client.post(
        f"{base}/reviews/{run['id']}/approvals", headers=headers(demo, "reviewer"), json=payload
    )
    assert approval.status_code == 201, approval.text
    for method in ["put", "patch", "delete"]:
        for target in [
            path,
            path + "/" + original[0]["id"],
            base + "/comments/" + comment["id"],
            f"{base}/reviews/{run['id']}/approvals",
        ]:
            response = getattr(client, method)(target, headers=owner)
            assert response.status_code in (404, 405), (method, target, response.text)
    assert client.get(path, headers=owner).json() == original
    assert client.get(base + "/comments", headers=owner).json() == [comment]
    assert (
        client.post(
            f"{base}/reviews/{run['id']}/approvals", headers=headers(demo, "reviewer"), json=payload
        ).status_code
        == 409
    )


@pytest.mark.parametrize("action", ["comment", "decision", "request", "approval", "suggestion"])
def test_waiting_write_refreshes_stale_campaign(client, demo, owner, campaign, monkeypatch, action):
    _, run, base, payload = setup_request(client, demo, owner, campaign, "Join our workshop.")
    import brandproof.approval as approval
    import brandproof.suggestions as suggestions
    import brandproof.workflow as workflow

    module = (
        approval if action == "approval" else suggestions if action == "suggestion" else workflow
    )
    original_lock = module.lock_campaign
    reached, release = Event(), Event()

    def delayed_lock(session, row):
        reached.set()
        assert release.wait(8)
        return original_lock(session, row)

    monkeypatch.setattr(module, "lock_campaign", delayed_lock)
    finding_path = f"{base}/reviews/{run['id']}/findings/{run['findings'][0]['id']}"
    actions = {
        "comment": (
            base + "/comments",
            {**expectation(run), "text": "An old snapshot comment."},
            headers(demo, "creator"),
        ),
        "decision": (
            finding_path + "/decisions",
            {
                **expectation(run),
                "expected_decision_version": 0,
                "decision": "exception",
                "reason": "Old snapshot decision must not persist.",
            },
            headers(demo, "reviewer"),
        ),
        "request": (
            f"{base}/reviews/{run['id']}/requests",
            expectation(run),
            headers(demo, "creator"),
        ),
        "approval": (f"{base}/reviews/{run['id']}/approvals", payload, headers(demo, "reviewer")),
        "suggestion": (finding_path + "/apply", expectation(run), headers(demo, "creator")),
    }
    path, data, auth = actions[action]
    with ThreadPoolExecutor(max_workers=1) as pool:
        waiting = pool.submit(client.post, path, headers=auth, json=data)
        assert reached.wait(8)
        try:
            changed = client.put(
                base + "/caption",
                headers=owner,
                json={
                    "expected_revision": run["content_revision"],
                    "text": "New snapshot. Terms apply.",
                },
            )
            assert changed.status_code == 200, changed.text
        finally:
            release.set()
        response = waiting.result(timeout=8)
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "version_conflict"
    receipt = client.get(base + "/receipt", headers=owner).json()
    assert receipt["approvals"] == []
    assert client.get(base + "/comments", headers=owner).json() == []


def test_previous_author_blocked_after_creator_revision(client, demo, owner, campaign):
    _, run, base, payload = setup_request(client, demo, owner, campaign)
    updated = client.put(
        base + "/caption",
        headers=headers(demo, "creator"),
        json={
            "expected_revision": run["content_revision"],
            "text": "Revised by creator. Terms apply.",
        },
    ).json()
    expect = {
        "expected_content_revision": updated["content_revision"],
        "expected_source_revision": updated["source_revision"],
    }
    run = client.post(base + "/reviews", headers=headers(demo, "creator"), json=expect).json()
    request = client.post(
        f"{base}/reviews/{run['id']}/requests", headers=headers(demo, "creator"), json=expect
    ).json()
    response = client.post(
        f"{base}/reviews/{run['id']}/approvals",
        headers=owner,
        json={**payload, **expect, "request_id": request["id"]},
    )
    assert response.status_code == 403, response.text
    assert response.json()["error"]["code"] == "self_approval"


def test_poster_author_is_recorded_and_cannot_approve(client, demo, owner, campaign):
    from brandproof.models import Actor
    from brandproof.workflow_models import RevisionAuthor
    from sqlalchemy import select
    from test_posters import upload

    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    response = upload(client, campaign, owner)
    assert response.status_code == 200, response.text
    with client.app.state.sessions() as session:
        author = session.scalar(
            select(RevisionAuthor).where(RevisionAuthor.campaign_id == campaign["id"])
        )
        assert author.content_revision == response.json()["content_revision"]
        assert session.get(Actor, author.actor_id).role == "owner"
    base = f"/api/v1/campaigns/{campaign['id']}"
    current = client.get(base, headers=owner).json()
    expect = {
        "expected_content_revision": current["content_revision"],
        "expected_source_revision": current["source_revision"],
    }
    run = client.post(base + "/reviews", headers=owner, json=expect).json()
    request = client.post(
        f"{base}/reviews/{run['id']}/requests", headers=headers(demo, "creator"), json=expect
    ).json()
    response = client.post(
        f"{base}/reviews/{run['id']}/approvals",
        headers=owner,
        json={
            **expect,
            "request_id": request["id"],
            "decision": "approve",
            "reason": "Poster content author must not approve.",
        },
    )
    assert response.status_code == 403, response.text
    assert response.json()["error"]["code"] == "self_approval"


@pytest.mark.parametrize("action", ["approval", "decision"])
def test_concurrent_decision_writes_have_single_winner(
    client, demo, owner, campaign, monkeypatch, action
):
    from threading import Barrier

    from sqlalchemy.orm import Session
    from sqlalchemy.sql.dml import Update

    _, run, base, payload = setup_request(
        client,
        demo,
        owner,
        campaign,
        "Join our workshop." if action == "decision" else "Terms apply.",
    )
    barrier = Barrier(2)
    original = Session.execute

    def before_write(session, statement, *args, **kwargs):
        if (
            isinstance(statement, Update)
            and statement.table.name == "campaigns"
            and not session.info.get("review_probe_first_write")
        ):
            session.info["review_probe_first_write"] = True
            barrier.wait(timeout=8)
        return original(session, statement, *args, **kwargs)

    monkeypatch.setattr(Session, "execute", before_write)
    if action == "decision":
        path = f"{base}/reviews/{run['id']}/findings/{run['findings'][0]['id']}/decisions"
        payload = {
            **expectation(run),
            "expected_decision_version": 0,
            "decision": "exception",
            "reason": "Concurrent versioned exception decision.",
        }
    else:
        path = f"{base}/reviews/{run['id']}/approvals"

    def write(_):
        return client.post(path, headers=headers(demo, "reviewer"), json=payload)

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(write, [0, 1]))
    assert sorted(r.status_code for r in responses) == [201, 409], [r.text for r in responses]
    receipt = client.get(base + "/receipt", headers=owner).json()
    if action == "approval":
        assert len(receipt["approvals"]) == 1
    else:
        assert len(client.get(path, headers=owner).json()) == 1


def test_expired_source_cannot_be_manually_promoted(client, demo, owner, campaign):
    _, run, base, payload = setup_request(client, demo, owner, campaign)
    add_source(
        client,
        owner,
        campaign,
        {"kind": "price", "amount": "499", "currency": "INR"},
        valid_until="2026-01-01",
    )
    run = review_copy(client, owner, campaign, "Terms apply.")
    request = client.post(
        f"{base}/reviews/{run['id']}/requests",
        headers=headers(demo, "creator"),
        json=expectation(run),
    ).json()
    response = client.post(
        f"{base}/reviews/{run['id']}/approvals",
        headers=headers(demo, "reviewer"),
        json={
            **payload,
            **expectation(run),
            "request_id": request["id"],
            "manual_checks": {
                key: "A manual check must not promote an expired approved source."
                for key in ["exact_text", "contextual", "advertising_risk"]
            },
        },
    )
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "sources_incomplete"


def test_actual_inflight_review_blocks_approval(client, demo, owner, campaign, monkeypatch):
    import brandproof.reviews as reviews
    from brandproof.contextual import ContextualResult

    _, run, base, payload = setup_request(client, demo, owner, campaign)
    entered, release = Event(), Event()

    def paused_context(*args, **kwargs):
        entered.set()
        assert release.wait(8)
        return ContextualResult("unavailable", "Isolated local probe; no external provider called.")

    monkeypatch.setattr(reviews, "analyze_context", paused_context)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(client.post, base + "/reviews", headers=owner, json=expectation(run))
        assert entered.wait(8)
        try:
            runs = client.get(base + "/reviews", headers=owner).json()
            live = next(row for row in runs if row["status"] == "running")
            request = client.post(
                f"{base}/reviews/{live['id']}/requests",
                headers=headers(demo, "creator"),
                json=expectation(live),
            ).json()
            response = client.post(
                f"{base}/reviews/{live['id']}/approvals",
                headers=headers(demo, "reviewer"),
                json={**payload, "request_id": request["id"]},
            )
            assert response.status_code == 409, response.text
            assert response.json()["error"]["code"] == "review_in_progress"
        finally:
            release.set()
        assert pending.result(timeout=8).status_code == 201

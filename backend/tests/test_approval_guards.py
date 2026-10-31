import pytest
from conftest import headers
from test_reviews import add_source, review_copy
from test_workflow import expectation


def setup_request(client, demo, owner, campaign, caption="Join our workshop. Terms apply."):
    source = add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    run = review_copy(client, owner, campaign, caption)
    base = f"/api/v1/campaigns/{campaign['id']}"
    request = client.post(
        f"{base}/reviews/{run['id']}/requests",
        headers=headers(demo, "creator"),
        json=expectation(run),
    )
    assert request.status_code == 201
    payload = {
        **expectation(run),
        "request_id": request.json()["id"],
        "decision": "approve",
        "reason": "Reviewed the current campaign and approved references.",
        "manual_checks": {
            "advertising_risk": "Synthetic test reviewer manually assessed the unconfigured advertising scope.",
            "contextual": "Personally checked tone and claim support against the current reference pack.",
        },
    }
    return source, run, base, payload


def test_content_author_cannot_approve_even_if_another_actor_requests_review(
    client, demo, owner, campaign
):
    _, run, base, payload = setup_request(client, demo, owner, campaign)
    # The owner wrote the caption; changing the requester must not bypass self-review protection.
    response = client.post(f"{base}/reviews/{run['id']}/approvals", headers=owner, json=payload)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "self_approval"


@pytest.mark.parametrize("change", ["source", "new_review", "new_request", "finding_decision"])
def test_approval_stales_after_relevant_review_workflow_changes(
    client, demo, owner, campaign, change
):
    caption = (
        "Join our workshop." if change == "finding_decision" else "Join our workshop. Terms apply."
    )
    source, run, base, payload = setup_request(client, demo, owner, campaign, caption)
    if run["findings"]:
        finding = run["findings"][0]
        response = client.post(
            f"{base}/reviews/{run['id']}/findings/{finding['id']}/decisions",
            headers=headers(demo, "reviewer"),
            json={
                **expectation(run),
                "expected_decision_version": 0,
                "decision": "exception",
                "reason": "Explicit campaign-scoped exception approved for this test.",
            },
        )
        assert response.status_code == 201, response.text
    approval = client.post(
        f"{base}/reviews/{run['id']}/approvals", headers=headers(demo, "reviewer"), json=payload
    )
    assert approval.status_code == 201, approval.text
    if change == "source":
        changed = client.put(
            f"{base}/sources/{source['id']}",
            headers=owner,
            json={
                "expected_version": source["version"],
                "title": "New rule",
                "rule": {"kind": "required_text", "text": "Updated terms apply"},
            },
        )
    elif change == "new_review":
        changed = client.post(base + "/reviews", headers=owner, json=expectation(run))
    elif change == "new_request":
        changed = client.post(
            f"{base}/reviews/{run['id']}/requests",
            headers=headers(demo, "creator"),
            json=expectation(run),
        )
    else:
        changed = client.post(
            f"{base}/reviews/{run['id']}/findings/{run['findings'][0]['id']}/decisions",
            headers=headers(demo, "reviewer"),
            json={
                **expectation(run),
                "expected_decision_version": 1,
                "decision": "reopen",
                "reason": "This exception needs renewed investigation before approval.",
            },
        )
    assert changed.status_code in (200, 201), changed.text
    receipt = client.get(base + "/receipt", headers=owner).json()
    assert receipt["readiness"] == "stale"
    assert receipt["approvals"][0]["is_current"] is False


@pytest.mark.parametrize("role", ["owner", "creator"])
def test_content_authors_and_creators_cannot_self_approve(client, demo, owner, campaign, role):
    _, run, base, payload = setup_request(client, demo, owner, campaign)
    response = client.post(
        f"{base}/reviews/{run['id']}/approvals", headers=headers(demo, role), json=payload
    )
    assert response.status_code == 403


def test_unresolved_findings_prevent_approval_even_with_manual_notes(client, demo, owner, campaign):
    _, run, base, payload = setup_request(client, demo, owner, campaign, "Join our workshop.")
    response = client.post(
        f"{base}/reviews/{run['id']}/approvals", headers=headers(demo, "reviewer"), json=payload
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "unresolved_findings"


def test_request_changes_is_recorded_and_requires_a_fresh_request_for_another_decision(
    client, demo, owner, campaign
):
    _, run, base, payload = setup_request(client, demo, owner, campaign)
    payload.update(decision="request_changes", manual_checks={})
    url = f"{base}/reviews/{run['id']}/approvals"
    response = client.post(url, headers=headers(demo, "reviewer"), json=payload)
    assert response.status_code == 201, response.text
    assert client.get(base + "/receipt", headers=owner).json()["readiness"] == "changes_requested"
    assert client.post(url, headers=headers(demo, "reviewer"), json=payload).status_code == 409


def test_pending_sources_cannot_be_approved_via_manual_coverage(client, demo, owner, campaign):
    source, run, base, payload = setup_request(client, demo, owner, campaign)
    add_source(
        client,
        owner,
        campaign,
        {"kind": "price", "amount": "499", "currency": "INR"},
        confirm=False,
    )
    run = review_copy(client, owner, campaign, "Join our workshop. Terms apply.")
    request = client.post(
        f"{base}/reviews/{run['id']}/requests",
        headers=headers(demo, "creator"),
        json=expectation(run),
    ).json()
    payload.update(**expectation(run), request_id=request["id"])
    payload["manual_checks"]["exact_text"] = (
        "Manually checked all relevant values; this cannot promote pending facts."
    )
    response = client.post(
        f"{base}/reviews/{run['id']}/approvals", headers=headers(demo, "reviewer"), json=payload
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "sources_incomplete"


def test_inflight_review_cannot_be_approved_with_manual_bypass(client, demo, owner, campaign):
    from brandproof.review_models import ReviewRun

    _, run, base, payload = setup_request(client, demo, owner, campaign)
    with client.app.state.sessions() as session:
        row = session.get(ReviewRun, run["id"])
        row.status = "running"
        session.commit()
    response = client.post(
        f"{base}/reviews/{run['id']}/approvals", headers=headers(demo, "reviewer"), json=payload
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "review_in_progress"

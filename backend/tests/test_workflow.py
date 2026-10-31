from conftest import headers
from test_reviews import add_source, review_copy


def test_creator_comment_is_persisted_and_isolated(client, demo, owner, campaign):
    run = review_copy(client, owner, campaign, "A workshop announcement.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    response = client.post(
        base + "/comments",
        headers=headers(demo, "creator"),
        json={
            "expected_content_revision": run["content_revision"],
            "expected_source_revision": run["source_revision"],
            "review_id": run["id"],
            "text": "Please check the campaign date before approval.",
        },
    )
    assert response.status_code == 201, response.text
    comment = response.json()
    assert comment["actor_role"] == "creator"
    assert comment["review_id"] == run["id"]
    rows = client.get(base + "/comments", headers=headers(demo, "reviewer")).json()
    assert rows == [comment]
    other = client.post("/api/v1/demo-sessions").json()
    assert client.get(base + "/comments", headers=headers(other)).status_code == 404


def expectation(run):
    return {
        "expected_content_revision": run["content_revision"],
        "expected_source_revision": run["source_revision"],
    }


def test_reviewer_finding_decisions_are_versioned_and_creator_cannot_dismiss(
    client, demo, owner, campaign
):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    run = review_copy(client, owner, campaign, "Book for INR 599.")
    base = f"/api/v1/campaigns/{campaign['id']}/reviews/{run['id']}/findings/{run['findings'][0]['id']}/decisions"
    payload = {
        **expectation(run),
        "expected_decision_version": 0,
        "decision": "exception",
        "reason": "A scoped exception confirmed by the campaign owner.",
    }
    assert client.post(base, headers=headers(demo, "creator"), json=payload).status_code == 403
    response = client.post(base, headers=headers(demo, "reviewer"), json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["version"] == 1
    assert client.post(base, headers=headers(demo, "reviewer"), json=payload).status_code == 409
    history = client.get(base, headers=owner).json()
    assert len(history) == 1
    assert history[0]["reason"] == payload["reason"]


def test_review_request_does_not_approve_and_only_creator_or_owner_can_request(
    client, demo, owner, campaign
):
    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    run = review_copy(client, owner, campaign, "Join our workshop. Terms apply.")
    url = f"/api/v1/campaigns/{campaign['id']}/reviews/{run['id']}/requests"
    assert (
        client.post(url, headers=headers(demo, "reviewer"), json=expectation(run)).status_code
        == 403
    )
    response = client.post(url, headers=headers(demo, "creator"), json=expectation(run))
    assert response.status_code == 201, response.text
    assert response.json()["requested_by"]
    assert response.json()["review_id"] == run["id"]
    receipt = client.get(f"/api/v1/campaigns/{campaign['id']}/receipt", headers=owner)
    assert receipt.status_code == 200
    assert receipt.json()["readiness"] == "not_approved"
    assert receipt.json()["requests"][0]["id"] == response.json()["id"]


def test_approval_requires_explicit_manual_coverage_and_becomes_stale_after_edit(
    client, demo, owner, campaign
):
    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    run = review_copy(client, owner, campaign, "Join our workshop. Terms apply.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    request = client.post(
        f"{base}/reviews/{run['id']}/requests",
        headers=headers(demo, "creator"),
        json=expectation(run),
    ).json()
    payload = {
        **expectation(run),
        "request_id": request["id"],
        "decision": "approve",
        "reason": "Reviewed the current campaign and approved reference material.",
    }
    url = f"{base}/reviews/{run['id']}/approvals"
    assert client.post(url, headers=headers(demo, "reviewer"), json=payload).status_code == 409
    payload["manual_checks"] = {
        "advertising_risk": "Synthetic test reviewer manually assessed the unconfigured advertising scope.",
        "contextual": "Manually checked tone and objective claims against the approved reference pack.",
    }
    response = client.post(url, headers=headers(demo, "reviewer"), json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["coverage_mode"] == "manual_supplement"
    receipt = client.get(base + "/receipt", headers=owner).json()
    assert receipt["readiness"] == "approved_with_manual_checks"
    assert receipt["approvals"][0]["is_current"] is True
    stored = client.get(f"{base}/reviews/{run['id']}", headers=owner).json()
    assert stored["status"] == "partial"
    assert stored["checks"]["contextual"]["status"] == "unavailable"
    assert stored["readiness"] == "approved_with_manual_checks"
    edited = client.put(
        base + "/caption",
        headers=owner,
        json={
            "expected_revision": run["content_revision"],
            "text": "Updated workshop. Terms apply.",
        },
    )
    assert edited.status_code == 200
    receipt = client.get(base + "/receipt", headers=owner).json()
    assert receipt["readiness"] == "stale"
    assert receipt["approvals"][0]["is_current"] is False
    assert receipt["approvals"][0]["manual_checks"] == payload["manual_checks"]

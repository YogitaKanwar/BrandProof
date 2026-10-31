from conftest import headers
from test_reviews import add_source, review_copy


def test_governance_deduplicates_runs_requires_sample_and_retains_latest_reasons(
    client, demo, owner, campaign
):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    base = f"/api/v1/campaigns/{campaign['id']}"
    latest = None
    for i in range(5):
        run = review_copy(client, owner, campaign, "Book for INR 599." + " " * i)
        if i == 0:
            # Same saved snapshot rerun: only the latest run contributes.
            run = client.post(
                base + "/reviews",
                headers=owner,
                json={
                    "expected_content_revision": run["content_revision"],
                    "expected_source_revision": run["source_revision"],
                },
            ).json()
        finding = next(f for f in run["findings"] if f["category"] == "price")
        payload = {
            "expected_content_revision": run["content_revision"],
            "expected_source_revision": run["source_revision"],
            "expected_decision_version": 0,
            "decision": "exception",
            "reason": "Synthetic historical exception; not real evidence of ambiguity.",
        }
        url = base + "/reviews/" + run["id"] + "/findings/" + finding["id"] + "/decisions"
        assert client.post(url, headers=headers(demo, "reviewer"), json=payload).status_code == 201
        latest = (url, payload)
        insights = client.get("/api/v1/governance-insights", headers=owner).json()
        row = insights["guidelines"][0]
        assert row["observations"] == i + 1
        if i < 4:
            assert row["decision_rate"] is None and not row["potentially_ambiguous"]
    assert row["decision_rate"] == 1 and row["potentially_ambiguous"]
    assert row["source_version"] == 2 and all(e["source_version_id"] for e in row["evidence"])
    url, payload = latest
    payload.update(
        expected_decision_version=1,
        decision="reopen",
        reason="Reopened after examining the actual support again.",
    )
    assert client.post(url, headers=headers(demo, "reviewer"), json=payload).status_code == 201
    row = client.get("/api/v1/governance-insights", headers=owner).json()["guidelines"][0]
    assert row["reopened"] == 1 and row["exceptions"] == 4 and row["decision_rate"] == 0.8
    assert any(
        e["reason"] == payload["reason"] and e["decision"] == "reopen" for e in row["evidence"]
    )
    other = client.post("/api/v1/demo-sessions").json()
    assert (
        client.get("/api/v1/governance-insights", headers=headers(other)).json()["categories"] == []
    )
    assert client.get("/api/v1/governance-insights").status_code == 401


def test_identical_rerun_does_not_inherit_previous_decisions_and_deleted_history_is_hidden(
    client, demo, owner, campaign
):
    from test_workflow import expectation

    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    run = review_copy(client, owner, campaign, "Workshop announcement.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    finding = run["findings"][0]
    client.post(
        base + f"/reviews/{run['id']}/findings/{finding['id']}/decisions",
        headers=headers(demo, "reviewer"),
        json={
            **expectation(run),
            "expected_decision_version": 0,
            "decision": "dismiss",
            "reason": "Synthetic test of decision counting semantics.",
        },
    )
    assert (
        client.get("/api/v1/governance-insights", headers=owner).json()["guidelines"][0]["reviewed"]
        == 1
    )
    newer = client.post(base + "/reviews", headers=owner, json=expectation(run)).json()
    data = client.get("/api/v1/governance-insights", headers=owner).json()
    assert data["guidelines"][0]["reviewed"] == 0
    assert data["guidelines"][0]["evidence"][0]["review_id"] == newer["id"]
    assert client.request("DELETE", base, headers=owner, json=expectation(run)).status_code == 200
    assert client.get("/api/v1/governance-insights", headers=owner).json()["categories"] == []


def test_insights_campaigns_versions_and_truncation(client, owner, campaign, monkeypatch):
    from brandproof import insights

    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    review_copy(client, owner, campaign, "INR 599")
    other = client.post(
        "/api/v1/campaigns",
        headers=owner,
        json={"name": "Other campaign", "publication_date": "2026-11-12"},
    ).json()
    add_source(client, owner, other, {"kind": "price", "amount": "499", "currency": "INR"})
    review_copy(client, owner, other, "INR 599")
    data = client.get("/api/v1/governance-insights", headers=owner).json()
    assert data["categories"][0]["campaigns"] == 2
    assert len(data["guidelines"]) == 2  # Same text does not collapse unrelated source versions.
    monkeypatch.setattr(insights, "MAX_RUNS", 1)
    assert client.get("/api/v1/governance-insights", headers=owner).json()["truncated"]


def test_regulatory_dismissals_never_mark_regulation_ambiguous(client, demo, owner, campaign):
    from test_legal import set_profile
    from test_workflow import expectation

    set_profile(client, owner, campaign)
    for i in range(5):
        run = review_copy(client, owner, campaign, "Guaranteed results. " + str(i))
        finding = run["findings"][0]
        response = client.post(
            f"/api/v1/campaigns/{campaign['id']}/reviews/{run['id']}/findings/{finding['id']}/decisions",
            headers=headers(demo, "reviewer"),
            json={
                **expectation(run),
                "expected_decision_version": 0,
                "decision": "dismiss",
                "reason": "Synthetic QA-only decision; not evidence of legal compliance.",
            },
        )
        assert response.status_code == 201
    row = client.get("/api/v1/governance-insights", headers=owner).json()["guidelines"][0]
    assert row["decision_rate"] == 1 and row["reviewed_snapshots"] == 5
    assert row["regulatory_reference"]["id"] == "IN-CCPA-2022-12A"
    assert not row["potentially_ambiguous"]

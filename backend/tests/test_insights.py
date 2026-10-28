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

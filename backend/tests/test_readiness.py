from conftest import headers
from test_reviews import review_copy


def test_guidance_reports_actual_pending_findings_requests_and_manual_requirements(
    client, demo, owner, campaign
):
    base = f"/api/v1/campaigns/{campaign['id']}"
    first = client.get(base + "/readiness", headers=owner).json()
    assert {"sources_missing", "content_missing", "review_missing"} <= {
        b["code"] for b in first["blockers"]
    }
    source = client.post(
        base + "/sources",
        headers=owner,
        json={"title": "Price", "rule": {"kind": "price", "amount": "499", "currency": "INR"}},
    ).json()
    assert "source_pending" in {
        b["code"] for b in client.get(base + "/readiness", headers=owner).json()["blockers"]
    }
    client.post(
        base + "/sources/" + source["id"] + "/confirm", headers=owner, json={"expected_version": 1}
    )
    run = review_copy(client, owner, campaign, "Guaranteed results in 30 days. Book for INR 599.")
    guide = client.get(base + "/readiness", headers=headers(demo, "reviewer")).json()
    ids = {b["finding_id"] for b in guide["blockers"] if b["code"] == "finding_unresolved"}
    assert ids == {f["id"] for f in run["findings"]}
    assert "claim_risk" in guide["manual_checks"] and "contextual" in guide["manual_checks"]
    assert "request_required" in {b["code"] for b in guide["blockers"]}
    assert "self_approval" in {
        b["code"] for b in client.get(base + "/readiness", headers=owner).json()["blockers"]
    }
    assert "approver_role" in {
        b["code"]
        for b in client.get(base + "/readiness", headers=headers(demo, "creator")).json()[
            "blockers"
        ]
    }
    client.put(
        base + "/caption", headers=owner, json={"expected_revision": 2, "text": "Book for INR 499."}
    )
    assert "review_stale" in {
        b["code"] for b in client.get(base + "/readiness", headers=owner).json()["blockers"]
    }


def test_readiness_is_workspace_scoped(client, owner, campaign):
    other = client.post("/api/v1/demo-sessions").json()
    assert (
        client.get(
            f"/api/v1/campaigns/{campaign['id']}/readiness", headers=headers(other)
        ).status_code
        == 404
    )

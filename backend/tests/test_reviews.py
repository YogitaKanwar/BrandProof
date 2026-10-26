def add_source(client, owner, campaign, rule, *, confirm=True, **extra):
    base = f"/api/v1/campaigns/{campaign['id']}/sources"
    response = client.post(base, headers=owner, json={"title": "Test rule", "rule": rule, **extra})
    assert response.status_code == 201, response.text
    source = response.json()
    if confirm:
        response = client.post(
            f"{base}/{source['id']}/confirm",
            headers=owner,
            json={"expected_version": source["version"]},
        )
        assert response.status_code == 200, response.text
        source = response.json()
    return source


def review_copy(client, owner, campaign, text):
    base = f"/api/v1/campaigns/{campaign['id']}"
    current = client.get(base, headers=owner).json()
    response = client.put(
        f"{base}/caption",
        headers=owner,
        json={"expected_revision": current["content_revision"], "text": text},
    )
    assert response.status_code == 200, response.text
    current = client.get(base, headers=owner).json()
    response = client.post(
        f"{base}/reviews",
        headers=owner,
        json={
            "expected_content_revision": current["content_revision"],
            "expected_source_revision": current["source_revision"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_price_conflict_has_exact_versioned_evidence_and_persisted_result(client, owner, campaign):
    source = add_source(
        client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"}
    )
    run = review_copy(client, owner, campaign, "Join our workshop for INR 599.")
    assert run["status"] == "partial"
    assert run["is_current"] is True
    assert run["readiness"] == "not_approved"
    assert run["checks"]["contextual"]["status"] == "unavailable"
    finding = run["findings"][0]
    assert finding["category"] == "price"
    assert finding["evidence_status"] == "contradicted"
    assert finding["location"]["quote"] == "INR 599"
    assert finding["evidence"]["source_id"] == source["id"]
    assert finding["evidence"]["source_version"] == source["version"]
    assert finding["evidence"]["quote"] == source["text"]
    assert finding["suggested_replacement"] == "INR 499"
    stored = client.get(f"/api/v1/campaigns/{campaign['id']}/reviews/{run['id']}", headers=owner)
    assert stored.status_code == 200
    assert stored.json()["findings"] == run["findings"]


def test_multiple_prices_request_clarification_instead_of_overwriting_offer_conditions(
    client, owner, campaign
):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    run = review_copy(client, owner, campaign, "Early bird INR 499; regular INR 599.")
    assert len(run["findings"]) == 1
    finding = run["findings"][0]
    assert finding["evidence_status"] == "needs_clarification"
    assert finding["suggested_replacement"] is None


def test_conflicting_approved_prices_require_owner_clarification(client, owner, campaign):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    add_source(client, owner, campaign, {"kind": "price", "amount": "599", "currency": "INR"})
    run = review_copy(client, owner, campaign, "Workshop price INR 499.")
    assert run["findings"]
    assert all(f["evidence_status"] == "needs_clarification" for f in run["findings"])
    assert all(f["suggested_replacement"] is None for f in run["findings"])
    assert run["checks"]["exact_text"]["status"] == "partial"

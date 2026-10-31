from brandproof.workflow_models import RevisionAuthor
from sqlalchemy import select
from test_ocr import poster_bytes


def test_production_app_mounts_poster_routes_and_tracks_uploader(client, demo, owner, campaign):
    base = f"/api/v1/campaigns/{campaign['id']}"
    response = client.put(
        base + "/posters?expected_revision=1",
        headers={**owner, "Content-Type": "image/png"},
        content=poster_bytes("Our cheap workshop"),
    )
    assert response.status_code == 200, response.text
    asset = response.json()
    assert client.get(base + "/posters", headers=owner).json()["id"] == asset["id"]
    with client.app.state.sessions() as session:
        authors = session.scalars(
            select(RevisionAuthor).where(RevisionAuthor.campaign_id == campaign["id"])
        ).all()
        assert len(authors) == 1
        assert authors[0].content_revision == asset["content_revision"]
        from brandproof.models import Actor

        author = session.get(Actor, authors[0].actor_id)
        assert author.workspace_id == demo["workspace_id"]
        assert author.role == "owner"


def test_poster_review_maps_real_ocr_findings_to_historical_asset_boxes(client, owner, campaign):
    from test_reviews import add_source

    source = add_source(
        client, owner, campaign, {"kind": "terminology", "term": "cheap", "preferred": "affordable"}
    )
    base = f"/api/v1/campaigns/{campaign['id']}"
    response = client.put(
        base + "/posters?expected_revision=1",
        headers={**owner, "Content-Type": "image/png"},
        content=poster_bytes("Our cheap workshop"),
    )
    assert response.status_code == 200
    asset = response.json()
    from brandproof.models import Campaign
    from brandproof.poster_review import review_poster

    with client.app.state.sessions() as session:
        findings, check = review_poster(
            session, session.get(Campaign, campaign["id"]), [source], []
        )
    assert check["status"] == "partial"  # Visual branding and accessibility were not assessed.
    assert check["details"]["asset_id"] == asset["id"]
    assert check["details"]["ocr_status"] == "completed"
    finding = next(f for f in findings if f["category"] == "terminology")
    assert finding["location"]["asset"] == "poster"
    assert finding["location"]["poster_id"] == asset["id"]
    assert finding["location"]["quote"].lower() == "cheap"
    assert finding["location"]["boxes"]
    assert finding["suggested_replacement"] is None
    assert finding["evidence"]["source_id"] == source["id"]


def test_api_review_persists_poster_locations_and_does_not_edit_image(client, owner, campaign):
    from test_reviews import add_source, review_copy
    from test_workflow import expectation

    add_source(
        client, owner, campaign, {"kind": "terminology", "term": "cheap", "preferred": "affordable"}
    )
    prior = review_copy(client, owner, campaign, "An affordable workshop.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    upload = client.put(
        base + f"/posters?expected_revision={prior['content_revision']}",
        headers={**owner, "Content-Type": "image/png"},
        content=poster_bytes("Our cheap workshop"),
    )
    assert upload.status_code == 200
    current = client.get(base, headers=owner).json()
    run_response = client.post(
        base + "/reviews",
        headers=owner,
        json={
            "expected_content_revision": current["content_revision"],
            "expected_source_revision": current["source_revision"],
        },
    )
    assert run_response.status_code == 201, run_response.text
    run = run_response.json()
    assert run["checks"]["poster"]["details"]["asset_id"] == upload.json()["id"]
    finding = next(f for f in run["findings"] if f["location"]["asset"] == "poster")
    assert finding["location"]["boxes"]
    assert finding["location"]["poster_id"] == upload.json()["id"]
    assert finding["location"]["content_revision"] == current["content_revision"]
    assert finding["suggested_replacement"] is None
    assert (
        client.get(base + f"/reviews/{run['id']}", headers=owner).json()["findings"]
        == run["findings"]
    )
    rejected = client.post(
        base + f"/reviews/{run['id']}/findings/{finding['id']}/apply",
        headers=owner,
        json=expectation(run),
    )
    assert rejected.status_code == 409
    assert client.get(base + "/posters", headers=owner).json()["id"] == upload.json()["id"]
    assert client.get(base, headers=owner).json()["content_revision"] == current["content_revision"]
    changed = client.put(
        base + f"/posters?expected_revision={current['content_revision']}",
        headers={**owner, "Content-Type": "image/png"},
        content=poster_bytes("An affordable workshop"),
    )
    assert changed.status_code == 200
    historical = client.get(base + f"/reviews/{run['id']}", headers=owner).json()
    assert historical["is_current"] is False
    assert historical["checks"]["poster"]["details"]["asset_id"] == upload.json()["id"]
    assert historical["findings"] == run["findings"]


def test_poster_manual_coverage_is_explicit_and_new_upload_stales_approval(
    client, demo, owner, campaign
):
    from conftest import headers
    from test_reviews import add_source, review_copy
    from test_workflow import expectation

    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    initial = review_copy(client, owner, campaign, "Terms apply")
    base = f"/api/v1/campaigns/{campaign['id']}"
    upload = client.put(
        base + f"/posters?expected_revision={initial['content_revision']}",
        headers={**owner, "Content-Type": "image/png"},
        content=poster_bytes("Terms apply"),
    )
    assert upload.status_code == 200
    current = client.get(base, headers=owner).json()
    expected = {
        "expected_content_revision": current["content_revision"],
        "expected_source_revision": current["source_revision"],
    }
    response = client.post(base + "/reviews", headers=owner, json=expected)
    assert response.status_code == 201, response.text
    run = response.json()
    request = client.post(
        base + f"/reviews/{run['id']}/requests",
        headers=headers(demo, "creator"),
        json=expectation(run),
    )
    assert request.status_code == 201, request.text
    payload = {
        **expectation(run),
        "request_id": request.json()["id"],
        "decision": "approve",
        "reason": "Synthetic API regression decision, not an actual user study.",
        "manual_checks": {
            "advertising_risk": "Synthetic test reviewer manually assessed the unconfigured advertising scope.",
            "contextual": "Synthetic reviewer attestation for tone and claim checking.",
        },
    }
    url = base + f"/reviews/{run['id']}/approvals"
    denied = client.post(url, headers=headers(demo, "reviewer"), json=payload)
    assert denied.status_code == 409, denied.text
    assert denied.json()["error"]["code"] == "checks_incomplete"
    payload["manual_checks"]["poster"] = (
        "Synthetic reviewer attestation for visual branding, text, claims and accessibility."
    )
    assert client.post(url, headers=owner, json=payload).status_code == 403
    approved = client.post(url, headers=headers(demo, "reviewer"), json=payload)
    assert approved.status_code == 201, approved.text
    receipt = client.get(base + "/receipt", headers=owner).json()
    assert receipt["scope"] == "caption_and_attached_poster"
    assert receipt["readiness"] == "approved_with_manual_checks"
    changed = client.put(
        base + f"/posters?expected_revision={current['content_revision']}",
        headers={**owner, "Content-Type": "image/png"},
        content=poster_bytes("Terms apply revised"),
    )
    assert changed.status_code == 200
    stale = client.get(base + "/receipt", headers=owner).json()
    assert stale["readiness"] == "stale"
    assert stale["approvals"][0]["is_current"] is False

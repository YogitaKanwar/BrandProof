from datetime import UTC, datetime, timedelta

import pytest
from brandproof.models import Actor
from conftest import headers
from sqlalchemy import select
from test_reviews import add_source, review_copy


def test_unauthenticated_calls_are_rejected(client):
    response = client.get("/api/v1/campaigns")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


@pytest.mark.parametrize("role", ["creator", "reviewer"])
def test_only_owner_can_confirm_campaign_sources(client, demo, campaign, owner, role):
    source = add_source(
        client,
        owner,
        campaign,
        {"kind": "price", "amount": "499", "currency": "INR"},
        confirm=False,
    )
    response = client.post(
        f"/api/v1/campaigns/{campaign['id']}/sources/{source['id']}/confirm",
        headers=headers(demo, role),
        json={"expected_version": 1},
    )
    assert response.status_code == 403


@pytest.mark.parametrize("suffix", ["", "/sources", "/reviews"])
def test_other_demo_workspace_cannot_read_campaign_records(client, owner, campaign, suffix):
    other = client.post("/api/v1/demo-sessions").json()
    response = client.get(f"/api/v1/campaigns/{campaign['id']}{suffix}", headers=headers(other))
    assert response.status_code == 404
    assert client.get("/api/v1/campaigns", headers=headers(other)).json() == []


def test_caller_cannot_assign_their_own_role_in_payload(client, demo):
    response = client.post(
        "/api/v1/campaigns",
        headers=headers(demo, "reviewer"),
        json={"name": "Hack", "publication_date": "2026-11-12", "role": "owner"},
    )
    assert response.status_code == 422
    response = client.post(
        "/api/v1/campaigns",
        headers=headers(demo, "reviewer"),
        json={"name": "Hack", "publication_date": "2026-11-12"},
    )
    assert response.status_code == 403


def test_expired_demo_token_is_rejected(client, owner):
    with client.app.state.sessions() as session:
        for actor in session.scalars(select(Actor)):
            actor.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()
    assert client.get("/api/v1/campaigns", headers=owner).status_code == 401


def test_invalid_source_values_are_rejected_without_echoing_content(client, owner, campaign):
    response = client.post(
        f"/api/v1/campaigns/{campaign['id']}/sources",
        headers=owner,
        json={
            "title": "private-confidential-example",
            "rule": {"kind": "price", "amount": "-1", "currency": "INR"},
        },
    )
    assert response.status_code == 422
    assert "private-confidential-example" not in response.text


def test_no_cross_campaign_source_id_access(client, owner, campaign):
    source = add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    second = client.post(
        "/api/v1/campaigns",
        headers=owner,
        json={"name": "Second", "publication_date": "2026-11-12"},
    ).json()
    response = client.get(
        f"/api/v1/campaigns/{second['id']}/sources/{source['id']}/versions", headers=owner
    )
    assert response.status_code == 404


def test_stale_caption_update_does_not_overwrite_newer_revision(client, owner, campaign):
    base = f"/api/v1/campaigns/{campaign['id']}"
    first = client.put(
        f"{base}/caption", headers=owner, json={"expected_revision": 1, "text": "New copy"}
    )
    assert first.status_code == 200
    stale = client.put(
        f"{base}/caption", headers=owner, json={"expected_revision": 1, "text": "Old browser copy"}
    )
    assert stale.status_code == 409
    assert client.get(base, headers=owner).json()["caption"] == "New copy"


@pytest.mark.parametrize("change", ["caption", "source"])
def test_old_review_remains_stored_but_is_not_current_after_edits(client, owner, campaign, change):
    source = add_source(
        client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"}
    )
    run = review_copy(client, owner, campaign, "Workshop price INR 599.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    if change == "caption":
        response = client.put(
            f"{base}/caption",
            headers=owner,
            json={"expected_revision": run["content_revision"], "text": "Workshop price INR 499."},
        )
    else:
        response = client.put(
            f"{base}/sources/{source['id']}",
            headers=owner,
            json={
                "expected_version": source["version"],
                "title": "Revised price",
                "rule": {"kind": "price", "amount": "699", "currency": "INR"},
            },
        )
    assert response.status_code == 200
    stored = client.get(f"{base}/reviews/{run['id']}", headers=owner).json()
    assert stored["is_current"] is False
    assert stored["findings"] == run["findings"]
    assert stored["sources_used"][0]["text"] == source["text"]


def test_review_creation_rejects_an_old_source_snapshot(client, owner, campaign):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    base = f"/api/v1/campaigns/{campaign['id']}"
    client.put(f"{base}/caption", headers=owner, json={"expected_revision": 1, "text": "INR 499"})
    response = client.post(
        f"{base}/reviews",
        headers=owner,
        json={"expected_content_revision": 2, "expected_source_revision": 0},
    )
    assert response.status_code == 409


@pytest.mark.parametrize(
    "caption",
    [
        "Join for INR 499.",
        "INR 499 for 20 seats on 2026-11-12.",
        "Join for Rs. 499.",
        "Join for ₹499.",
    ],
)
def test_valid_price_and_unrelated_numbers_do_not_trigger_price_conflicts(
    client, owner, campaign, caption
):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    assert review_copy(client, owner, campaign, caption)["findings"] == []

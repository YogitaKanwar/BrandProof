import pytest
from fastapi.testclient import TestClient
from test_reviews import add_source


@pytest.mark.parametrize(
    "operation,field,oversize",
    [
        ("caption", "expected_revision", 2**100),
        ("caption", "expected_revision", 2**31 - 1),
        ("revise", "expected_version", 2**100),
        ("revise", "expected_version", 2**31 - 1),
        ("confirm", "expected_version", 2**100),
        ("confirm", "expected_version", 2**31 - 1),
        ("review", "expected_content_revision", 2**100),
        ("review", "expected_content_revision", 2**31),
        ("review", "expected_source_revision", 2**100),
        ("review", "expected_source_revision", 2**31),
    ],
)
def test_expectations_outside_portable_integer_range_return_422(
    client, owner, campaign, operation, field, oversize
):
    base = f"/api/v1/campaigns/{campaign['id']}"
    source = add_source(
        client,
        owner,
        campaign,
        {"kind": "required_text", "text": "Terms apply"},
        confirm=False,
    )
    method = "POST"
    if operation == "caption":
        method, path, payload = (
            "PUT",
            f"{base}/caption",
            {"expected_revision": 1, "text": "Saved"},
        )
    elif operation == "revise":
        method, path, payload = (
            "PUT",
            f"{base}/sources/{source['id']}",
            {
                "expected_version": 1,
                "title": "Revised",
                "rule": {"kind": "required_text", "text": "Terms apply"},
            },
        )
    elif operation == "confirm":
        path, payload = (
            f"{base}/sources/{source['id']}/confirm",
            {"expected_version": 1},
        )
    else:
        path, payload = (
            f"{base}/reviews",
            {"expected_content_revision": 1, "expected_source_revision": 1},
        )
    payload[field] = oversize
    # Surface real HTTP 500s as failed assertions, not exception propagation.
    with TestClient(client.app, raise_server_exceptions=False) as requester:
        response = requester.request(method, path, headers=owner, json=payload)
    assert response.status_code == 422, response.text


def test_revision_bounds_allow_the_last_safe_increment(client, owner, campaign):
    from brandproof.models import Campaign

    base = f"/api/v1/campaigns/{campaign['id']}"
    with client.app.state.sessions() as session:
        row = session.get(Campaign, campaign["id"])
        row.content_revision = 2**31 - 2
        session.commit()
    response = client.put(
        f"{base}/caption",
        headers=owner,
        json={"expected_revision": 2**31 - 2, "text": "Last supported revision"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["content_revision"] == 2**31 - 1
    response = client.post(
        f"{base}/reviews",
        headers=owner,
        json={"expected_content_revision": 2**31 - 1, "expected_source_revision": 0},
    )
    assert response.status_code == 201, response.text


def test_source_snapshot_increment_cannot_exceed_portable_integer_range(client, owner, campaign):
    from brandproof.models import Campaign

    base = f"/api/v1/campaigns/{campaign['id']}"
    with client.app.state.sessions() as session:
        row = session.get(Campaign, campaign["id"])
        row.source_revision = 2**31 - 1
        session.commit()
    response = client.post(
        f"{base}/sources",
        headers=owner,
        json={
            "title": "Overflow",
            "rule": {"kind": "required_text", "text": "Terms apply"},
        },
    )
    assert response.status_code == 409, response.text
    assert client.get(f"{base}/sources", headers=owner).json() == []
    assert client.get(base, headers=owner).json()["source_revision"] == 2**31 - 1

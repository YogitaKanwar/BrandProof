from conftest import headers
from test_reviews import add_source, review_copy
from test_workflow import expectation


def test_explicit_suggestion_acceptance_creates_revision_and_cannot_replay(
    client, demo, owner, campaign
):
    add_source(
        client, owner, campaign, {"kind": "terminology", "term": "cheap", "preferred": "affordable"}
    )
    run = review_copy(client, owner, campaign, "Our cheap workshop.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    url = f"{base}/reviews/{run['id']}/findings/{run['findings'][0]['id']}/apply"
    response = client.post(url, headers=headers(demo, "creator"), json=expectation(run))
    assert response.status_code == 200, response.text
    assert response.json()["caption"] == "Our affordable workshop."
    assert response.json()["content_revision"] == run["content_revision"] + 1
    assert (
        client.post(url, headers=headers(demo, "creator"), json=expectation(run)).status_code == 409
    )
    history = client.get(base + "/revisions", headers=owner)
    assert history.status_code == 200
    assert [r["caption"] for r in history.json()] == [
        "",
        "Our cheap workshop.",
        "Our affordable workshop.",
    ]


def test_appending_required_wording_cannot_overflow_caption_limit(client, demo, owner, campaign):
    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    run = review_copy(client, owner, campaign, "x" * 20000)
    url = f"/api/v1/campaigns/{campaign['id']}/reviews/{run['id']}/findings/{run['findings'][0]['id']}/apply"
    # Invalid transformation must be an API conflict, not an unhandled Pydantic exception.
    from fastapi.testclient import TestClient

    with TestClient(client.app, raise_server_exceptions=False) as requester:
        response = requester.post(url, headers=headers(demo, "creator"), json=expectation(run))
    assert response.status_code == 409, response.text

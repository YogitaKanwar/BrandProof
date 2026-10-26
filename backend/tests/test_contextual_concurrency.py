"""Deterministic simulated-provider waits; no live inference or network calls."""

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import httpx
import pytest
from test_contextual_integration import completion_response, configured, start_current
from test_reviews import add_source, review_copy


@pytest.mark.parametrize("mutation", ["caption", "source"])
@pytest.mark.parametrize("expire_on_commit", [False, True])
def test_provider_wait_releases_database_and_preserves_stale_snapshot(
    client,
    owner,
    campaign,
    mutation,
    expire_on_commit,
):
    client.app.state.sessions.configure(expire_on_commit=expire_on_commit)
    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    tone = add_source(client, owner, campaign, {"kind": "tone", "guidance": "Respectful tone"})
    old = review_copy(client, owner, campaign, "Stupid offer. Terms apply.")
    configured(client)
    entered, release = Event(), Event()
    packs, connections = [], []

    def provider(request):
        # Record before any inspection request acquires its own connection.
        connections.append(client.app.state.engine.pool.checkedout())
        packs.append(json.loads(json.loads(request.content)["messages"][1]["content"]))
        entered.set()
        assert release.wait(10), "Test did not release simulated provider"
        return completion_response(
            {
                "findings": [
                    {
                        "category": "tone",
                        "severity": "warning",
                        "evidence_status": "contradicted",
                        "start": 0,
                        "end": 6,
                        "quote": "Stupid",
                        "source_id": tone["id"],
                        "source_version": tone["version"],
                        "source_quote": tone["text"],
                        "message": "Use respectful wording.",
                    }
                ]
            }
        )

    client.app.state.contextual_transport = httpx.MockTransport(provider)
    base = f"/api/v1/campaigns/{campaign['id']}"
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(start_current, client, owner, campaign)
        try:
            assert entered.wait(5), "Provider was not called"
            assert connections == [0], "Review retained a database connection across HTTP"
            listed = client.get(base + "/reviews", headers=owner)
            assert listed.status_code == 200, listed.text
            running = [run for run in listed.json() if run["status"] == "running"]
            assert len(running) == 1
            snapshot = running[0]
            assert snapshot["caption"] == old["caption"]
            assert snapshot["sources_used"] == old["sources_used"]
            if mutation == "caption":
                edit = pool.submit(
                    client.put,
                    base + "/caption",
                    headers=owner,
                    json={"expected_revision": old["content_revision"], "text": "Changed draft"},
                )
            else:
                edit = pool.submit(
                    client.put,
                    base + f"/sources/{tone['id']}",
                    headers=owner,
                    json={
                        "expected_version": tone["version"],
                        "title": "New policy",
                        "rule": {"kind": "tone", "guidance": "Changed policy"},
                    },
                )
            changed = edit.result(timeout=4)
            assert changed.status_code == 200, changed.text
            waiting = client.get(base + f"/reviews/{snapshot['id']}", headers=owner).json()
            assert waiting["status"] == "running"
            assert waiting["is_current"] is False
        finally:
            release.set()
        response = pending.result(timeout=10)
    assert response.status_code == 201, response.text
    run = response.json()
    assert run["id"] == snapshot["id"]
    assert run["is_current"] is False
    assert run["caption"] == old["caption"]
    assert run["content_revision"] == old["content_revision"]
    assert run["source_revision"] == old["source_revision"]
    assert run["sources_used"] == old["sources_used"]
    assert packs[0]["draft"] == old["caption"]
    packed_tone = next(source for source in packs[0]["sources"] if source["id"] == tone["id"])
    assert packed_tone["version"] == tone["version"]
    assert packed_tone["text"] == tone["text"]
    assert run["findings"][0]["location"]["quote"] == "Stupid"
    assert run["findings"][0]["evidence"]["source_version"] == tone["version"]
    stored = client.get(base + f"/reviews/{run['id']}", headers=owner).json()
    assert stored["is_current"] is False
    for key in ["caption", "checks", "findings", "sources_used", "excluded_sources"]:
        assert stored[key] == run[key]

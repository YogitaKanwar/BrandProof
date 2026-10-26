def test_source_confirmation_and_edits_preserve_immutable_versions(client, owner, campaign):
    base = f"/api/v1/campaigns/{campaign['id']}/sources"
    response = client.post(
        base,
        headers=owner,
        json={
            "title": "Workshop price",
            "rule": {"kind": "price", "amount": "499", "currency": "INR"},
        },
    )
    assert response.status_code == 201, response.text
    pending = response.json()
    assert pending["status"] == "pending"
    assert pending["version"] == 1
    assert pending["text"] == "The approved campaign price is INR 499."
    confirmed = client.post(
        f"{base}/{pending['id']}/confirm", headers=owner, json={"expected_version": 1}
    )
    assert confirmed.status_code == 200, confirmed.text
    approved = confirmed.json()
    assert approved["status"] == "approved"
    assert approved["version"] == 2
    assert approved["confirmed_by"]
    updated = client.put(
        f"{base}/{pending['id']}",
        headers=owner,
        json={
            "expected_version": 2,
            "title": "Updated workshop price",
            "rule": {"kind": "price", "amount": "599", "currency": "INR"},
        },
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "pending"
    assert updated.json()["version"] == 3
    history = client.get(f"{base}/{pending['id']}/versions", headers=owner).json()
    assert [v["version"] for v in history] == [1, 2, 3]
    assert history[1]["text"] == "The approved campaign price is INR 499."
    assert history[1]["rule"]["amount"] == "499"
    stale = client.post(
        f"{base}/{pending['id']}/confirm", headers=owner, json={"expected_version": 2}
    )
    assert stale.status_code == 409

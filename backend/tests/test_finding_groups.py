from test_ocr import poster_bytes
from test_reviews import add_source, review_copy


def test_findings_group_by_same_rule_without_losing_both_asset_locations(client, owner, campaign):
    source = add_source(
        client, owner, campaign, {"kind": "terminology", "term": "cheap", "preferred": "affordable"}
    )
    run = review_copy(client, owner, campaign, "Our cheap workshop.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    response = client.put(
        base + f"/posters?expected_revision={run['content_revision']}",
        headers={**owner, "Content-Type": "image/png"},
        content=poster_bytes("Our cheap workshop"),
    )
    assert response.status_code == 200
    current = client.get(base, headers=owner).json()
    response = client.post(
        base + "/reviews",
        headers=owner,
        json={
            "expected_content_revision": current["content_revision"],
            "expected_source_revision": current["source_revision"],
        },
    )
    assert response.status_code == 201, response.text
    result = response.json()
    group = next(g for g in result["finding_groups"] if g["category"] == "terminology")
    assert group["source_id"] == source["id"]
    assert group["source_version"] == source["version"]
    assert set(group["assets"]) == {"caption", "poster"}
    assert len(group["finding_ids"]) == 2
    linked = [f for f in result["findings"] if f["id"] in group["finding_ids"]]
    assert all(f["location"]["quote"].lower() == "cheap" for f in linked)
    assert next(f for f in linked if f["location"]["asset"] == "poster")["location"]["boxes"]
    assert (
        client.get(base + f"/reviews/{result['id']}", headers=owner).json()["finding_groups"]
        == result["finding_groups"]
    )

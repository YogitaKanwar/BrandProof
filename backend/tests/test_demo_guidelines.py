"""Actual distributed PDFs -> pending evidence -> owner confirmation -> real review."""

from decimal import Decimal
from pathlib import Path

import pytest
from conftest import headers


@pytest.mark.parametrize(
    ("relative", "count"),
    [("demo/workshop-guidelines.pdf", 3), ("fictional-guidelines.pdf", 7)],
)
def test_public_guidelines_match_workshop_references_and_detect_real_copy_conflicts(
    client, demo, owner, campaign, relative, count
):
    root = Path(__file__).resolve().parents[2]
    # Test the actual shipped asset in both the source checkout and final Docker image.
    choices = [root / "frontend/public" / relative, root / "frontend-dist" / relative]
    asset = next((path for path in choices if path.is_file()), None)
    assert asset is not None, "The distributed PDF must be present"
    base = f"/api/v1/campaigns/{campaign['id']}"
    response = client.post(
        base + "/guideline-documents?expected_source_revision=0",
        headers={**owner, "Content-Type": "application/pdf"},
        content=asset.read_bytes(),
    )
    assert response.status_code == 201
    imported = response.json()
    sources = imported["sources"]
    assert imported["document"]["status"] == "completed"
    assert len(sources) == count
    rules = {source["rule"]["kind"]: source["rule"] for source in sources}
    assert Decimal(rules["price"]["amount"]) == Decimal("899")
    assert rules["price"]["currency"] == "INR"
    assert rules["date"]["date"] == "2026-11-12"
    assert rules["required_text"]["text"] == "Terms apply"
    if count == 7:
        assert rules["terminology"]["term"] == "cheap"
        assert rules["terminology"]["preferred"] == "affordable"
        assert rules["brand_color"]["hex"].upper() == "#FFFFFF"
        assert rules["contrast"]["minimum_ratio"] == 4.5
        assert rules["alt_text"]["required"]
    for source in sources:
        assert source["status"] == "pending" and source["confirmed_by"] is None
        assert source["version"] == 1
        citation = source["document_evidence"]
        page = imported["document"]["pages"][citation["page_number"] - 1]["text"]
        assert page[citation["start"] : citation["end"]] == citation["quote"]

    def save(text):
        current = client.get(base, headers=owner).json()
        response = client.put(
            base + "/caption",
            headers=headers(demo, "creator"),
            json={"text": text, "expected_revision": current["content_revision"]},
        )
        assert response.status_code == 200

    def review():
        current = client.get(base, headers=owner).json()
        response = client.post(
            base + "/reviews",
            headers=headers(demo, "creator"),
            json={
                "expected_content_revision": current["content_revision"],
                "expected_source_revision": current["source_revision"],
                "external_ai_consent": False,
            },
        )
        assert response.status_code == 201
        return response.json()

    save("A cheap workshop on 2026-11-13. Book for INR 599.")
    pending = review()
    assert pending["sources_used"] == []
    assert len(pending["excluded_sources"]) == count
    assert not any(finding["category"] == "price" for finding in pending["findings"])

    for source in sources:
        confirmed = client.post(
            base + "/sources/" + source["id"] + "/confirm",
            headers=owner,
            json={"expected_version": 1},
        )
        assert confirmed.status_code == 200
        confirmed = confirmed.json()
        assert confirmed["version"] == 2 and confirmed["status"] == "approved"
        assert confirmed["document_evidence"] == source["document_evidence"]
    conflict = review()
    expected = {"price", "date", "required_text"}
    if count == 7:
        expected.add("terminology")
    assert expected <= {
        f["category"] for f in conflict["findings"] if f["evidence_status"] == "contradicted"
    }
    price = next(f for f in conflict["findings"] if f["category"] == "price")
    assert price["location"]["quote"] == "INR 599"
    assert "899" in price["evidence"]["quote"]
    assert price["evidence"]["source_version"] == 2

    save("An affordable workshop on 2026-11-12. Book for INR 899. Terms apply.")
    aligned = review()
    assert not any(f["category"] in expected for f in aligned["findings"])
    # A supported rule match is not approval or complete brand/legal compliance.
    receipt = client.get(base + "/receipt", headers=owner).json()
    assert receipt["readiness"] == "not_approved"
    assert receipt["approvals"] == []

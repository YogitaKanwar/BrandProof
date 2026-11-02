"""Additional final acceptance boundaries; all data and decisions are fictional."""

from io import BytesIO

from conftest import headers
from PIL import Image, ImageDraw
from pypdf import PdfWriter
from test_documents import pdf_bytes
from test_reviews import add_source, review_copy


def test_real_image_only_pdf_and_two_supported_pages(client, owner, campaign):
    image = Image.new("RGB", (600, 800), "white")
    ImageDraw.Draw(image).text((40, 40), "Campaign price: INR 899", fill="black")
    scanned = BytesIO()
    image.save(scanned, format="PDF")
    path = f"/api/v1/campaigns/{campaign['id']}/guideline-documents"
    request_headers = {**owner, "Content-Type": "application/pdf"}
    response = client.post(
        path + "?expected_source_revision=0", headers=request_headers, content=scanned.getvalue()
    )
    assert response.status_code == 201
    assert response.json()["document"]["status"] == "unavailable"
    assert response.json()["sources"] == []
    writer = PdfWriter()
    for line in ["Campaign price: INR 899", "Required text: Terms apply"]:
        writer.append(BytesIO(pdf_bytes([line])))
    raw = BytesIO()
    writer.write(raw)
    response = client.post(
        path + "?expected_source_revision=0", headers=request_headers, content=raw.getvalue()
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert len(data["sources"]) == 2
    assert {source["document_evidence"]["page_number"] for source in data["sources"]} == {1, 2}
    assert all(source["status"] == "pending" for source in data["sources"])
    for source in data["sources"]:
        evidence = source["document_evidence"]
        text = data["document"]["pages"][evidence["page_number"] - 1]["text"]
        assert text[evidence["start"] : evidence["end"]] == evidence["quote"]


def test_zero_through_six_reviewed_snapshots_and_missing_reason(client, demo, owner, campaign):
    endpoint = "/api/v1/governance-insights"
    empty = client.get(endpoint, headers=owner).json()
    assert empty["categories"] == empty["guidelines"] == []
    assert empty["snapshots_considered"] == 0
    add_source(client, owner, campaign, {"kind": "price", "currency": "INR", "amount": "899"})
    for count in range(1, 7):
        run = review_copy(client, owner, campaign, "Book for INR 599." + " " * count)
        finding = next(row for row in run["findings"] if row["category"] == "price")
        path = f"/api/v1/campaigns/{campaign['id']}/reviews/{run['id']}/findings/{finding['id']}/decisions"
        payload = {
            "expected_content_revision": run["content_revision"],
            "expected_source_revision": run["source_revision"],
            "expected_decision_version": 0,
            "decision": "exception",
            "reason": "   ",
        }
        assert client.post(path, headers=headers(demo, "reviewer"), json=payload).status_code == 422
        payload["reason"] = "Fictional QA exception to exercise sample boundaries, not approval."
        assert client.post(path, headers=headers(demo, "reviewer"), json=payload).status_code == 201
        row = client.get(endpoint, headers=owner).json()["guidelines"][0]
        assert row["reviewed"] == row["reviewed_snapshots"] == row["observations"] == count
        assert row["decision_rate"] == (None if count < 5 else 1)
        assert row["potentially_ambiguous"] == (count >= 5)
        assert all(entry["reason"] == payload["reason"] for entry in row["evidence"])
        assert client.get(endpoint, headers=owner).json()["guidelines"][0] == row


def test_decision_truncation_is_disclosed(client, demo, owner, campaign, monkeypatch):
    from brandproof import insights

    add_source(client, owner, campaign, {"kind": "price", "currency": "INR", "amount": "899"})
    for index in range(2):
        run = review_copy(client, owner, campaign, "Book for INR 599." + " " * index)
        finding = next(row for row in run["findings"] if row["category"] == "price")
        response = client.post(
            f"/api/v1/campaigns/{campaign['id']}/reviews/{run['id']}/findings/{finding['id']}/decisions",
            headers=headers(demo, "reviewer"),
            json={
                "expected_content_revision": run["content_revision"],
                "expected_source_revision": run["source_revision"],
                "expected_decision_version": 0,
                "decision": "dismiss",
                "reason": "Fictional QA-only reason for truncation acceptance.",
            },
        )
        assert response.status_code == 201
    monkeypatch.setattr(insights, "MAX_DECISIONS", 1)
    data = client.get("/api/v1/governance-insights", headers=owner).json()
    assert data["truncated"] is True
    assert data["guidelines"][0]["decision_rate"] is None

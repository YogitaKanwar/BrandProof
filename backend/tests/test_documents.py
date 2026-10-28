from io import BytesIO

from conftest import headers
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def pdf_bytes(lines=None, encrypted=False):
    writer = PdfWriter()
    page = writer.add_blank_page(width=600, height=800)
    if lines:
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
        )
        stream = DecodedStreamObject()
        stream.set_data(
            (
                "BT /F1 16 Tf 40 750 Td "
                + " 0 -24 Td ".join(
                    "("
                    + line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                    + ") Tj"
                    for line in lines
                )
                + " ET"
            ).encode()
        )
        page[NameObject("/Contents")] = writer._add_object(stream)
    if encrypted:
        writer.encrypt("private")
    result = BytesIO()
    writer.write(result)
    return result.getvalue()


def test_import_creates_pending_page_cited_sources_then_confirmation_preserves_evidence(
    client, demo, owner, campaign
):
    base = f"/api/v1/campaigns/{campaign['id']}"
    raw = pdf_bytes(
        [
            "Campaign price: INR 499",
            "Tone: Use a calm voice.",
            "Unstructured material is not guessed.",
        ]
    )
    response = client.post(
        base + "/guideline-documents?expected_source_revision=0",
        headers={**owner, "Content-Type": "application/pdf", "X-BrandProof-Filename": "brand.pdf"},
        content=raw,
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["sources"]) == 2
    first = data["sources"][0]
    assert first["status"] == "pending" and first["confirmed_by"] is None
    citation = first["document_evidence"]
    page = data["document"]["pages"][0]["text"]
    assert (
        page[citation["start"] : citation["end"]] == citation["quote"] == "Campaign price: INR 499"
    )
    confirmed = client.post(
        base + "/sources/" + first["id"] + "/confirm", headers=owner, json={"expected_version": 1}
    ).json()
    assert confirmed["status"] == "approved" and confirmed["document_evidence"] == citation
    versions = client.get(base + "/sources/" + first["id"] + "/versions", headers=owner).json()
    assert [v["version"] for v in versions] == [1, 2]
    assert versions[0]["document_evidence"] == versions[1]["document_evidence"]
    assert (
        client.post(
            base + "/guideline-documents?expected_source_revision=0",
            headers={**owner, "Content-Type": "application/pdf"},
            content=raw,
        ).status_code
        == 409
    )
    assert (
        client.post(
            base + "/guideline-documents?expected_source_revision=3",
            headers={**headers(demo, "creator"), "Content-Type": "application/pdf"},
            content=raw,
        ).status_code
        == 403
    )


def test_blank_scan_and_unsupported_pdf_never_invent_sources(client, owner, campaign):
    path = f"/api/v1/campaigns/{campaign['id']}/guideline-documents?expected_source_revision=0"
    response = client.post(
        path, headers={**owner, "Content-Type": "application/pdf"}, content=pdf_bytes()
    )
    assert response.status_code == 201
    assert response.json()["document"]["status"] == "unavailable"
    assert response.json()["sources"] == []
    for raw in [b"not a PDF", pdf_bytes(["Campaign price: INR 499"], encrypted=True)]:
        assert (
            client.post(
                path, headers={**owner, "Content-Type": "application/pdf"}, content=raw
            ).status_code
            == 422
        )
    assert (
        client.post(
            path, headers={**owner, "Content-Type": "text/plain"}, content=b"text"
        ).status_code
        == 415
    )
    assert (
        client.post(
            path,
            headers={**owner, "Content-Type": "application/pdf"},
            content=b"%PDF-" + b"x" * (5 * 1024 * 1024),
        ).status_code
        == 413
    )

"""Real HTTP feature acceptance on a fictional workspace. No credentials persisted."""

import argparse
import io
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from workflow_smoke import fixture_font


def pdf_fixture():
    writer = PdfWriter()
    page = writer.add_blank_page(width=600, height=800)
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
        b"BT /F1 16 Tf 40 750 Td (Campaign price: INR 499) Tj 0 -24 Td (Background colour: #FFFFFF) Tj 0 -24 Td (Alt text: required) Tj ET"
    )
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8013")
    args = parser.parse_args()
    tokens = {}

    def call(method, path, payload=None, raw=None, mime=None, role="creator", expected=200):
        headers = {"Content-Type": mime or "application/json"}
        if tokens:
            headers["Authorization"] = "Bearer " + tokens[role]["access_token"]
        data = (
            raw
            if raw is not None
            else json.dumps(payload).encode()
            if payload is not None
            else None
        )
        try:
            with urlopen(
                Request(
                    args.base_url + "/api/v1" + path, method=method, headers=headers, data=data
                ),
                timeout=90,
            ) as response:
                assert response.status == expected
                return json.load(response)
        except HTTPError as error:
            assert error.code == expected, f"Unexpected HTTP {error.code}"
            return json.load(error)

    tokens.update(call("POST", "/demo-sessions", expected=201)["actors"])
    campaign = call(
        "POST",
        "/campaigns",
        {"name": "Fictional improvements acceptance", "publication_date": "2026-11-12"},
        expected=201,
    )
    base = "/campaigns/" + campaign["id"]
    document = call(
        "POST",
        base + "/guideline-documents?expected_source_revision=0",
        raw=pdf_fixture(),
        mime="application/pdf",
        role="owner",
        expected=201,
    )
    assert len(document["sources"]) == 3
    for source in document["sources"]:
        assert source["status"] == "pending"
        citation = source["document_evidence"]
        assert (
            document["document"]["pages"][citation["page_number"] - 1]["text"][
                citation["start"] : citation["end"]
            ]
            == citation["quote"]
        )
        approved = call(
            "POST",
            base + "/sources/" + source["id"] + "/confirm",
            {"expected_version": 1},
            role="owner",
        )
        assert approved["document_evidence"] == citation
    call(
        "PUT",
        base + "/caption",
        {"expected_revision": 1, "text": "Book for INR 599. Guaranteed results in 30 days."},
    )
    image = Image.new("RGB", (1400, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.text((35, 40), "Book for INR 599.", font=fixture_font(60), fill="black")
    draw.text((35, 150), "Guaranteed results in 30 days.", font=fixture_font(60), fill="black")
    output = io.BytesIO()
    image.save(output, format="PNG")
    poster = call(
        "PUT", base + "/posters?expected_revision=2", raw=output.getvalue(), mime="image/png"
    )

    def review():
        current = call("GET", base)
        return call(
            "POST",
            base + "/reviews",
            {
                "expected_content_revision": current["content_revision"],
                "expected_source_revision": current["source_revision"],
                "external_ai_consent": False,
            },
            expected=201,
        )

    run = review()
    assert any(f["category"] == "alt_text" for f in run["findings"])
    assert any(
        f["category"] == "claim_risk"
        and f["location"]["asset"] == "poster"
        and f["location"]["boxes"]
        for f in run["findings"]
    )
    assert any(f.get("unverified_draft_suggestion") for f in run["findings"])
    assert (
        run["checks"]["poster"]["details"]["measured_checks"]["visual"]["observed_hex"] == "#FFFFFF"
    )
    call(
        "PUT",
        base + "/alt-text",
        {
            "expected_revision": 3,
            "text": "Fictional workshop poster: Book for INR 599. Guaranteed results in 30 days; this claim requires review.",
        },
    )
    assert call("GET", base + "/reviews/" + run["id"])["is_current"] is False
    run = review()
    assert not any(f["category"] == "alt_text" for f in run["findings"])
    snapshot = {
        "expected_content_revision": run["content_revision"],
        "expected_source_revision": run["source_revision"],
    }
    guide = call("GET", base + "/readiness", role="reviewer")
    assert any(b["code"] == "finding_unresolved" for b in guide["blockers"])
    for finding in run["findings"]:
        if finding["severity"] == "error" or finding["evidence_status"] in {
            "needs_clarification",
            "insufficient_evidence",
        }:
            call(
                "POST",
                base + "/reviews/" + run["id"] + "/findings/" + finding["id"] + "/decisions",
                {
                    **snapshot,
                    "expected_decision_version": 0,
                    "decision": "exception",
                    "reason": "Scripted fictional acceptance exception; not evidence of actual claim support.",
                },
                role="reviewer",
                expected=201,
            )
    request = call("POST", base + "/reviews/" + run["id"] + "/requests", snapshot, expected=201)
    required = ["exact_text", "contextual", "claim_risk", "poster"]
    notes = {
        name: "Scripted workflow attestation for "
        + name
        + "; not actual independent human feedback."
        for name in required
        if run["checks"][name]["status"] != "completed"
    }
    call(
        "POST",
        base + "/reviews/" + run["id"] + "/approvals",
        {
            **snapshot,
            "request_id": request["id"],
            "decision": "approve",
            "reason": "Scripted fictional acceptance; no real campaign publication authorized.",
            "manual_checks": notes,
        },
        role="reviewer",
        expected=201,
    )
    assert call("GET", base + "/receipt")["readiness"] == "approved_with_manual_checks"
    assert call("GET", base + "/readiness", role="reviewer")["blockers"] == []
    insights = call("GET", "/governance-insights")
    assert insights["guidelines"] and all(
        row["decision_rate"] is None for row in insights["guidelines"]
    )
    call("POST", base + "/caption/clear", {"expected_revision": 4})
    assert call("GET", base + "/receipt")["readiness"] == "stale"
    assert call("GET", base + "/posters")["id"] == poster["id"]
    print(
        json.dumps(
            {
                "pdf_pending_provenance": "passed",
                "poster_claim_boxes": "passed",
                "unverified_drafts": "passed",
                "measured_background": "passed",
                "alt_text_revisions": "passed",
                "readiness_and_governance": "passed",
                "sources_content_findings_human_review": "passed",
                "credentials_written": False,
            }
        )
    )


if __name__ == "__main__":
    main()

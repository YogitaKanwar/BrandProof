from io import BytesIO

import pytest
from brandproof.claim_screening import MAX_FINDINGS, combined_coverage, screen_claims
from conftest import headers
from PIL import Image, ImageDraw
from test_ocr import fixture_font
from test_reviews import add_source, review_copy
from test_workflow import expectation


@pytest.mark.parametrize(
    "text",
    [
        "Guaranteed results in 30 days.",
        "Results guaranteed.",
        "Success is guaranteed.",
        "We guarantee positive results.",
        "You will definitely see results within a month.",
        "You will certainly achieve success.",
        "Visible results after two weeks.",
        "Results within just 7 days.",
        "100% safe.",
        "100 % effective.",
        "Works for everyone.",
        "This never fails.",
        "Zero side effects.",
        "Lose 10 kg in 30 days.",
        "Boost your sales by 50%.",
        "Reduce costs by 25%.",
        "🚀 GUARANTEED\nRESULTS IN 30 DAYS!",
        "Guaranteed results in 30 days. Individual results may vary.",
        "Guaranteed placement after the course.",
        "100% placement guarantee.",
        "Guaranteed admission.",
        "Guaranteed cure within a week.",
    ],
)
def test_promises_need_evidence_review_without_a_brand_source(text):
    findings, check = screen_claims(text, 3)
    assert findings and check["status"] == "partial"
    for item in findings:
        assert item["category"] == "claim_risk"
        assert item["evidence_status"] == "needs_clarification"
        assert item["evidence"] is None and item["suggested_replacement"] is None
        assert item["location"]["content_revision"] == 3
        assert (
            text[item["location"]["start"] : item["location"]["end"]] == item["location"]["quote"]
        )
        assert "does not establish" in item["message"]


@pytest.mark.parametrize(
    "text",
    [
        "Workshop on 2026-11-12. Book for INR 499. Terms apply.",
        "The course lasts 30 days.",
        "Delivery within 7 days.",
        "30-day money-back guarantee. Terms apply.",
        "Results may vary.",
        "Results are not guaranteed.",
        "No guaranteed results.",
        "We do not guarantee results in 30 days.",
        "We cannot guarantee results within a month.",
        "We can't promise results in 30 days.",
        "We may see results within a month.",
        "We aim to achieve results in 30 days.",
        "Avoid saying guaranteed results.",
        "100% cotton.",
        "Save 20% on workshop tickets.",
        "Red Bull gives you wings.",
        "A workshop that opens doors.",
        "Placement assistance is available.",
    ],
)
def test_ordinary_copy_and_explicit_local_disclaimers_do_not_trigger(text):
    findings, check = screen_claims(text, 1)
    assert findings == []
    assert check["status"] == "completed"
    assert "does not verify" in check["reason"]


def test_overlapping_signals_form_one_precise_review_prompt():
    text = "🚀 Guaranteed results in 30 days."
    findings, _ = screen_claims(text, 1)
    assert len(findings) == 1
    assert findings[0]["location"]["quote"] == "Guaranteed results in 30 days"
    assert (
        "guaranteed outcome" in findings[0]["message"]
        and "time-bound outcome" in findings[0]["message"]
    )


def test_bounded_screen_never_calls_a_truncated_scan_complete():
    findings, check = screen_claims("Guaranteed results. " * 2000, 1)
    assert len(findings) == MAX_FINDINGS
    assert check["status"] == "partial" and check["details"]["limited"]
    assert check["details"]["scanned_characters"] == 20000
    combined = combined_coverage(check)
    assert combined["status"] == "partial" and combined["details"]["limited"]
    assert "Screening limit reached" in combined["reason"]
    assert screen_claims("", 1)[1]["status"] == "not_assessed"


def test_real_api_flags_and_persists_claims_with_ai_off_and_no_sources(client, owner, campaign):
    run = review_copy(client, owner, campaign, "Guaranteed results in 30 days.")
    assert run["checks"]["contextual"]["status"] == "unavailable"
    assert run["checks"]["exact_text"]["status"] == "not_assessed"
    assert run["checks"]["claim_risk"]["status"] == "partial"
    assert run["checks"]["claim_risk"]["details"]["version"] == "claim-risk-v1"
    assert run["sources_used"] == []
    assert len(run["findings"]) == 1 and run["readiness"] == "not_approved"
    base = f"/api/v1/campaigns/{campaign['id']}"
    saved = client.get(f"{base}/reviews/{run['id']}", headers=owner).json()
    assert saved["findings"] == run["findings"] and saved["checks"] == run["checks"]
    corrected = review_copy(client, owner, campaign, "The workshop lasts 30 days.")
    assert (
        corrected["findings"] == [] and corrected["checks"]["claim_risk"]["status"] == "completed"
    )
    assert corrected["readiness"] == "not_approved"
    assert client.get(f"{base}/reviews/{run['id']}", headers=owner).json()["is_current"] is False


def test_real_poster_screen_maps_claim_to_actual_ocr_boxes_without_sources(client, owner, campaign):
    image = Image.new("RGB", (1200, 220), "white")
    ImageDraw.Draw(image).text(
        (35, 60), "Guaranteed results in 30 days.", font=fixture_font(55), fill="black"
    )
    output = BytesIO()
    image.save(output, format="PNG")
    base = f"/api/v1/campaigns/{campaign['id']}"
    upload = client.put(
        base + "/posters?expected_revision=1",
        headers={**owner, "Content-Type": "image/png"},
        content=output.getvalue(),
    )
    assert upload.status_code == 200
    response = client.post(
        base + "/reviews",
        headers=owner,
        json={"expected_content_revision": 2, "expected_source_revision": 0},
    )
    assert response.status_code == 201, response.text
    run = response.json()
    finding = next(item for item in run["findings"] if item["category"] == "claim_risk")
    assert (
        finding["location"]["asset"] == "poster"
        and finding["location"]["poster_id"] == upload.json()["id"]
    )
    assert len(finding["location"]["boxes"]) >= 4
    assert finding["evidence"] is None and finding["evidence_status"] == "needs_clarification"
    assert run["checks"]["claim_risk"]["status"] == "partial"


def test_claim_flag_requires_human_disposition_and_dedicated_manual_notes(
    client, demo, owner, campaign
):
    add_source(
        client,
        owner,
        campaign,
        {
            "kind": "claim_policy",
            "guidance": "Outcome claims require owner approval and documented support.",
        },
    )
    run = review_copy(client, owner, campaign, "Guaranteed results in 30 days.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    req = client.post(
        f"{base}/reviews/{run['id']}/requests", headers=owner, json=expectation(run)
    ).json()
    payload = {
        **expectation(run),
        "request_id": req["id"],
        "decision": "approve",
        "reason": "Synthetic workflow test; not real campaign authorisation.",
        "manual_checks": {
            "exact_text": "No exact facts were supplied; manually inspected the caption.",
            "contextual": "No AI inference used; manually compared the supplied policy.",
        },
    }
    url = f"{base}/reviews/{run['id']}/approvals"
    assert (
        client.post(url, headers=headers(demo, "reviewer"), json=payload).json()["error"]["code"]
        == "unresolved_findings"
    )
    finding = run["findings"][0]
    result = client.post(
        f"{base}/reviews/{run['id']}/findings/{finding['id']}/decisions",
        headers=headers(demo, "reviewer"),
        json={
            **expectation(run),
            "expected_decision_version": 0,
            "decision": "exception",
            "reason": "Synthetic QA exception only; verifies workflow enforcement.",
        },
    )
    assert result.status_code == 201
    assert (
        client.post(url, headers=headers(demo, "reviewer"), json=payload).json()["error"]["code"]
        == "checks_incomplete"
    )
    payload["manual_checks"]["claim_risk"] = (
        "Synthetic QA: inspected the flagged phrase and recorded this explicit test-only exception. No real outcome is certified."
    )
    approved = client.post(url, headers=headers(demo, "reviewer"), json=payload)
    assert approved.status_code == 201, approved.text
    receipt = client.get(base + "/receipt", headers=owner).json()
    assert receipt["readiness"] == "approved_with_manual_checks"
    assert (
        receipt["approvals"][0]["manual_checks"]["claim_risk"]
        == payload["manual_checks"]["claim_risk"]
    )
    assert (
        client.get(f"{base}/reviews/{run['id']}", headers=owner).json()["findings"][0]["category"]
        == "claim_risk"
    )

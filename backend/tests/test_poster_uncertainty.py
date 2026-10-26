"""OCR uncertainty must survive poster findings, coverage and persisted reviews."""

import pytest
from brandproof import ocr
from brandproof.models import Campaign
from brandproof.poster_review import review_poster
from test_ocr import poster_bytes
from test_reviews import add_source, review_copy


@pytest.fixture(autouse=True)
def disable_external_ai(monkeypatch):
    monkeypatch.setenv("BRANDPROOF_AI_PROVIDER", "none")
    monkeypatch.setenv("BRANDPROOF_EXTERNAL_AI_ENABLED", "false")
    monkeypatch.setenv("BRANDPROOF_AI_API_KEY", "")


def _review_with_ocr(client, owner, campaign, monkeypatch, rules, rows):
    sources = [add_source(client, owner, campaign, rule) for rule in rules]
    prior = review_copy(client, owner, campaign, "Terms apply. An affordable workshop.")
    if rows is not None:
        raw = ("level\tleft\ttop\twidth\theight\tconf\ttext\n" + rows).encode()
        monkeypatch.setattr(ocr, "_run_tesseract", lambda png: raw)
    base = f"/api/v1/campaigns/{campaign['id']}"
    upload = client.put(
        base + f"/posters?expected_revision={prior['content_revision']}",
        headers={**owner, "Content-Type": "image/png"},
        content=poster_bytes("Terms apply"),
    )
    assert upload.status_code == 200, upload.text
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
    run = response.json()
    saved = client.get(base + f"/reviews/{run['id']}", headers=owner)
    assert saved.status_code == 200, saved.text
    assert saved.json()["checks"] == run["checks"]
    assert saved.json()["findings"] == run["findings"]
    findings = [finding for finding in run["findings"] if finding["location"]["asset"] == "poster"]
    assert all(finding["suggested_replacement"] is None for finding in findings)
    assert client.get(base + "/posters", headers=owner).json()["id"] == upload.json()["id"]
    assert client.get(base, headers=owner).json()["content_revision"] == current["content_revision"]
    return findings, run["checks"]["poster"], sources


def test_partial_ocr_cannot_prove_required_wording_absent(client, owner, campaign, monkeypatch):
    findings, check, sources = _review_with_ocr(
        client,
        owner,
        campaign,
        monkeypatch,
        [{"kind": "required_text", "text": "Terms apply"}],
        "5\t2\t3\t15\t10\t10\tcheap\n",
    )
    assert check["details"]["ocr_status"] == "partial"
    assert len(findings) == 1
    finding = findings[0]
    assert finding["category"] == "required_text"
    assert finding["location"]["start"] is None
    assert finding["location"]["end"] is None
    assert finding["location"]["boxes"] == []
    assert finding["location"]["ocr_confidence"] is None
    assert finding["evidence_status"] == "needs_clarification"
    assert finding["severity"] == "warning"
    assert "image" in finding["message"].lower()
    assert "incomplete ocr" in finding["message"].lower()
    assert finding["evidence"]["source_id"] == sources[0]["id"]
    assert finding["evidence"]["source_version"] == sources[0]["version"]


def test_uncertain_findings_make_only_their_source_coverage_partial(
    client, owner, campaign, monkeypatch
):
    findings, check, sources = _review_with_ocr(
        client,
        owner,
        campaign,
        monkeypatch,
        [
            {"kind": "terminology", "term": "cheap", "preferred": "affordable"},
            {"kind": "terminology", "term": "costly", "preferred": "premium"},
            {"kind": "required_text", "text": "Terms apply"},
        ],
        "5\t2\t3\t15\t10\t10\tcheap\n5\t20\t3\t15\t10\t95\tcostly\n",
    )
    by_source = {finding["evidence"]["source_id"]: finding for finding in findings}
    assert by_source[sources[0]["id"]]["evidence_status"] == "needs_clarification"
    assert by_source[sources[0]["id"]]["location"]["ocr_confidence"] == 0.1
    assert by_source[sources[0]["id"]]["location"]["boxes"]
    assert by_source[sources[1]["id"]]["evidence_status"] == "contradicted"
    assert by_source[sources[1]["id"]]["severity"] == "error"
    assert by_source[sources[2]["id"]]["evidence_status"] == "needs_clarification"
    coverage = {(rule["source_id"], rule["source_version"]): rule for rule in check["rules"]}
    for index, expected in enumerate(("partial", "completed", "partial")):
        source = sources[index]
        rule = coverage[(source["id"], source["version"])]
        assert rule["status"] == expected
        if expected == "partial":
            assert "visual" in rule["reason"].lower()
    assert check["details"]["exact_text_status"] == "partial"


@pytest.mark.parametrize(
    "rules",
    [
        [{"kind": "required_text", "text": "Terms apply"}],
        [{"kind": "terminology", "term": "cheap", "preferred": "affordable"}],
        [],
    ],
    ids=["required-wording-present", "prohibited-word-absent", "no-exact-rules"],
)
def test_partial_extraction_cannot_claim_clean_exact_text_without_findings(
    client, owner, campaign, monkeypatch, rules
):
    findings, check, _ = _review_with_ocr(
        client,
        owner,
        campaign,
        monkeypatch,
        rules,
        "5\t2\t3\t100\t10\t10\tTerms apply\n",
    )
    assert findings == []
    assert check["details"]["ocr_status"] == "partial"
    assert check["details"]["exact_text_status"] == "partial"


@pytest.mark.parametrize(
    "missing_tool,expected_status,expected_reason",
    [(False, "partial", "unreadable"), (True, "unavailable", "tool_missing")],
    ids=["unreadable-image", "ocr-tool-unavailable"],
)
def test_no_extracted_text_exposes_incomplete_exact_text_status(
    client, owner, campaign, monkeypatch, missing_tool, expected_status, expected_reason
):
    if missing_tool:

        def missing_executable(png):
            raise FileNotFoundError("Synthetic missing OCR executable")

        monkeypatch.setattr(ocr, "_run_tesseract", missing_executable)
    findings, check, _ = _review_with_ocr(
        client,
        owner,
        campaign,
        monkeypatch,
        [{"kind": "required_text", "text": "Terms apply"}],
        None if missing_tool else "",
    )
    assert findings == []
    assert check["status"] == expected_status
    assert check["details"]["ocr_status"] == expected_status
    assert check["details"]["ocr_reason"] == expected_reason
    assert check["details"]["exact_text_status"] == expected_status
    assert "manually" in check["reason"]


def test_no_poster_remains_not_assessed(client, owner, campaign):
    run = review_copy(client, owner, campaign, "Terms apply.")
    check = run["checks"]["poster"]
    assert check["status"] == "not_assessed"
    assert check["details"] == {}
    assert not any(finding["location"]["asset"] == "poster" for finding in run["findings"])


@pytest.mark.parametrize("confidence", [70, 95], ids=["confidence-boundary", "high-confidence"])
def test_completed_ocr_keeps_supported_missing_wording_finding(
    client, owner, campaign, monkeypatch, confidence
):
    findings, check, _ = _review_with_ocr(
        client,
        owner,
        campaign,
        monkeypatch,
        [{"kind": "required_text", "text": "Terms apply"}],
        f"5\t2\t3\t15\t10\t{confidence}\tcheap\n",
    )
    assert len(findings) == 1
    assert findings[0]["evidence_status"] == "contradicted"
    assert findings[0]["severity"] == "error"
    assert check["rules"][0]["status"] == "completed"
    assert check["details"]["ocr_status"] == "completed"
    assert check["details"]["exact_text_status"] == "completed"
    assert check["status"] == "partial"  # Never claim a full visual assessment.


def test_completed_ocr_without_exact_rules_remains_not_assessed(
    client, owner, campaign, monkeypatch
):
    findings, check, _ = _review_with_ocr(
        client, owner, campaign, monkeypatch, [], "5\t2\t3\t15\t10\t95\tcheap\n"
    )
    assert findings == []
    assert check["rules"] == []
    assert check["details"]["ocr_status"] == "completed"
    assert check["details"]["exact_text_status"] == "not_assessed"


def test_coverage_reconciliation_distinguishes_versions_of_one_source(
    client, owner, campaign, monkeypatch
):
    _, _, sources = _review_with_ocr(
        client,
        owner,
        campaign,
        monkeypatch,
        [{"kind": "terminology", "term": "cheap", "preferred": "affordable"}],
        "5\t2\t3\t15\t10\t10\tcheap\n5\t20\t3\t15\t10\t95\tcostly\n",
    )
    old = sources[0]
    url = f"/api/v1/campaigns/{campaign['id']}/sources/{old['id']}"
    changed = client.put(
        url,
        headers=owner,
        json={
            "expected_version": old["version"],
            "title": "Revised terminology",
            "rule": {"kind": "terminology", "term": "costly", "preferred": "premium"},
        },
    )
    assert changed.status_code == 200, changed.text
    confirmed = client.post(
        url + "/confirm",
        headers=owner,
        json={"expected_version": changed.json()["version"]},
    )
    assert confirmed.status_code == 200, confirmed.text
    new = confirmed.json()
    # Exercise the reconciliation seam with two real immutable source versions.
    with client.app.state.sessions() as session:
        findings, check = review_poster(
            session, session.get(Campaign, campaign["id"]), [old, new], []
        )
    assert old["id"] == new["id"]
    assert old["version"] != new["version"]
    coverage = {(rule["source_id"], rule["source_version"]): rule for rule in check["rules"]}
    assert coverage[(old["id"], old["version"])]["status"] == "partial"
    assert coverage[(new["id"], new["version"])]["status"] == "completed"
    assert {finding["evidence"]["source_version"] for finding in findings} == {
        old["version"],
        new["version"],
    }

import hashlib
from pathlib import Path

import pytest
from brandproof import legal
from brandproof.main import create_app
from conftest import headers
from fastapi.testclient import TestClient
from pypdf import PdfReader
from test_claim_screening import fixture_font
from test_reviews import add_source, review_copy
from test_workflow import expectation


def set_profile(client, owner, campaign, **changes):
    base = f"/api/v1/campaigns/{campaign['id']}"
    current = client.get(base, headers=owner).json()
    profile = {"jurisdiction": "IN", "sector": "general", "language": "en", **changes}
    response = client.put(
        base + "/advertising-profile",
        headers=owner,
        json={
            "expected_content_revision": current["content_revision"],
            "expected_source_revision": current["source_revision"],
            **profile,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_pack_quote_and_digest_match_checked_official_pdf():
    path = Path(__file__).parent / "fixtures/ccpa-2022.pdf"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == legal.PACK["source_sha256"]
    rule = legal.PACK["rules"][0]
    text = " ".join(PdfReader(path).pages[rule["page"] - 1].extract_text().split())
    assert rule["quote"] in text and rule["clause"] == "12(a)"


@pytest.mark.parametrize(
    "text,flagged",
    [
        ("Guaranteed results in 30 days.", True),
        ("🚀 Guaranteed results in 30 days. T&Cs apply.", True),
        ("100% selection guaranteed.", True),
        ("Guaranteed placement after the course.", True),
        ("Results within 30 days.", True),
        ("Works for everyone.", True),
        ("No results are guaranteed.", False),
        ("Results are not guaranteed.", False),
        ("Do not say ‘guaranteed results’.", False),
        ("We may see results in 30 days.", False),
        ("30-day money-back guarantee.", False),
        ("Red Bull gives you wings.", False),
        ("100% cotton. Delivery within 30 days.", False),
    ],
)
def test_cited_risk_signals_are_bounded_and_do_not_duplicate_claims(
    client, owner, campaign, text, flagged
):
    set_profile(client, owner, campaign)
    run = review_copy(client, owner, campaign, text)
    risk = [f for f in run["findings"] if f.get("regulatory_evidence")]
    assert bool(risk) is flagged
    assert len(risk) == len([f for f in run["findings"] if f["category"] == "claim_risk"])
    check = run["checks"]["advertising_risk"]
    assert check["status"] == ("partial" if flagged else "completed")
    assert check["details"]["pack"]["version"] == legal.PACK["version"]
    for finding in risk:
        assert finding["evidence"] is None  # Never mislabel regulation as owner evidence.
        assert finding["regulatory_evidence"]["id"] == "IN-CCPA-2022-12A"
        loc = finding["location"]
        assert text[loc["start"] : loc["end"]] == loc["quote"]
    assert run["readiness"] == "not_approved"


@pytest.mark.parametrize(
    "profile,status",
    [
        ({"jurisdiction": "unknown"}, "not_assessed"),
        ({"jurisdiction": "other"}, "not_applicable"),
        ({"language": "other"}, "not_assessed"),
        ({"sector": "coaching"}, "partial"),
        ({"sector": "healthcare"}, "partial"),
    ],
)
def test_profile_applicability_is_explicit(client, owner, campaign, profile, status):
    set_profile(client, owner, campaign, **profile)
    run = review_copy(client, owner, campaign, "An ordinary workshop announcement.")
    assert run["checks"]["advertising_risk"]["status"] == status


def test_unset_profile_roles_conflicts_and_workspace_isolation(client, demo, owner, campaign):
    base = f"/api/v1/campaigns/{campaign['id']}"
    assert client.get(base + "/advertising-profile", headers=owner).json()["profile"] is None
    run = review_copy(client, owner, campaign, "Guaranteed results.")
    assert run["checks"]["advertising_risk"]["status"] == "not_assessed"
    assert not run["findings"][0]["regulatory_evidence"]
    payload = {**expectation(run), "jurisdiction": "IN", "sector": "general", "language": "en"}
    for role in ("creator", "reviewer"):
        assert (
            client.put(
                base + "/advertising-profile", headers=headers(demo, role), json=payload
            ).status_code
            == 403
        )
    assert client.put(base + "/advertising-profile", headers=owner, json=payload).status_code == 200
    assert client.put(base + "/advertising-profile", headers=owner, json=payload).status_code == 409
    other = client.post("/api/v1/demo-sessions").json()
    assert client.get(base + "/advertising-profile", headers=headers(other)).status_code == 404
    assert (
        client.put(base + "/advertising-profile", headers=headers(other), json=payload).status_code
        == 404
    )


def test_evidence_review_approval_profile_and_pack_staleness(
    client, demo, owner, campaign, monkeypatch
):
    set_profile(client, owner, campaign)
    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    run = review_copy(client, owner, campaign, "Guaranteed results in 30 days. Terms apply.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    snap = expectation(run)
    req = client.post(
        base + f"/reviews/{run['id']}/requests", headers=headers(demo, "creator"), json=snap
    ).json()
    payload = {
        **snap,
        "request_id": req["id"],
        "decision": "approve",
        "reason": "Synthetic QA of a human decision, not real substantiation.",
        "manual_checks": {
            "contextual": "Synthetic reviewer manually checked the contextual scope.",
            "claim_risk": "Synthetic reviewer checked the promise and its supporting test evidence.",
            "advertising_risk": "Synthetic reviewer examined clause 12(a); test reference QA-001, not actual legal clearance.",
        },
    }
    url = base + f"/reviews/{run['id']}/approvals"
    assert (
        client.post(url, headers=headers(demo, "reviewer"), json=payload).json()["error"]["code"]
        == "unresolved_findings"
    )
    finding = run["findings"][0]
    assert (
        client.post(
            base + f"/reviews/{run['id']}/findings/{finding['id']}/decisions",
            headers=headers(demo, "reviewer"),
            json={
                **snap,
                "expected_decision_version": 0,
                "decision": "exception",
                "reason": "Synthetic QA-only evidence reference QA-001; this does not waive regulation.",
            },
        ).status_code
        == 201
    )
    missing = {
        **payload,
        "manual_checks": {
            k: v for k, v in payload["manual_checks"].items() if k != "advertising_risk"
        },
    }
    assert (
        client.post(url, headers=headers(demo, "reviewer"), json=missing).json()["error"]["code"]
        == "checks_incomplete"
    )
    approved = client.post(url, headers=headers(demo, "reviewer"), json=payload)
    assert approved.status_code == 201, approved.text
    snapshot = approved.json()["advertising_snapshot"]
    assert snapshot["details"]["pack"]["version"] == legal.PACK["version"]
    assert (
        client.get(base + "/receipt", headers=owner).json()["readiness"]
        == "approved_with_manual_checks"
    )
    original_digest = legal.PACK_DIGEST
    monkeypatch.setattr(legal, "PACK_DIGEST", "new-installed-version")
    assert not client.get(base + f"/reviews/{run['id']}", headers=owner).json()["is_current"]
    assert client.get(base + "/receipt", headers=owner).json()["readiness"] == "stale"
    assert (
        client.post(base + f"/reviews/{run['id']}/requests", headers=owner, json=snap).status_code
        == 409
    )
    monkeypatch.setattr(legal, "PACK_DIGEST", original_digest)
    set_profile(client, owner, campaign, sector="coaching")
    receipt = client.get(base + "/receipt", headers=owner).json()
    assert receipt["readiness"] == "stale"
    assert receipt["approvals"][0]["advertising_snapshot"] == snapshot


def test_expired_pack_pauses_screening_and_stales_existing_run(
    client, owner, campaign, monkeypatch
):
    set_profile(client, owner, campaign)
    run = review_copy(client, owner, campaign, "Guaranteed results.")
    monkeypatch.setitem(legal.PACK, "review_due", "2000-01-01")
    stored = client.get(
        f"/api/v1/campaigns/{campaign['id']}/reviews/{run['id']}", headers=owner
    ).json()
    assert not stored["is_current"]
    rerun = review_copy(client, owner, campaign, "Guaranteed results.")
    assert rerun["checks"]["advertising_risk"]["status"] == "partial"
    assert all(not f["regulatory_evidence"] for f in rerun["findings"])


def test_profile_and_pinned_pack_survive_real_app_restart(tmp_path):
    url = f"sqlite:///{tmp_path / 'restart.db'}"
    with TestClient(create_app(database_url=url)) as first:
        demo = first.post("/api/v1/demo-sessions").json()
        owner = headers(demo)
        campaign = first.post(
            "/api/v1/campaigns",
            headers=owner,
            json={"name": "Restart QA", "publication_date": "2026-11-12"},
        ).json()
        set_profile(first, owner, campaign)
        run = review_copy(first, owner, campaign, "Guaranteed results.")
    with TestClient(create_app(database_url=url)) as second:
        base = f"/api/v1/campaigns/{campaign['id']}"
        assert (
            second.get(base + "/advertising-profile", headers=owner).json()["profile"][
                "jurisdiction"
            ]
            == "IN"
        )
        stored = second.get(base + f"/reviews/{run['id']}", headers=owner).json()
        assert stored["checks"] == run["checks"] and stored["findings"] == run["findings"]


def test_real_poster_claim_has_regulatory_evidence_and_ocr_coordinates(client, owner, campaign):
    from io import BytesIO

    from PIL import Image, ImageDraw

    set_profile(client, owner, campaign)
    image = Image.new("RGB", (1200, 220), "white")
    ImageDraw.Draw(image).text(
        (35, 60), "Guaranteed results in 30 days.", font=fixture_font(55), fill="black"
    )
    raw = BytesIO()
    image.save(raw, format="PNG")
    base = f"/api/v1/campaigns/{campaign['id']}"
    response = client.put(
        base + "/posters?expected_revision=1",
        headers={**owner, "Content-Type": "image/png"},
        content=raw.getvalue(),
    )
    assert response.status_code == 200
    current = client.get(base, headers=owner).json()
    run = client.post(
        base + "/reviews",
        headers=owner,
        json={
            "expected_content_revision": current["content_revision"],
            "expected_source_revision": current["source_revision"],
        },
    ).json()
    finding = next(f for f in run["findings"] if f["regulatory_evidence"])
    assert finding["location"]["asset"] == "poster" and finding["location"]["boxes"]

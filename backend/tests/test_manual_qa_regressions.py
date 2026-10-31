"""Regressions reproduced through the manual Round 2 acceptance audit."""

from datetime import UTC, datetime
from io import BytesIO

from conftest import headers
from PIL import Image, ImageDraw
from test_ocr import fixture_font, poster_bytes
from test_reviews import add_source, review_copy
from test_workflow import expectation


def mixed_poster():
    image = Image.new("RGB", (1100, 600), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1100, 95), fill="#102d44")
    for xy, text, size, colour in [
        ((42, 25), "BRANDPROOF / FICTIONAL DEMO", 30, "white"),
        ((42, 150), "Workshop", 56, "black"),
        ((42, 270), "INR 599", 76, "black"),
        ((42, 410), "Terms apply", 35, "black"),
        ((42, 535), "Synthetic test artwork - not a real event", 22, "black"),
    ]:
        draw.text(xy, text, font=fixture_font(size), fill=colour)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_mixed_size_poster_extracts_price_with_genuine_word_coordinates():
    from brandproof.ocr import extract_text

    result = extract_text(mixed_poster(), 1100, 600)
    assert "INR 599" in result["text"]
    assert "\n" in result["text"]
    price = [word for word in result["words"] if word["text"] in {"INR", "599"}]
    assert len(price) == 2
    assert all(260 < word["y"] < 370 for word in price)
    for word in result["words"]:
        assert result["text"][word["start"] : word["end"]] == word["text"]


def test_ocr_lines_support_main_price_without_losing_conditional_scope():
    from brandproof.ocr import parse_tsv
    from brandproof.rules import exact_checks

    raw = b"level\tpage_num\tblock_num\tpar_num\tline_num\tleft\ttop\twidth\theight\tconf\ttext\n"
    for line, words in enumerate(["Workshop", "Book for INR 599", "Terms apply"], 1):
        for position, word in enumerate(words.split()):
            raw += (
                f"5\t1\t1\t1\t{line}\t{position * 80}\t{line * 30}\t70\t20\t95\t{word}\n".encode()
            )
    result = parse_tsv(raw, 900, 250)
    assert result["text"] == "Workshop\nBook for INR 599\nTerms apply"
    price = {
        "id": "price",
        "version_id": "price-v2",
        "version": 2,
        "text": "INR 499",
        "rule": {"kind": "price", "amount": "499", "currency": "INR"},
    }
    disclosure = {
        **price,
        "id": "disclosure",
        "rule": {"kind": "required_text", "text": "Terms apply"},
    }
    findings, _ = exact_checks(result["text"], 1, [price, disclosure])
    assert len(findings) == 1 and findings[0]["evidence_status"] == "contradicted"
    start, end = findings[0]["location"]["start"], findings[0]["location"]["end"]
    assert result["text"][start:end] == "INR 599"
    conditional, _ = exact_checks("Only if eligible\n" + result["text"], 1, [price])
    assert all(item["evidence_status"] == "needs_clarification" for item in conditional)
    wrapped, _ = exact_checks("Terms\napply", 1, [disclosure])
    assert wrapped == []


def test_workflow_and_revision_timestamps_remain_utc_aware_after_sqlite_readback(
    client, demo, owner, campaign
):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    run = review_copy(client, owner, campaign, "Book for INR 599.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    comment = client.post(
        base + "/comments",
        headers=owner,
        json={
            **expectation(run),
            "review_id": run["id"],
            "text": "QA: read the approved fictional price.",
        },
    )
    assert comment.status_code == 201
    decision = client.post(
        f"{base}/reviews/{run['id']}/findings/{run['findings'][0]['id']}/decisions",
        headers=headers(demo, "reviewer"),
        json={
            **expectation(run),
            "expected_decision_version": 0,
            "decision": "dismiss",
            "reason": "Synthetic timestamp regression only.",
        },
    )
    assert decision.status_code == 201
    request = client.post(
        f"{base}/reviews/{run['id']}/requests", headers=owner, json=expectation(run)
    )
    assert request.status_code == 201
    approval = client.post(
        f"{base}/reviews/{run['id']}/approvals",
        headers=headers(demo, "reviewer"),
        json={
            **expectation(run),
            "request_id": request.json()["id"],
            "decision": "request_changes",
            "reason": "Please fix the fictional campaign price.",
        },
    )
    assert approval.status_code == 201, approval.text
    receipt = client.get(base + "/receipt", headers=owner).json()
    rows = client.get(base + "/revisions", headers=owner).json()
    records = [
        comment.json(),
        decision.json(),
        request.json(),
        approval.json(),
        *receipt["approvals"],
        *receipt["requests"],
        *rows,
        client.get(base, headers=owner).json(),
    ]
    for record in records:
        assert datetime.fromisoformat(record["created_at"]).utcoffset().total_seconds() == 0
    assert datetime.fromisoformat(comment.json()["created_at"]) >= datetime.fromisoformat(
        run["created_at"]
    )
    assert (
        client.get(base + "/comments", headers=owner).json()[0]["created_at"]
        == comment.json()["created_at"]
    )


def test_clear_caption_keeps_poster_history_and_stales_approval(client, demo, owner, campaign):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    review_copy(client, owner, campaign, "Book for INR 499.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    poster = client.put(
        base + "/posters?expected_revision=2",
        headers={**owner, "Content-Type": "image/png"},
        content=poster_bytes("Book for INR 499."),
    ).json()
    run = client.post(
        base + "/reviews",
        headers=owner,
        json={"expected_content_revision": 3, "expected_source_revision": 2},
    ).json()
    request = client.post(
        f"{base}/reviews/{run['id']}/requests", headers=owner, json=expectation(run)
    ).json()
    approval = client.post(
        f"{base}/reviews/{run['id']}/approvals",
        headers=headers(demo, "reviewer"),
        json={
            **expectation(run),
            "request_id": request["id"],
            "decision": "approve",
            "reason": "Synthetic QA of the displayed caption and poster.",
            "manual_checks": {
                "advertising_risk": "Synthetic test reviewer manually assessed the unconfigured advertising scope.",
                "contextual": "Read the fictional campaign against the approved source.",
                "poster": "Read the simple fictional image and compared its price.",
            },
        },
    )
    assert approval.status_code == 201, approval.text
    cleared = client.post(base + "/caption/clear", headers=owner, json={"expected_revision": 3})
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["caption"] == "" and cleared.json()["content_revision"] == 4
    assert client.get(base + "/receipt", headers=owner).json()["readiness"] == "stale"
    assert client.get(base + f"/posters/{poster['id']}/content", headers=owner).status_code == 200
    revisions = client.get(base + "/revisions", headers=owner).json()
    assert revisions[-1]["caption"] == "" and any(
        row["caption"] == "Book for INR 499." for row in revisions
    )
    assert (
        client.post(
            base + "/caption/clear", headers=owner, json={"expected_revision": 3}
        ).status_code
        == 409
    )
    assert (
        client.post(
            base + "/caption/clear",
            headers=headers(demo, "reviewer"),
            json={"expected_revision": 4},
        ).status_code
        == 403
    )
    other = client.post("/api/v1/demo-sessions").json()
    assert (
        client.post(
            base + "/caption/clear", headers=headers(other), json={"expected_revision": 4}
        ).status_code
        == 404
    )
    rerun = client.post(
        base + "/reviews",
        headers=owner,
        json={"expected_content_revision": 4, "expected_source_revision": 2},
    )
    assert (
        rerun.status_code == 201
        and rerun.json()["checks"]["poster"]["details"]["asset_id"] == poster["id"]
    )


def test_clear_caption_without_poster_cannot_create_an_empty_campaign(client, owner, campaign):
    base = f"/api/v1/campaigns/{campaign['id']}"
    review_copy(client, owner, campaign, "Keep this caption.")
    assert (
        client.post(
            base + "/caption/clear", headers=owner, json={"expected_revision": 2}
        ).status_code
        == 422
    )
    saved = client.get(base, headers=owner).json()
    assert saved["caption"] == "Keep this caption." and saved["content_revision"] == 2


def test_utc_normalisation_preserves_aware_instants():
    from brandproof.timestamps import as_utc

    source = datetime.fromisoformat("2026-10-28T16:00:00+05:30")
    assert as_utc(source) == datetime(2026, 10, 28, 10, 30, tzinfo=UTC)


def test_real_multiline_poster_review_produces_a_supported_price_contradiction(
    client, owner, campaign
):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    image = Image.new("RGB", (1100, 600), "white")
    draw = ImageDraw.Draw(image)
    for y, line in [
        (60, "Fictional workshop"),
        (150, "Book for INR 599"),
        (240, "Terms apply"),
        (330, "Synthetic demonstration artwork"),
    ]:
        draw.text((42, y), line, font=fixture_font(38), fill="black")
    output = BytesIO()
    image.save(output, format="PNG")
    base = f"/api/v1/campaigns/{campaign['id']}"
    uploaded = client.put(
        base + "/posters?expected_revision=1",
        headers={**owner, "Content-Type": "image/png"},
        content=output.getvalue(),
    )
    assert uploaded.status_code == 200, uploaded.text
    run = client.post(
        base + "/reviews",
        headers=owner,
        json={"expected_content_revision": 2, "expected_source_revision": 2},
    )
    assert run.status_code == 201, run.text
    price = [finding for finding in run.json()["findings"] if finding["category"] == "price"]
    assert len(price) == 1 and price[0]["evidence_status"] == "contradicted"
    assert price[0]["location"]["quote"] == "INR 599"
    assert len(price[0]["location"]["boxes"]) == 2

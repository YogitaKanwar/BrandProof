from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from brandproof.visual_checks import (
    background_colour,
    contrast_ratio,
    delta_e,
    evaluate_visuals,
    word_colours,
)
from conftest import headers
from PIL import Image, ImageDraw, ImageFont
from test_ocr import fixture_font
from test_reviews import add_source


def poster(background="white", ink="black", confidence=0.99, *, font=None):
    image = Image.new("RGB", (500, 170), background)
    font = font or fixture_font(72)
    draw = ImageDraw.Draw(image)
    bounds = draw.textbbox((40, 35), "TEST", font=font)
    draw.text((40, 35), "TEST", font=font, fill=ink)
    raw = BytesIO()
    image.save(raw, format="PNG")
    word = {
        "text": "TEST",
        "start": 0,
        "end": 4,
        "x": bounds[0],
        "y": bounds[1],
        "width": bounds[2] - bounds[0],
        "height": bounds[3] - bounds[1],
        "confidence": confidence,
    }
    return (
        image,
        SimpleNamespace(
            id="poster",
            normalized_bytes=raw.getvalue(),
            ocr={"text": "TEST", "status": "completed", "words": [word]},
        ),
        word,
    )


@pytest.mark.parametrize(
    "background,ink,minimum",
    [("white", "black", 20.9), ("black", "white", 20.9), ("white", "#999999", 2.8)],
)
def test_real_rendered_text_contrast_samples(background, ink, minimum):
    image, _, word = poster(background, ink)
    colors = word_colours(image, word)
    assert colors is not None
    ratio = contrast_ratio(*colors)
    assert ratio > minimum
    if ink == "#999999":
        assert ratio < 4.5


def test_gradient_noisy_and_low_confidence_images_abstain():
    image, _, word = poster(confidence=0.4)
    assert word_colours(image, word) is None
    gradient = Image.new("RGB", (200, 120))
    gradient.putdata([(x % 256, y % 256, (x * y) % 256) for y in range(120) for x in range(200)])
    assert background_colour(gradient) is None
    word.update(confidence=0.99, x=10, y=10, width=50, height=50)
    assert word_colours(gradient, word) is None


@pytest.mark.parametrize("size", [24, 48, 72])
@pytest.mark.parametrize("family", ["NotoSans", "NotoSerif", "NotoSansMono"])
@pytest.mark.parametrize("background,ink", [("white", "black"), ("#1E2640", "#DC9750")])
def test_antialiasing_across_available_fonts_and_sizes(size, family, background, ink):
    path = Path(f"/usr/share/fonts/noto/{family}-Regular.ttf")
    if not path.exists():
        pytest.skip("Optional Noto family unavailable; default fixture tests remain required")
    image, _, word = poster(background, ink, font=ImageFont.truetype(str(path), size))
    colors = word_colours(image, word)
    if size == 24:
        # These thin glyphs have <50% solid ink. Keep the conservative core
        # requirement: small, mostly antialiased text is explicitly unsupported.
        assert colors is None
        return
    assert colors == (
        Image.new("RGB", (1, 1), ink).getpixel((0, 0)),
        Image.new("RGB", (1, 1), background).getpixel((0, 0)),
    )


@pytest.mark.parametrize("secondary", ["red", "#888888"])
def test_secondary_interior_ink_is_not_antialiasing(secondary):
    image, _, word = poster()
    # The black core remains dominant: a mode-only relaxation would accept this.
    ImageDraw.Draw(image).rectangle((45, 65, 60, 80), fill=secondary)
    assert word_colours(image, word) is None


def test_collinear_interior_gradient_and_single_coloured_noise_abstain():
    image, _, word = poster()
    for x in range(45, 65):
        shade = 60 + (x - 45) * 5
        ImageDraw.Draw(image).line((x, 65, x, 85), fill=(shade, shade, shade))
    assert word_colours(image, word) is None
    image, _, word = poster()
    image.putpixel((word["x"] + 5, word["y"] + 5), (255, 0, 0))
    assert word_colours(image, word) is None


def contrast_source(minimum=4.5):
    return {
        "id": "contrast",
        "version_id": "v1",
        "version": 1,
        "text": "Minimum contrast",
        "rule": {"kind": "contrast", "minimum_ratio": minimum},
    }


@pytest.mark.parametrize("minimum,flagged", [(21, False), (21.01, True)])
def test_measured_threshold_is_exact_and_exposed(minimum, flagged):
    _, asset, _ = poster()
    findings, checks = evaluate_visuals(
        asset, SimpleNamespace(content_revision=1), [contrast_source(minimum)], ""
    )
    assert checks["contrast"]["status"] == "completed"
    assert checks["contrast"]["measurements"][0]["minimum_ratio"] == minimum
    assert bool(findings) is flagged


def test_ocr_partial_and_word_limit_keep_contrast_partial():
    _, asset, _ = poster()
    asset.ocr["status"] = "partial"
    _, checks = evaluate_visuals(
        asset, SimpleNamespace(content_revision=1), [contrast_source()], ""
    )
    assert checks["contrast"]["status"] == "partial"
    asset.ocr["status"] = "completed"
    asset.ocr["words"] *= 101
    _, checks = evaluate_visuals(
        asset, SimpleNamespace(content_revision=1), [contrast_source()], ""
    )
    assert checks["contrast"]["status"] == "partial"
    assert len(checks["contrast"]["measurements"]) == 100


@pytest.mark.parametrize("ink,flagged", [("black", False), ("#999999", True)])
def test_real_ocr_upload_measures_and_preserves_finding_evidence(
    client, owner, campaign, ink, flagged
):
    source = add_source(client, owner, campaign, {"kind": "contrast", "minimum_ratio": 4.5})
    _, asset, _ = poster(ink=ink)
    base = f"/api/v1/campaigns/{campaign['id']}"
    upload = client.put(
        base + "/posters?expected_revision=1",
        headers={**owner, "Content-Type": "image/png"},
        content=asset.normalized_bytes,
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
    check = run["checks"]["poster"]["details"]["measured_checks"]["contrast"]
    assert check["status"] == "completed"
    assert check["measurements"][0]["text"] == "TEST"
    assert check["measurements"][0]["ratio"] == pytest.approx(
        contrast_ratio((0, 0, 0) if ink == "black" else (153, 153, 153), (255, 255, 255)), abs=0.001
    )
    findings = [f for f in run["findings"] if f["category"] == "contrast"]
    assert bool(findings) is flagged
    if flagged:
        assert findings[0]["evidence"]["source_version_id"] == source["version_id"]
        assert findings[0]["location"]["quote"] == "TEST"
        assert findings[0]["location"]["boxes"]
    assert run["readiness"] == "not_approved"
    saved = client.get(base + "/reviews/" + run["id"], headers=owner).json()
    assert saved["findings"] == run["findings"]


def test_palette_delta_e_and_flags_are_scoped_to_real_measured_background():
    assert delta_e((255, 255, 255), (255, 255, 255)) == 0
    assert contrast_ratio((0, 0, 0), (255, 255, 255)) == 21
    _, asset, _ = poster("#FF0000")
    source = {
        "id": "palette",
        "version_id": "v2",
        "version": 2,
        "text": "Approved teal background",
        "rule": {"kind": "brand_color", "hex": "#008080", "tolerance": 5},
    }
    findings, checks = evaluate_visuals(asset, SimpleNamespace(content_revision=2), [source], "")
    assert checks["visual"]["observed_hex"] == "#FF0000"
    assert findings[0]["category"] == "brand_color" and findings[0]["location"]["boxes"] == []
    assert findings[0]["evidence_status"] == "needs_clarification"


def test_alt_text_revision_conflicts_permissions_and_poster_specificity(
    client, demo, owner, campaign
):
    add_source(client, owner, campaign, {"kind": "alt_text"})
    _, asset, _ = poster()
    base = f"/api/v1/campaigns/{campaign['id']}"
    upload = client.put(
        base + "/posters?expected_revision=1",
        headers={**owner, "Content-Type": "image/png"},
        content=asset.normalized_bytes,
    )
    assert upload.status_code == 200
    c = client.get(base, headers=owner).json()
    review = client.post(
        base + "/reviews",
        headers=owner,
        json={"expected_content_revision": 2, "expected_source_revision": c["source_revision"]},
    ).json()
    assert any(f["category"] == "alt_text" for f in review["findings"])
    payload = {"expected_revision": 2, "text": "A poster reading TEST."}
    assert (
        client.put(base + "/alt-text", headers=headers(demo, "reviewer"), json=payload).status_code
        == 403
    )
    assert (
        client.put(base + "/alt-text", headers=headers(demo, "creator"), json=payload).status_code
        == 200
    )
    assert client.put(base + "/alt-text", headers=owner, json=payload).status_code == 409
    assert client.get(base + "/alt-text", headers=owner).json()["text"] == payload["text"]
    assert (
        client.get(base + "/reviews/" + review["id"], headers=owner).json()["is_current"] is False
    )
    assert (
        client.put(
            base + "/posters?expected_revision=3",
            headers={**owner, "Content-Type": "image/png"},
            content=asset.normalized_bytes,
        ).status_code
        == 200
    )
    assert client.get(base + "/alt-text", headers=owner).json()["text"] == ""


def test_alt_text_edits_stale_receipts_and_empty_text_remains_missing(
    client, demo, owner, campaign
):
    from test_workflow import expectation

    add_source(client, owner, campaign, {"kind": "alt_text"})
    _, asset, _ = poster()
    base = f"/api/v1/campaigns/{campaign['id']}"
    assert (
        client.put(
            base + "/posters?expected_revision=1",
            headers={**owner, "Content-Type": "image/png"},
            content=asset.normalized_bytes,
        ).status_code
        == 200
    )
    assert (
        client.put(
            base + "/alt-text",
            headers=owner,
            json={"expected_revision": 2, "text": "A poster reading TEST."},
        ).status_code
        == 200
    )
    current = client.get(base, headers=owner).json()
    run = client.post(
        base + "/reviews",
        headers=owner,
        json={
            "expected_content_revision": current["content_revision"],
            "expected_source_revision": current["source_revision"],
        },
    ).json()
    assert (
        run["checks"]["poster"]["details"]["measured_checks"]["accessibility"]["status"]
        == "completed"
    )
    request = client.post(
        base + f"/reviews/{run['id']}/requests",
        headers=headers(demo, "creator"),
        json=expectation(run),
    ).json()
    notes = {
        name: "Synthetic QA attestation of the exact incomplete scope, not independent user feedback."
        for name in ["exact_text", "contextual", "claim_risk", "advertising_risk", "poster"]
        if run["checks"][name]["status"] != "completed"
    }
    approval = client.post(
        base + f"/reviews/{run['id']}/approvals",
        headers=headers(demo, "reviewer"),
        json={
            **expectation(run),
            "request_id": request["id"],
            "decision": "approve",
            "reason": "Synthetic QA of description staleness; not publication authorisation.",
            "manual_checks": notes,
        },
    )
    assert approval.status_code == 201, approval.text
    assert (
        client.put(
            base + "/alt-text",
            headers=owner,
            json={"expected_revision": current["content_revision"], "text": "   "},
        ).status_code
        == 200
    )
    assert client.get(base + "/receipt", headers=owner).json()["readiness"] == "stale"
    current = client.get(base, headers=owner).json()
    new = client.post(
        base + "/reviews",
        headers=owner,
        json={
            "expected_content_revision": current["content_revision"],
            "expected_source_revision": current["source_revision"],
        },
    ).json()
    assert any(f["category"] == "alt_text" for f in new["findings"])
    historic = client.get(base + f"/reviews/{run['id']}", headers=owner).json()
    assert (
        historic["checks"]["poster"]["details"]["alt_text_snapshot"]["text"]
        == "A poster reading TEST."
    )

from io import BytesIO
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
from PIL import Image, ImageDraw
from test_ocr import fixture_font
from test_reviews import add_source


def poster(background="white", ink="black", confidence=0.99):
    image = Image.new("RGB", (500, 170), background)
    font = fixture_font(72)
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

from io import BytesIO

import pytest
from brandproof.logos import compare_logo
from PIL import Image, ImageDraw


def png(image):
    out = BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def logo_image():
    image = Image.new("RGB", (80, 40), "navy")
    ImageDraw.Draw(image).polygon([(0, 0), (40, 40), (80, 0)], fill="teal")
    return image


def test_real_comparison_distinguishes_reference_missing_and_changed():
    logo = logo_image()
    poster = Image.new("RGB", (800, 400), "white")
    poster.paste(logo, (40, 40))
    same = compare_logo(png(logo), png(poster), max_seconds=8)
    assert same["similar_candidate"] is True
    assert same["status"] == "partial"  # similarity is not approval
    altered = logo_image()
    ImageDraw.Draw(altered).rectangle((15, 5, 55, 35), fill="red")
    poster.paste(altered, (40, 40))
    assert compare_logo(png(logo), png(poster), max_seconds=8)["similar_candidate"] is False
    missing = compare_logo(png(logo), png(Image.new("RGB", (800, 400), "white")), max_seconds=8)
    assert missing["similar_candidate"] is False
    assert "Possible logo mismatch" in missing["reason"]


def test_blank_and_timeout_are_not_assessed():
    blank = png(Image.new("RGB", (100, 50), "white"))
    assert compare_logo(blank, blank)["status"] == "not_assessed"
    assert compare_logo(png(logo_image()), blank, max_seconds=0)["status"] == "not_assessed"


def test_owner_reference_confirmation_history_and_review(client, owner, demo, campaign):
    base = f"/api/v1/campaigns/{campaign['id']}"
    creator = {"Authorization": "Bearer " + demo["actors"]["creator"]["access_token"]}
    raw = png(logo_image())
    assert (
        client.put(
            base + "/brand-logo?expected_source_revision=0",
            headers={**creator, "Content-Type": "image/png"},
            content=raw,
        ).status_code
        == 403
    )
    assert (
        client.put(
            base + "/brand-logo?expected_source_revision=0",
            headers={**owner, "Content-Type": "image/png"},
            content=b"bad",
        ).status_code
        == 422
    )
    upload = client.put(
        base + "/brand-logo?expected_source_revision=0",
        headers={**owner, "Content-Type": "image/png"},
        content=raw,
    )
    assert upload.status_code == 200
    pending = upload.json()
    assert pending["status"] == "pending"
    confirmation = {"expected_version": 1, "expected_source_revision": 1}
    assert (
        client.post(
            base + "/brand-logo/" + pending["id"] + "/confirm", headers=creator, json=confirmation
        ).status_code
        == 403
    )
    approved = client.post(
        base + "/brand-logo/" + pending["id"] + "/confirm", headers=owner, json=confirmation
    ).json()
    assert (
        approved["status"] == "approved" and approved["version"] == 2 and approved["confirmed_by"]
    )
    assert (
        client.post(
            base + "/brand-logo/" + pending["id"] + "/confirm", headers=owner, json=confirmation
        ).status_code
        == 409
    )
    history = client.get(base + "/brand-logo/history", headers=owner).json()
    assert len(history) == 2 and history[0]["status"] == "pending"
    assert client.get(base + "/brand-logo/" + approved["id"] + "/content").status_code == 401
    other = client.post("/api/v1/demo-sessions").json()
    other_h = {"Authorization": "Bearer " + other["actors"]["owner"]["access_token"]}
    assert client.get(base + "/brand-logo", headers=other_h).status_code == 404
    poster = png(Image.new("RGB", (400, 200), "white"))
    assert (
        client.put(
            base + "/posters?expected_revision=1",
            headers={**creator, "Content-Type": "image/png"},
            content=poster,
        ).status_code
        == 200
    )
    run = client.post(
        base + "/reviews",
        headers=creator,
        json={
            "expected_content_revision": 2,
            "expected_source_revision": 2,
            "external_ai_consent": False,
        },
    ).json()
    finding = next(f for f in run["findings"] if f["category"] == "logo")
    assert finding["evidence_status"] == "needs_clarification"
    assert finding["evidence"]["source_version_id"] == approved["id"]
    assert finding["location"]["boxes"] == []  # no invented detected location
    assert run["checks"]["poster"]["details"]["logo"]["status"] == "partial"
    assert (
        client.get(base + "/reviews/" + run["id"], headers=owner).json()["findings"]
        == run["findings"]
    )
    replace = client.put(
        base + "/brand-logo?expected_source_revision=2",
        headers={**owner, "Content-Type": "image/png"},
        content=raw,
    )
    assert replace.status_code == 200 and replace.json()["status"] == "pending"
    assert client.get(base + "/reviews/" + run["id"], headers=owner).json()["is_current"] is False
    assert (
        client.get(base + "/brand-logo/" + approved["id"] + "/content", headers=owner).content
        == raw
    )


@pytest.mark.parametrize("mime,expected", [("text/plain", 415), ("image/png", 413)])
def test_upload_limits(client, owner, campaign, mime, expected):
    data = b"x" * (5 * 1024 * 1024 + 1) if expected == 413 else b"x"
    assert (
        client.put(
            f"/api/v1/campaigns/{campaign['id']}/brand-logo?expected_source_revision=0",
            headers={**owner, "Content-Type": mime},
            content=data,
        ).status_code
        == expected
    )


def test_reference_snapshots_cannot_be_mutated(client, owner, campaign):
    from brandproof.logos import BrandLogo

    base = f"/api/v1/campaigns/{campaign['id']}"
    row = client.put(
        base + "/brand-logo?expected_source_revision=0",
        headers={**owner, "Content-Type": "image/png"},
        content=png(logo_image()),
    ).json()
    with client.app.state.sessions() as session:
        logo = session.get(BrandLogo, row["id"])
        logo.status = "approved"
        with pytest.raises(ValueError, match="immutable"):
            session.commit()
        session.rollback()
    assert client.get(base + "/brand-logo", headers=owner).json()["status"] == "pending"


def test_full_poster_reference_cannot_hide_changed_small_logo():
    reference = Image.new("RGB", (800, 400), "white")
    reference.paste(logo_image(), (40, 40))
    ImageDraw.Draw(reference).rectangle((40, 180, 400, 220), fill="black")
    altered = reference.copy()
    ImageDraw.Draw(altered).rectangle((55, 45, 95, 75), fill="red")
    result = compare_logo(png(reference), png(altered), max_seconds=8)
    assert result["status"] == "not_assessed"
    assert "reference needs cropping" in result["reason"]
    assert not result.get("similar_candidate")

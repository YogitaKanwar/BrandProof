import hashlib
from importlib.util import find_spec
from io import BytesIO

import pytest
from brandproof.main import create_app
from fastapi.testclient import TestClient
from PIL import Image
from test_ocr import poster_bytes


@pytest.fixture
def client(tmp_path):
    assert find_spec("brandproof.posters") is not None, "Poster router is missing"
    app = create_app(database_url=f"sqlite:///{tmp_path / 'posters.db'}")
    with TestClient(app) as value:
        yield value


def upload(client, campaign, owner, data=None, revision=1, mime="image/png"):
    return client.put(
        f"/api/v1/campaigns/{campaign['id']}/posters",
        params={"expected_revision": revision},
        headers={**owner, "Content-Type": mime},
        content=poster_bytes() if data is None else data,
    )


def test_real_upload_ocr_and_authenticated_canonical_content(client, campaign, owner):
    response = upload(client, campaign, owner)
    assert response.status_code == 200, response.text
    asset = response.json()
    assert asset["campaign_id"] == campaign["id"]
    assert asset["content_revision"] == 2
    assert asset["mime"] == "image/png"
    assert (asset["width"], asset["height"]) == (1000, 240)
    assert asset["ocr"]["status"] == "completed"
    assert "SUMMER SALE 2026" in asset["ocr"]["text"]
    assert "normalized_bytes" not in asset
    path = f"/api/v1/campaigns/{campaign['id']}/posters/{asset['id']}/content"
    content = client.get(path, headers=owner)
    assert content.status_code == 200
    assert content.headers["content-type"] == "image/png"
    assert hashlib.sha256(content.content).hexdigest() == asset["sha256"]
    assert Image.open(BytesIO(content.content)).size == (1000, 240)
    assert client.get(path).status_code == 401


@pytest.mark.parametrize(
    "data,mime,status",
    [
        (b"not an image", "image/png", 422),
        (poster_bytes()[:80], "image/png", 422),
        (poster_bytes(), "image/jpeg", 422),
        (poster_bytes(fmt="GIF"), "image/png", 422),
        (poster_bytes(), "text/plain", 415),
        (b"x" * (5 * 1024 * 1024 + 1), "image/png", 413),
        (poster_bytes("", size=(4001, 4000)), "image/png", 422),
    ],
    ids=[
        "corrupt",
        "truncated",
        "mime-mismatch",
        "wrong-format",
        "mime",
        "byte-limit",
        "pixel-limit",
    ],
)
def test_invalid_uploads_are_bounded_and_do_not_mutate(client, campaign, owner, data, mime, status):
    result = upload(client, campaign, owner, data, mime=mime)
    assert result.status_code == status, result.text
    if status == 422:
        assert result.json()["error"]["message"] == "Invalid or unsupported poster image"
    current = client.get(f"/api/v1/campaigns/{campaign['id']}", headers=owner).json()
    assert current["content_revision"] == 1


def test_upload_preserves_initial_and_shared_caption_history(client, campaign, owner):
    from brandproof.review_models import ContentVersion
    from sqlalchemy import select

    base = f"/api/v1/campaigns/{campaign['id']}"
    first_response = upload(client, campaign, owner)
    assert first_response.status_code == 200
    first = first_response.json()
    caption = client.put(
        base + "/caption",
        headers=owner,
        json={"text": "Original caption survives posters", "expected_revision": 2},
    )
    assert caption.status_code == 200, caption.text
    second_response = upload(client, campaign, owner, poster_bytes("WINTER SALE 2027"), revision=3)
    assert second_response.status_code == 200, second_response.text
    second = second_response.json()
    assert second["content_revision"] == 4
    with client.app.state.sessions() as session:
        rows = session.scalars(
            select(ContentVersion)
            .where(ContentVersion.campaign_id == campaign["id"])
            .order_by(ContentVersion.revision)
        ).all()
        assert [(row.revision, row.caption) for row in rows] == [
            (1, ""),
            (2, ""),
            (3, "Original caption survives posters"),
            (4, "Original caption survives posters"),
        ]
    first_bytes = client.get(base + f"/posters/{first['id']}/content", headers=owner).content
    assert hashlib.sha256(first_bytes).hexdigest() == first["sha256"]


def test_stale_revision_conflicts_without_creating_asset(client, campaign, owner):
    from brandproof.poster_models import PosterAsset
    from sqlalchemy import select

    assert upload(client, campaign, owner).status_code == 200
    result = upload(client, campaign, owner)
    assert result.status_code == 409, result.text
    with client.app.state.sessions() as session:
        assert len(session.scalars(select(PosterAsset)).all()) == 1


def test_latest_metadata_uses_poster_revision_not_caption_revision(client, campaign, owner):
    base = f"/api/v1/campaigns/{campaign['id']}"
    assert client.get(base + "/posters", headers=owner).status_code == 404
    first = upload(client, campaign, owner).json()
    latest = upload(client, campaign, owner, poster_bytes("WINTER SALE 2027"), revision=2).json()
    caption = client.put(
        base + "/caption", headers=owner, json={"text": "Later caption", "expected_revision": 3}
    )
    assert caption.status_code == 200
    assert client.get(base + "/posters", headers=owner).json() == latest
    historical = client.get(base + f"/posters/{first['id']}", headers=owner)
    assert historical.status_code == 200
    assert historical.json() == first
    assert client.get(base + "/posters/no-such-poster", headers=owner).status_code == 404


@pytest.mark.parametrize("kind", ["oriented-jpeg", "transparent-png"])
def test_normalization_matches_display_and_ocr_coordinates(client, campaign, owner, kind):
    image = Image.open(BytesIO(poster_bytes())).convert("RGBA")
    output = BytesIO()
    if kind == "oriented-jpeg":
        image = image.convert("RGB").transpose(Image.Transpose.ROTATE_90)
        exif = Image.Exif()
        exif[274] = 6
        image.save(output, format="JPEG", exif=exif)
        mime = "image/jpeg"
    else:
        pixels = image.load()
        for y in range(image.height):
            for x in range(image.width):
                if pixels[x, y] == (255, 255, 255, 255):
                    pixels[x, y] = (255, 0, 0, 0)
        image.save(output, format="PNG")
        mime = "image/png"
    response = upload(client, campaign, owner, output.getvalue(), mime=mime)
    assert response.status_code == 200, response.text
    asset = response.json()
    assert (asset["width"], asset["height"]) == (1000, 240)
    assert "SUMMER SALE 2026" in asset["ocr"]["text"]
    content = client.get(
        f"/api/v1/campaigns/{campaign['id']}/posters/{asset['id']}/content", headers=owner
    )
    canonical = Image.open(BytesIO(content.content))
    assert canonical.mode == "RGB"
    assert canonical.getpixel((0, 0)) == (255, 255, 255)
    assert not canonical.getexif()
    for word in asset["ocr"]["words"]:
        assert 0 <= word["x"] < asset["width"]
        assert 0 <= word["y"] < asset["height"]
        crop = canonical.crop(
            (word["x"], word["y"], word["x"] + word["width"], word["y"] + word["height"])
        )
        assert crop.convert("L").getextrema()[0] < 100


@pytest.mark.parametrize("operation", ["update", "delete"])
def test_poster_assets_reject_orm_mutation(client, campaign, owner, operation):
    from brandproof.poster_models import PosterAsset

    asset = upload(client, campaign, owner).json()
    with client.app.state.sessions() as session:
        stored = session.get(PosterAsset, asset["id"])
        if operation == "update":
            stored.mime = "image/jpeg"
        else:
            session.delete(stored)
        with pytest.raises(ValueError, match="immutable"):
            session.commit()
        session.rollback()


def test_roles_and_workspace_campaign_isolation(client, campaign, owner, demo):
    from conftest import headers

    reviewer = headers(demo, "reviewer")
    creator = headers(demo, "creator")
    assert upload(client, campaign, reviewer).status_code == 403
    created = upload(client, campaign, creator)
    assert created.status_code == 200, created.text
    asset = created.json()
    base = f"/api/v1/campaigns/{campaign['id']}/posters"
    for suffix in ("", f"/{asset['id']}", f"/{asset['id']}/content"):
        assert client.get(base + suffix, headers=reviewer).status_code == 200
        assert client.get(base + suffix).status_code == 401
    other = client.post("/api/v1/demo-sessions").json()
    other_owner = headers(other)
    for suffix in ("", f"/{asset['id']}", f"/{asset['id']}/content"):
        assert client.get(base + suffix, headers=other_owner).status_code == 404
    assert upload(client, campaign, other_owner).status_code == 404
    second = client.post(
        "/api/v1/campaigns", headers=owner, json={"name": "Other", "publication_date": "2026-11-12"}
    ).json()
    for suffix in (f"/{asset['id']}", f"/{asset['id']}/content"):
        wrong_path = f"/api/v1/campaigns/{second['id']}/posters" + suffix
        assert client.get(wrong_path, headers=owner).status_code == 404


@pytest.mark.parametrize("revision", [0, -1, 2**31 - 1, 2**63, "not-a-revision"])
def test_revision_expectation_is_bounded(client, campaign, owner, revision):
    assert upload(client, campaign, owner, revision=revision).status_code == 422


def test_unreadable_and_timeout_are_persisted_visible(client, campaign, owner, monkeypatch):
    from brandproof import ocr

    unreadable = upload(client, campaign, owner, poster_bytes(""))
    assert unreadable.status_code == 200
    assert unreadable.json()["ocr"]["status"] == "partial"
    assert unreadable.json()["ocr"]["reason"] == "unreadable"
    monkeypatch.setattr(ocr, "OCR_TIMEOUT_SECONDS", 0)
    timed_out = upload(client, campaign, owner, revision=2)
    assert timed_out.status_code == 200
    asset = timed_out.json()
    assert asset["ocr"]["status"] == "unavailable"
    assert asset["ocr"]["reason"] == "timeout"
    persisted = client.get(
        f"/api/v1/campaigns/{campaign['id']}/posters/{asset['id']}", headers=owner
    )
    assert persisted.json() == asset


def test_concurrent_real_uploads_recheck_revision_after_ocr(client, campaign, owner):
    from concurrent.futures import ThreadPoolExecutor

    from brandproof.models import Campaign
    from brandproof.poster_models import PosterAsset
    from brandproof.review_models import ContentVersion
    from sqlalchemy import select

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(upload, client, campaign, owner) for _ in range(2)]
        results = [future.result() for future in futures]
    assert sorted(result.status_code for result in results) == [200, 409]
    with client.app.state.sessions() as session:
        assert session.get(Campaign, campaign["id"]).content_revision == 2
        assert len(session.scalars(select(PosterAsset)).all()) == 1
        assert sorted(session.scalars(select(ContentVersion.revision)).all()) == [1, 2]


@pytest.mark.parametrize("dimension", [10000, 20000])
def test_decompression_bomb_headers_are_generic_422(client, campaign, owner, dimension):
    import struct
    import zlib

    data = bytearray(poster_bytes("", size=(1, 1)))
    data[16:24] = struct.pack(">II", dimension, dimension)
    data[29:33] = struct.pack(">I", zlib.crc32(data[12:29]))
    result = upload(client, campaign, owner, bytes(data))
    assert result.status_code == 422
    assert result.json()["error"]["message"] == "Invalid or unsupported poster image"


def test_stream_byte_limit_does_not_trust_content_length(client, campaign, owner):
    result = client.put(
        f"/api/v1/campaigns/{campaign['id']}/posters?expected_revision=1",
        headers={**owner, "Content-Type": "image/png", "Content-Length": "1"},
        content=(b"x" * 65536 for _ in range(81)),
    )
    assert result.status_code == 413


def test_exact_byte_limit_is_accepted(client, campaign, owner):
    png = poster_bytes()
    padded = png + b"\0" * (5 * 1024 * 1024 - len(png))
    result = upload(client, campaign, owner, padded)
    assert result.status_code == 200, result.text
    assert result.json()["ocr"]["status"] == "completed"

"""Private raw-image upload and historical canonical-poster retrieval."""

import hashlib
import warnings
from io import BytesIO

from fastapi import APIRouter, Depends, Query, Request, Response
from PIL import Image, ImageOps
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from brandproof.auth import actor, db, lock_campaign, require_role, scoped_campaign
from brandproof.errors import fail
from brandproof.models import Actor
from brandproof.ocr import extract_text
from brandproof.poster_models import PosterAsset
from brandproof.poster_schemas import PosterOut
from brandproof.review_models import ContentVersion
from brandproof.schemas import MAX_INCREMENT_EXPECTATION
from brandproof.workflow_models import RevisionAuthor

router = APIRouter(prefix="/api/v1/campaigns/{campaign_id}", tags=["posters"])


MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000


def _prepare(data: bytes, mime: str):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data), formats=["PNG", "JPEG"]) as image:
                if image.format != {"image/png": "PNG", "image/jpeg": "JPEG"}.get(mime):
                    raise ValueError("Format mismatch")
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise ValueError("Pixel limit")
                image.verify()
            with Image.open(BytesIO(data), formats=["PNG", "JPEG"]) as image:
                image.load()
                oriented = ImageOps.exif_transpose(image).convert("RGBA")
                normalized = Image.new("RGB", oriented.size, "white")
                normalized.paste(oriented, mask=oriented.getchannel("A"))
                output = BytesIO()
                normalized.save(output, format="PNG")
                png = output.getvalue()
                width, height = normalized.size
    except (
        OSError,
        ValueError,
        SyntaxError,
        EOFError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        fail(422, "invalid_poster", "Invalid or unsupported poster image")
    return png, width, height, extract_text(png, width, height)


def _authorize(session, campaign_id, who):
    scoped_campaign(session, campaign_id, who)
    require_role(who, "owner", "creator")
    # Do not keep a read transaction/snapshot open during expensive local OCR.
    session.rollback()


def _save(session, campaign_id, who, expected_revision, prepared):
    campaign = scoped_campaign(session, campaign_id, who)
    lock_campaign(session, campaign)
    if campaign.content_revision != expected_revision:
        fail(409, "version_conflict", "Content changed; reload before saving the poster")
    if not session.scalar(
        select(ContentVersion.id).where(
            ContentVersion.campaign_id == campaign_id,
            ContentVersion.revision == expected_revision,
        )
    ):
        session.add(
            ContentVersion(
                campaign_id=campaign_id, revision=expected_revision, caption=campaign.caption
            )
        )
    png, width, height, extraction = prepared
    campaign.content_revision = expected_revision + 1
    session.add(
        ContentVersion(
            campaign_id=campaign_id, revision=campaign.content_revision, caption=campaign.caption
        )
    )
    asset = PosterAsset(
        campaign_id=campaign_id,
        content_revision=campaign.content_revision,
        normalized_bytes=png,
        mime="image/png",
        sha256=hashlib.sha256(png).hexdigest(),
        width=width,
        height=height,
        ocr=extraction,
    )
    session.add(asset)
    session.add(
        RevisionAuthor(
            campaign_id=campaign_id, content_revision=campaign.content_revision, actor_id=who.id
        )
    )
    session.commit()
    return PosterOut.model_validate(asset)


@router.put("/posters", response_model=PosterOut)
async def upload_poster(
    campaign_id: str,
    request: Request,
    expected_revision: int = Query(ge=1, le=MAX_INCREMENT_EXPECTATION),
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    await run_in_threadpool(_authorize, session, campaign_id, who)
    mime = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if mime not in {"image/png", "image/jpeg"}:
        fail(415, "unsupported_media_type", "Poster must use image/png or image/jpeg")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_UPLOAD_BYTES:
            fail(413, "poster_too_large", "Poster must not exceed 5 MiB")
        body.extend(chunk)
    prepared = await run_in_threadpool(_prepare, bytes(body), mime)
    return await run_in_threadpool(_save, session, campaign_id, who, expected_revision, prepared)


def _asset(session, campaign_id, poster_id, who):
    scoped_campaign(session, campaign_id, who)
    asset = session.scalar(
        select(PosterAsset).where(
            PosterAsset.id == poster_id, PosterAsset.campaign_id == campaign_id
        )
    )
    if not asset:
        fail(404, "not_found", "Poster not found")
    return asset


@router.get("/posters", response_model=PosterOut)
def latest_poster(
    campaign_id: str,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    scoped_campaign(session, campaign_id, who)
    asset = session.scalar(
        select(PosterAsset)
        .where(PosterAsset.campaign_id == campaign_id)
        .order_by(PosterAsset.content_revision.desc())
        .limit(1)
    )
    if not asset:
        fail(404, "not_found", "Poster not found")
    return asset


@router.get("/posters/{poster_id}", response_model=PosterOut)
def get_poster(
    campaign_id: str,
    poster_id: str,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    return _asset(session, campaign_id, poster_id, who)


@router.get("/posters/{poster_id}/content")
def poster_content(
    campaign_id: str,
    poster_id: str,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    asset = _asset(session, campaign_id, poster_id, who)
    return Response(
        asset.normalized_bytes,
        media_type=asset.mime,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )

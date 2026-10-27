"""Private, revision-bound owner logo references and conservative local comparison."""

import hashlib
import time
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, Query, Request, Response
from PIL import Image, ImageChops, ImageStat
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, UniqueConstraint, event, select
from sqlalchemy.orm import Mapped, Session, mapped_column
from starlette.concurrency import run_in_threadpool

from brandproof.auth import actor, db, lock_campaign, require_role, scoped_campaign
from brandproof.db import Base
from brandproof.errors import fail
from brandproof.models import Actor, new_id, utcnow
from brandproof.poster_models import PosterAsset
from brandproof.posters import MAX_UPLOAD_BYTES, _prepare
from brandproof.schemas import MAX_INCREMENT_EXPECTATION, StrictModel

router = APIRouter(prefix="/api/v1/campaigns/{campaign_id}", tags=["brand logo"])


class BrandLogo(Base):
    __tablename__ = "brand_logos"
    __table_args__ = (UniqueConstraint("campaign_id", "version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    version: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(20))
    normalized_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    sha256: Mapped[str] = mapped_column(String(64))
    width: Mapped[int] = mapped_column()
    height: Mapped[int] = mapped_column()
    confirmed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


@event.listens_for(BrandLogo, "before_update")
@event.listens_for(BrandLogo, "before_delete")
def reject_logo_mutation(_mapper, _connection, _target):
    raise ValueError("Brand logo versions are immutable")


class LogoOut(BaseModel):
    id: str
    campaign_id: str
    version: int
    status: str
    sha256: str
    width: int
    height: int
    confirmed_by: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class LogoConfirm(StrictModel):
    expected_version: int = Field(ge=1, le=MAX_INCREMENT_EXPECTATION)
    expected_source_revision: int = Field(ge=0, le=MAX_INCREMENT_EXPECTATION)


def latest_logo(session, campaign_id):
    return session.scalar(
        select(BrandLogo)
        .where(BrandLogo.campaign_id == campaign_id)
        .order_by(BrandLogo.version.desc())
        .limit(1)
    )


@router.get("/brand-logo", response_model=LogoOut)
def get_logo(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    scoped_campaign(session, campaign_id, who)
    row = latest_logo(session, campaign_id)
    if not row:
        fail(404, "not_found", "No brand logo uploaded")
    return row


@router.get("/brand-logo/history", response_model=list[LogoOut])
def logo_history(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    scoped_campaign(session, campaign_id, who)
    return session.scalars(
        select(BrandLogo).where(BrandLogo.campaign_id == campaign_id).order_by(BrandLogo.version)
    ).all()


@router.get("/brand-logo/{logo_id}/content")
def logo_content(
    campaign_id: str, logo_id: str, who: Actor = Depends(actor), session: Session = Depends(db)
):
    scoped_campaign(session, campaign_id, who)
    row = session.get(BrandLogo, logo_id)
    if not row or row.campaign_id != campaign_id:
        fail(404, "not_found", "Logo not found")
    return Response(
        row.normalized_bytes,
        media_type="image/png",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


def save_logo(session, campaign_id, who, expected, prepared):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "owner")
    lock_campaign(session, campaign)
    if campaign.source_revision != expected:
        fail(409, "version_conflict", "Brand information changed; reload before uploading logo")
    head = latest_logo(session, campaign_id)
    png, width, height, _ = prepared
    row = BrandLogo(
        campaign_id=campaign_id,
        version=head.version + 1 if head else 1,
        status="pending",
        normalized_bytes=png,
        sha256=hashlib.sha256(png).hexdigest(),
        width=width,
        height=height,
    )
    session.add(row)
    campaign.source_revision += 1
    session.commit()
    return LogoOut.model_validate(row)


@router.put("/brand-logo", response_model=LogoOut)
async def upload_logo(
    campaign_id: str,
    request: Request,
    expected_source_revision: int = Query(ge=0, le=MAX_INCREMENT_EXPECTATION),
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    scoped_campaign(session, campaign_id, who)
    require_role(who, "owner")
    session.rollback()
    mime = request.headers.get("content-type", "").split(";", 1)[0].lower().strip()
    if mime not in {"image/png", "image/jpeg"}:
        fail(415, "unsupported_media_type", "Logo must be PNG or JPEG")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_UPLOAD_BYTES:
            fail(413, "logo_too_large", "Logo must not exceed 5 MiB")
        data.extend(chunk)
    prepared = await run_in_threadpool(_prepare, bytes(data), mime)
    return await run_in_threadpool(
        save_logo, session, campaign_id, who, expected_source_revision, prepared
    )


@router.post("/brand-logo/{logo_id}/confirm", response_model=LogoOut)
def confirm_logo(
    campaign_id: str,
    logo_id: str,
    payload: LogoConfirm,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "owner")
    lock_campaign(session, campaign)
    head = latest_logo(session, campaign_id)
    if (
        not head
        or head.id != logo_id
        or head.version != payload.expected_version
        or campaign.source_revision != payload.expected_source_revision
        or head.status != "pending"
    ):
        fail(409, "version_conflict", "Logo or brand information changed; reload before confirming")
    row = BrandLogo(
        campaign_id=campaign_id,
        version=head.version + 1,
        status="approved",
        normalized_bytes=head.normalized_bytes,
        sha256=head.sha256,
        width=head.width,
        height=head.height,
        confirmed_by=who.id,
    )
    session.add(row)
    campaign.source_revision += 1
    session.commit()
    return row


def compare_logo(reference: bytes, poster: bytes, *, max_seconds=2.0):
    """Bounded template search, not a semantic logo detector or calibrated confidence."""
    logo = Image.open(BytesIO(reference)).convert("RGB")
    bounds = ImageChops.difference(logo, Image.new("RGB", logo.size, "white")).getbbox()
    if not bounds or min(bounds[2] - bounds[0], bounds[3] - bounds[1]) < 8:
        return {
            "status": "not_assessed",
            "reason": "Reference is blank or too small for comparison.",
        }
    logo = logo.crop(bounds)
    # A full poster can resemble another full poster while hiding a changed
    # small logo. Refuse separated artwork/text blocks instead of averaging
    # their layout into a misleading low-resolution logo template.
    foreground = (
        ImageChops.difference(logo, Image.new("RGB", logo.size, "white"))
        .convert("L")
        .point(lambda value: 255 if value > 20 else 0)
    )
    rows = list(foreground.resize((1, logo.height), Image.Resampling.BOX).tobytes())
    occupied = [i for i, value in enumerate(rows) if value > 2]
    if occupied:
        longest_gap = max(
            (right - left - 1 for left, right in zip(occupied, occupied[1:], strict=False)),
            default=0,
        )
        if longest_gap > max(12, logo.height * 0.25):
            return {
                "status": "not_assessed",
                "reason": "Logo reference needs cropping: it contains widely separated artwork or text, which may be a full poster. Upload only the approved logo, confirm the new reference, then run review again.",
            }
    target = logo.resize((16, 16), Image.Resampling.LANCZOS)
    image = Image.open(BytesIO(poster)).convert("RGB")
    original = image.size
    image.thumbnail((160, 160))
    deadline = time.monotonic() + max_seconds
    best = (0.0, None)
    # Restrict sizes/aspect ratio, time and pixel count. Unsupported rotations,
    # busy/transparent backgrounds and tiny marks remain uncertain.
    for width in range(12, image.width + 1, 4):
        height = round(width * logo.height / logo.width)
        if height < 8 or height > image.height:
            continue
        step = max(2, width // 8)
        for y in range(0, image.height - height + 1, step):
            for x in range(0, image.width - width + 1, step):
                if time.monotonic() > deadline:
                    return {
                        "status": "not_assessed",
                        "reason": "Logo search time limit reached; manual comparison required.",
                    }
                patch = image.crop((x, y, x + width, y + height)).resize(
                    (16, 16), Image.Resampling.LANCZOS
                )
                score = 1 - sum(ImageStat.Stat(ImageChops.difference(target, patch)).mean) / (
                    3 * 255
                )
                if score > best[0]:
                    best = (score, (x, y, width, height))
    # A high similarity is still a candidate, never approval or proof of identity.
    return {
        "status": "partial",
        "reason": "A similar logo candidate was found; verify fine details manually."
        if best[0] >= 0.97
        else "Possible logo mismatch: the approved logo was not matched closely. It may be altered, missing, too small or obscured. Owner review required.",
        "similarity": round(best[0], 4),
        "similar_candidate": best[0] >= 0.97,
        "algorithm": "bounded_rgb_template_v1",
        "poster_dimensions": list(original),
    }


def review_logo(session, campaign, poster_check):
    logo = latest_logo(session, campaign.id)
    if not logo:
        return [], None, None
    snapshot = {
        "id": logo.id,
        "version_id": logo.id,
        "version": logo.version,
        "title": "Owner-confirmed brand logo",
        "rule": {"kind": "logo"},
        "text": f"Brand logo SHA-256 {logo.sha256}",
        "status": logo.status,
        "confirmed_by": logo.confirmed_by,
    }
    if logo.status != "approved":
        return (
            [],
            {
                "status": "not_assessed",
                "reason": "Brand logo is pending owner confirmation.",
                "reference_id": logo.id,
            },
            snapshot,
        )
    poster_id = poster_check.get("details", {}).get("asset_id")
    poster = session.get(PosterAsset, poster_id) if poster_id else None
    if not poster:
        return (
            [],
            {
                "status": "not_assessed",
                "reason": "Upload a poster for logo comparison.",
                "reference_id": logo.id,
            },
            snapshot,
        )
    result = {
        **compare_logo(logo.normalized_bytes, poster.normalized_bytes),
        "reference_id": logo.id,
        "reference_version": logo.version,
        "reference_sha256": logo.sha256,
        "poster_id": poster.id,
    }
    findings = []
    if result["status"] == "not_assessed" or (
        result["status"] == "partial" and not result.get("similar_candidate")
    ):
        findings.append(
            {
                "id": new_id(),
                "category": "logo",
                "severity": "warning",
                "evidence_status": "needs_clarification",
                "message": result["reason"],
                "location": {
                    "asset": "poster",
                    "content_revision": campaign.content_revision,
                    "poster_id": poster.id,
                    "boxes": [],
                    "start": None,
                    "end": None,
                    "quote": None,
                },
                "evidence": {
                    "source_id": logo.id,
                    "source_version_id": logo.id,
                    "source_version": logo.version,
                    "quote": snapshot["text"],
                },
                "suggested_replacement": None,
            }
        )
    return findings, result, snapshot

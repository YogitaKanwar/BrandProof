"""Curated, offline advertising-risk screening. No legal conclusions or model citations."""

import copy
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, event, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from brandproof.auth import actor, db, lock_campaign, require_role, scoped_campaign
from brandproof.claim_screening import screen_claims
from brandproof.db import Base
from brandproof.errors import fail
from brandproof.models import Actor, new_id, utcnow
from brandproof.review_schemas import ReviewCreate
from brandproof.sources import bump_source_snapshot

PACK = json.loads(Path(__file__).with_name("legal_pack.json").read_text())
PACK_DIGEST = hashlib.sha256(json.dumps(PACK, sort_keys=True).encode()).hexdigest()


class LegalProfile(Base):
    __tablename__ = "legal_profile_versions"
    __table_args__ = (UniqueConstraint("campaign_id", "source_revision"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    source_revision: Mapped[int] = mapped_column()
    profile: Mapped[dict] = mapped_column(JSON)
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProfileInput(ReviewCreate):
    jurisdiction: Literal["IN", "other", "unknown"]
    sector: Literal["general", "coaching", "healthcare", "finance", "other", "unknown"]
    language: Literal["en", "other", "unknown"]


@event.listens_for(LegalProfile, "before_update")
@event.listens_for(LegalProfile, "before_delete")
def immutable_profile(*_args):
    raise ValueError("Advertising profile versions are immutable")


class ProfileOut(BaseModel):
    profile: dict | None
    source_revision: int
    pack: dict


def profile_at(session, campaign):
    return session.scalar(
        select(LegalProfile)
        .where(LegalProfile.campaign_id == campaign.id)
        .order_by(LegalProfile.source_revision.desc())
        .limit(1)
    )


def legal_current(run):
    check = run.checks.get("advertising_risk", {})
    pinned = check.get("details", {}).get("pack_digest")
    # Legacy runs remain historical records of their actual scope. Never label
    # them legally assessed. Every new run pins the installed pack, even unset profiles.
    return not pinned or (
        pinned == PACK_DIGEST
        and (
            check.get("status") in {"not_assessed", "not_applicable"}
            or datetime.now(UTC).date().isoformat() <= PACK["review_due"]
            or check.get("details", {}).get("screening_paused") is True
        )
    )


def evaluate_advertising(session, campaign, findings, poster_check):
    row = profile_at(session, campaign)
    profile = copy.deepcopy(row.profile) if row else None
    details = {
        "profile": profile,
        "profile_version_id": row.id if row else None,
        "publication_date": campaign.publication_date.isoformat(),
        "pack": copy.deepcopy(PACK),
        "pack_digest": PACK_DIGEST,
        "scope": PACK["supported_scope"],
    }
    check = {
        "status": "not_assessed",
        "reason": "Owner: select jurisdiction, sector and language before advertising-risk screening.",
        "details": details,
    }
    if not profile or "unknown" in profile.values():
        return findings, check
    if profile["jurisdiction"] != "IN":
        check.update(
            status="not_applicable",
            reason="The installed India pack is not applicable to the selected jurisdiction. No other jurisdiction was assessed.",
        )
        return findings, check
    if profile["language"] != "en":
        check["reason"] = (
            "Only English pattern signals are supported; selected language requires manual assessment."
        )
        return findings, check
    publication = campaign.publication_date.isoformat()
    if publication < PACK["effective_from"] or (
        PACK["effective_until"] and publication > PACK["effective_until"]
    ):
        check.update(
            status="not_applicable",
            reason="Publication is outside this reference's verified effective dates. Other applicable instruments were not assessed.",
        )
        return findings, check
    if datetime.now(UTC).date().isoformat() > PACK["review_due"]:
        details["screening_paused"] = True
        check.update(
            status="partial",
            reason="This curated pack is due for source review. Screening is paused; obtain a current human assessment.",
        )
        return findings, check
    # Reuse the existing bounded match locations and IDs: a single finding can
    # explain both the local promise signal and the cited substantiation concern.
    matched = 0
    result = []
    rule = PACK["rules"][0]
    for finding in findings:
        item = copy.deepcopy(finding)
        if item["category"] == "claim_risk":
            matched += 1
            item["regulatory_evidence"] = {
                **rule,
                "pack_id": PACK["id"],
                "pack_version": PACK["version"],
                "source_url": PACK["source_url"],
                "source_title": PACK["source_title"],
                "source_sha256": PACK["source_sha256"],
                "retrieved_at": PACK["retrieved_at"],
                "jurisdiction": "IN",
                "sector": profile["sector"],
            }
        result.append(item)
    _, caption_check = screen_claims(campaign.caption, campaign.content_revision)
    ocr_risk = poster_check.get("details", {}).get("claim_risk", {})
    uncertain = caption_check.get("details", {}).get("limited", False) or bool(
        poster_check.get("details", {}).get("asset_id") and ocr_risk.get("status") != "completed"
    )
    sector_partial = profile["sector"] != "general"
    check.update(
        status="partial" if matched or uncertain or sector_partial else "completed",
        reason="Selected English claim signals checked against a frozen general substantiation reference. No matches does not verify truth or legal compliance."
        + (" Review the cited claim findings and record supporting evidence." if matched else "")
        + (" OCR/screening coverage is incomplete." if uncertain else "")
        + (
            " Sector-specific regulation is not implemented; obtain a sector review."
            if sector_partial
            else ""
        ),
    )
    details["finding_count"] = matched
    return result, check


router = APIRouter(prefix="/api/v1", tags=["advertising risk"])


@router.get("/advertising-risk-pack")
def get_pack():
    return {"pack": PACK, "digest": PACK_DIGEST}


@router.get("/campaigns/{campaign_id}/advertising-profile", response_model=ProfileOut)
def get_profile(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    campaign = scoped_campaign(session, campaign_id, who)
    row = profile_at(session, campaign)
    return {
        "profile": row.profile if row else None,
        "source_revision": campaign.source_revision,
        "pack": PACK,
    }


@router.put("/campaigns/{campaign_id}/advertising-profile", response_model=ProfileOut)
def set_profile(
    campaign_id: str,
    payload: ProfileInput,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "owner")
    lock_campaign(session, campaign)
    if (campaign.content_revision, campaign.source_revision) != (
        payload.expected_content_revision,
        payload.expected_source_revision,
    ):
        fail(
            409,
            "version_conflict",
            "Campaign changed; reload before saving the advertising profile",
        )
    profile = payload.model_dump(exclude={"expected_content_revision", "expected_source_revision"})
    bump_source_snapshot(session, campaign.id)
    session.flush()
    session.refresh(campaign)
    session.add(
        LegalProfile(
            campaign_id=campaign.id,
            source_revision=campaign.source_revision,
            profile=profile,
            actor_id=who.id,
        )
    )
    session.commit()
    return {"profile": profile, "source_revision": campaign.source_revision, "pack": PACK}

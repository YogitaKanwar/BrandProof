"""Poster-specific, immutable creator descriptions sharing content revision locks."""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, event, select, update
from sqlalchemy.orm import Mapped, Session, mapped_column

from brandproof.auth import actor, db, lock_campaign, require_role, scoped_campaign
from brandproof.db import Base
from brandproof.errors import fail
from brandproof.models import Actor, Campaign, new_id, utcnow
from brandproof.poster_models import PosterAsset
from brandproof.review_models import ContentVersion
from brandproof.schemas import MAX_INCREMENT_EXPECTATION, CampaignOut, StrictModel
from brandproof.workflow_models import RevisionAuthor


class AltTextVersion(Base):
    __tablename__ = "alt_text_versions"
    __table_args__ = (UniqueConstraint("campaign_id", "content_revision"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    poster_id: Mapped[str] = mapped_column(ForeignKey("poster_assets.id"))
    content_revision: Mapped[int] = mapped_column()
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


@event.listens_for(AltTextVersion, "before_update")
@event.listens_for(AltTextVersion, "before_delete")
def immutable_alt_text(*_args):
    raise ValueError("Alt text revisions are immutable")


def current_poster(session, campaign):
    return session.scalar(
        select(PosterAsset)
        .where(
            PosterAsset.campaign_id == campaign.id,
            PosterAsset.content_revision <= campaign.content_revision,
        )
        .order_by(PosterAsset.content_revision.desc())
        .limit(1)
    )


def alt_text_for(session, campaign, poster):
    if not poster:
        return None
    return session.scalar(
        select(AltTextVersion)
        .where(
            AltTextVersion.campaign_id == campaign.id,
            AltTextVersion.poster_id == poster.id,
            AltTextVersion.content_revision <= campaign.content_revision,
        )
        .order_by(AltTextVersion.content_revision.desc())
        .limit(1)
    )


class AltTextUpdate(StrictModel):
    expected_revision: int = Field(ge=1, le=MAX_INCREMENT_EXPECTATION)
    text: str = Field(max_length=4000)


class AltTextOut(BaseModel):
    poster_id: str | None
    content_revision: int
    text: str


router = APIRouter(prefix="/api/v1/campaigns/{campaign_id}/alt-text", tags=["accessibility"])


@router.get("", response_model=AltTextOut)
def get_alt_text(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    campaign = scoped_campaign(session, campaign_id, who)
    poster = current_poster(session, campaign)
    version = alt_text_for(session, campaign, poster)
    return {
        "poster_id": poster.id if poster else None,
        "content_revision": campaign.content_revision,
        "text": version.text if version else "",
    }


@router.put("", response_model=CampaignOut)
def save_alt_text(
    campaign_id: str,
    payload: AltTextUpdate,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "creator", "owner")
    lock_campaign(session, campaign)
    if campaign.content_revision != payload.expected_revision:
        fail(409, "version_conflict", "Content changed; reload before saving alt text")
    poster = current_poster(session, campaign)
    if not poster:
        fail(422, "poster_required", "Attach a poster before writing its description")
    changed = session.execute(
        update(Campaign)
        .where(Campaign.id == campaign_id, Campaign.content_revision == payload.expected_revision)
        .values(content_revision=Campaign.content_revision + 1),
        execution_options={"synchronize_session": False},
    )
    if changed.rowcount != 1:
        fail(409, "version_conflict", "Content changed")
    session.add_all(
        [
            AltTextVersion(
                campaign_id=campaign_id,
                poster_id=poster.id,
                content_revision=payload.expected_revision + 1,
                text=payload.text,
            ),
            ContentVersion(
                campaign_id=campaign_id,
                revision=payload.expected_revision + 1,
                caption=campaign.caption,
            ),
            RevisionAuthor(
                campaign_id=campaign_id,
                content_revision=payload.expected_revision + 1,
                actor_id=who.id,
            ),
        ]
    )
    session.commit()
    session.refresh(campaign)
    return campaign

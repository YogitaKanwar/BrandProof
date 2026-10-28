"""Reversible removal from the review workspace; audit records are retained."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from brandproof.db import Base
from brandproof.models import new_id, utcnow


class CampaignRemoval(Base):
    __tablename__ = "campaign_removals"
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), primary_key=True)
    id: Mapped[str] = mapped_column(String(36), unique=True, default=new_id)
    removed_by: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    removed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


def active_campaigns():
    from sqlalchemy import select

    from brandproof.models import Campaign

    return (
        ~select(CampaignRemoval.campaign_id)
        .where(CampaignRemoval.campaign_id == Campaign.id)
        .exists()
    )

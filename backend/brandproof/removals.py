from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from brandproof.auth import actor, db, lock_campaign, require_role, scoped_campaign
from brandproof.errors import fail
from brandproof.models import Actor, Campaign
from brandproof.removal_models import CampaignRemoval
from brandproof.review_models import ReviewRun
from brandproof.review_schemas import ReviewCreate
from brandproof.schemas import CampaignOut
from brandproof.workflow import require_snapshot

router = APIRouter(prefix="/api/v1/campaigns", tags=["review removal"])


class RemovalOut(BaseModel):
    campaign_id: str
    deletion_id: str
    deleted: bool
    retained_history: bool


class RestoreCreate(ReviewCreate):
    expected_deletion_id: str = Field(min_length=36, max_length=36)


@router.delete("/{campaign_id}", response_model=RemovalOut)
def remove_review(
    campaign_id: str,
    payload: ReviewCreate,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "owner")
    lock_campaign(session, campaign)
    require_snapshot(campaign, payload)
    if session.scalar(
        select(ReviewRun.id)
        .where(ReviewRun.campaign_id == campaign_id, ReviewRun.status == "running")
        .limit(1)
    ):
        fail(
            409,
            "review_in_progress",
            "A review is still running. Wait for completion or interrupted-run recovery, then refresh before deleting.",
        )
    removal = CampaignRemoval(campaign_id=campaign_id, removed_by=who.id)
    session.add(removal)
    session.flush()
    deletion_id = removal.id
    session.commit()
    return {
        "campaign_id": campaign_id,
        "deletion_id": deletion_id,
        "deleted": True,
        "retained_history": True,
    }


@router.post("/{campaign_id}/restore", response_model=CampaignOut)
def restore_review(
    campaign_id: str,
    payload: RestoreCreate,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    # Restoration alone may resolve a removed campaign; all ordinary reads/writes exclude it.
    campaign = session.scalar(
        select(Campaign).where(
            Campaign.id == campaign_id, Campaign.workspace_id == who.workspace_id
        )
    )
    if not campaign:
        fail(404, "not_found", "Campaign not found")
    require_role(who, "owner")
    lock_campaign(session, campaign, allow_removed=True)
    require_snapshot(campaign, payload)
    removal = session.get(CampaignRemoval, campaign_id)
    if not removal or removal.id != payload.expected_deletion_id:
        fail(
            409,
            "removal_conflict",
            "This deletion has changed or was already undone. Refresh before continuing.",
        )
    session.delete(removal)
    session.commit()
    session.refresh(campaign)
    return campaign

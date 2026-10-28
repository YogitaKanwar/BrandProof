from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from brandproof.auth import actor, db, lock_campaign, require_role, scoped_campaign
from brandproof.errors import fail
from brandproof.models import Actor
from brandproof.review_models import ContentVersion
from brandproof.review_schemas import CaptionUpdate, ReviewCreate
from brandproof.reviews import update_caption
from brandproof.schemas import CampaignOut
from brandproof.workflow import ensure_current, finding_in, require_snapshot, scoped_run
from brandproof.workflow_schemas import RevisionOut

router = APIRouter(prefix="/api/v1/campaigns/{campaign_id}", tags=["revisions"])


@router.post("/reviews/{review_id}/findings/{finding_id}/apply", response_model=CampaignOut)
def apply_suggestion(
    campaign_id: str,
    review_id: str,
    finding_id: str,
    payload: ReviewCreate,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "owner", "creator")
    lock_campaign(session, campaign)
    require_snapshot(campaign, payload)
    run = scoped_run(session, campaign_id, review_id)
    ensure_current(campaign, run)
    item = finding_in(run, finding_id)
    replacement = item.get("suggested_replacement")
    location = item["location"]
    if replacement is None or item["evidence_status"] == "needs_clarification":
        fail(409, "manual_edit_required", "No safe automatic text replacement is available")
    if location["asset"] != "caption":
        fail(
            409,
            "poster_reupload_required",
            "Upload a revised poster; image suggestions cannot edit the caption",
        )
    if location.get("start") is None:
        if item["category"] != "required_text":
            fail(409, "manual_edit_required", "This suggestion has no text span")
        new_text = campaign.caption.rstrip() + "\n" + replacement
    else:
        start, end = location["start"], location["end"]
        if campaign.caption[start:end] != location["quote"]:
            fail(409, "suggestion_conflict", "Original text no longer matches the suggestion")
        new_text = campaign.caption[:start] + replacement + campaign.caption[end:]
    if len(new_text) > 20000:
        fail(
            409, "manual_edit_required", "Suggested edit exceeds the caption limit; revise manually"
        )
    update = CaptionUpdate(expected_revision=campaign.content_revision, text=new_text)
    return update_caption(campaign_id, update, who, session)


@router.get("/revisions", response_model=list[RevisionOut])
def revisions(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    campaign = scoped_campaign(session, campaign_id, who)
    rows = session.scalars(
        select(ContentVersion)
        .where(ContentVersion.campaign_id == campaign_id)
        .order_by(ContentVersion.revision)
    ).all()
    if not rows:
        return [
            {
                "revision": campaign.content_revision,
                "caption": campaign.caption,
                "created_at": campaign.created_at,
            }
        ]
    return [
        {"revision": row.revision, "caption": row.caption, "created_at": row.created_at}
        for row in rows
    ]

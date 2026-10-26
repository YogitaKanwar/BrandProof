from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from brandproof.auth import actor, db, lock_campaign, require_role, scoped_campaign
from brandproof.errors import fail
from brandproof.models import Actor, Campaign
from brandproof.review_models import ContentVersion, ReviewRun
from brandproof.review_schemas import CaptionUpdate, ReviewCreate, ReviewOut
from brandproof.rules import exact_checks
from brandproof.schemas import CampaignOut
from brandproof.source_models import Source, SourceVersion
from brandproof.sources import render_source

router = APIRouter(prefix="/api/v1/campaigns/{campaign_id}", tags=["reviews"])


@router.put("/caption", response_model=CampaignOut)
def update_caption(
    campaign_id: str,
    payload: CaptionUpdate,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "owner", "creator")
    lock_campaign(session, campaign)
    if not payload.text.strip():
        fail(422, "empty_caption", "Caption must contain text")
    initial_caption = campaign.caption
    changed = session.execute(
        update(Campaign)
        .where(
            Campaign.id == campaign_id,
            Campaign.content_revision == payload.expected_revision,
        )
        .values(caption=payload.text, content_revision=Campaign.content_revision + 1),
        execution_options={"synchronize_session": False},
    )
    if changed.rowcount != 1:
        fail(409, "version_conflict", "Caption changed; reload before saving")
    # Only the successful compare-and-swap may initialise legacy revision-one history.
    if payload.expected_revision == 1 and not session.scalar(
        select(ContentVersion.id).where(
            ContentVersion.campaign_id == campaign_id, ContentVersion.revision == 1
        )
    ):
        session.add(ContentVersion(campaign_id=campaign_id, revision=1, caption=initial_caption))
    session.add(
        ContentVersion(
            campaign_id=campaign_id,
            revision=payload.expected_revision + 1,
            caption=payload.text,
        )
    )
    session.commit()
    session.refresh(campaign)
    return campaign


def render_run(run: ReviewRun, campaign: Campaign):
    return {
        "id": run.id,
        "campaign_id": run.campaign_id,
        "content_revision": run.content_revision,
        "source_revision": run.source_revision,
        "caption": run.caption,
        "status": run.status,
        "is_current": run.content_revision == campaign.content_revision
        and run.source_revision == campaign.source_revision,
        "readiness": "not_approved",
        "checks": run.checks,
        "sources_used": run.sources_used,
        "excluded_sources": run.excluded_sources,
        "findings": run.findings,
        "created_at": run.created_at,
    }


@router.post("/reviews", status_code=201, response_model=ReviewOut)
def start_review(
    campaign_id: str,
    payload: ReviewCreate,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "owner", "creator")
    lock_campaign(session, campaign)
    if (
        campaign.content_revision != payload.expected_content_revision
        or campaign.source_revision != payload.expected_source_revision
    ):
        fail(
            409,
            "version_conflict",
            "Content or sources changed; reload before reviewing",
        )
    if not campaign.caption.strip():
        fail(422, "empty_caption", "Save a caption before reviewing")
    rows = session.execute(
        select(Source, SourceVersion)
        .join(
            SourceVersion,
            (Source.id == SourceVersion.source_id)
            & (Source.current_version == SourceVersion.version),
        )
        .where(Source.campaign_id == campaign_id)
    ).all()
    active = [
        render_source(s, v)
        for s, v in rows
        if v.status == "approved"
        and (not v.valid_from or v.valid_from <= campaign.publication_date)
        and (not v.valid_until or campaign.publication_date <= v.valid_until)
    ]
    excluded = []
    for source, version in rows:
        reason = None
        if version.status != "approved":
            reason = "pending_owner_confirmation"
        elif version.valid_from and version.valid_from > campaign.publication_date:
            reason = "not_yet_valid_for_publication_date"
        elif version.valid_until and version.valid_until < campaign.publication_date:
            reason = "expired_for_publication_date"
        if reason:
            excluded.append(
                {
                    "source_id": source.id,
                    "source_version": version.version,
                    "kind": version.rule["kind"],
                    "reason": reason,
                }
            )
    exact_kinds = {"price", "date", "terminology", "required_text"}
    has_exact = any(s["rule"]["kind"] in exact_kinds for s in active)
    excluded_exact = any(s["kind"] in exact_kinds for s in excluded)
    sources = [
        {
            **s,
            "created_at": s["created_at"].isoformat(),
            "valid_from": s["valid_from"].isoformat() if s["valid_from"] else None,
            "valid_until": s["valid_until"].isoformat() if s["valid_until"] else None,
        }
        for s in active
    ]
    findings, coverage = exact_checks(campaign.caption, campaign.content_revision, active)
    if not coverage or all(r["status"] == "not_assessed" for r in coverage):
        exact_status = "not_assessed"
    elif excluded_exact or any(r["status"] != "completed" for r in coverage):
        exact_status = "partial"
    else:
        exact_status = "completed"
    if has_exact and any(f["evidence_status"] == "needs_clarification" for f in findings):
        exact_status = "partial"
    run = ReviewRun(
        campaign_id=campaign_id,
        content_revision=campaign.content_revision,
        source_revision=campaign.source_revision,
        caption=campaign.caption,
        status="partial",
        checks={
            "exact_text": {
                "status": exact_status,
                "reason": None
                if exact_status == "completed"
                else "Some rules lack comparable supported expressions, or require source/scope clarification or renewal.",
                "rules": coverage,
            },
            "contextual": {
                "status": "unavailable",
                "reason": "No AI provider is connected in this milestone.",
            },
            "poster": {
                "status": "not_assessed",
                "reason": "Poster review is not implemented in this milestone.",
            },
        },
        sources_used=sources,
        excluded_sources=excluded,
        findings=findings,
    )
    # Recheck immutable snapshot identity rather than presenting a mixed-version run.
    latest = session.execute(
        select(Campaign.content_revision, Campaign.source_revision).where(
            Campaign.id == campaign_id
        )
    ).one()
    if tuple(latest) != (
        payload.expected_content_revision,
        payload.expected_source_revision,
    ):
        fail(
            409,
            "version_conflict",
            "Campaign changed during review; retry on the latest version",
        )
    session.add(run)
    session.commit()
    # Observe actual current state, rather than the pre-commit identity-map cache.
    session.refresh(campaign)
    return render_run(run, campaign)


@router.get("/reviews", response_model=list[ReviewOut])
def list_reviews(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    campaign = scoped_campaign(session, campaign_id, who)
    return [
        render_run(run, campaign)
        for run in session.scalars(
            select(ReviewRun)
            .where(ReviewRun.campaign_id == campaign_id)
            .order_by(ReviewRun.created_at.desc())
        )
    ]


@router.get("/reviews/{review_id}", response_model=ReviewOut)
def get_review(
    campaign_id: str,
    review_id: str,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    run = session.scalar(
        select(ReviewRun).where(ReviewRun.id == review_id, ReviewRun.campaign_id == campaign_id)
    )
    if not run:
        fail(404, "not_found", "Review not found")
    return render_run(run, campaign)

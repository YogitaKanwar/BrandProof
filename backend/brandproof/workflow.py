from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from brandproof.auth import actor, db, lock_campaign, require_role, scoped_campaign
from brandproof.errors import fail
from brandproof.models import Actor
from brandproof.review_models import ReviewRun
from brandproof.review_schemas import ReviewCreate
from brandproof.workflow_models import Comment, FindingDecision, ReviewRequest
from brandproof.workflow_schemas import (
    CommentCreate,
    CommentOut,
    FindingDecisionCreate,
    FindingDecisionOut,
    ReviewRequestOut,
)

router = APIRouter(prefix="/api/v1/campaigns/{campaign_id}", tags=["collaboration"])


def ensure_current(campaign, run):
    if (run.content_revision, run.source_revision) != (
        campaign.content_revision,
        campaign.source_revision,
    ):
        fail(409, "stale_review", "Review is no longer current")


def finding_in(run, finding_id):
    finding = next((f for f in run.findings if f["id"] == finding_id), None)
    if not finding:
        fail(404, "not_found", "Finding not found")
    return finding


def decision_rows(session, review_id, finding_id=None):
    query = select(FindingDecision).where(FindingDecision.review_id == review_id)
    if finding_id is not None:
        query = query.where(FindingDecision.finding_id == finding_id)
    return session.scalars(
        query.order_by(FindingDecision.created_at, FindingDecision.version, FindingDecision.id)
    ).all()


@router.post(
    "/reviews/{review_id}/findings/{finding_id}/decisions",
    status_code=201,
    response_model=FindingDecisionOut,
)
def decide_finding(
    campaign_id: str,
    review_id: str,
    finding_id: str,
    payload: FindingDecisionCreate,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "owner", "reviewer")
    lock_campaign(session, campaign)
    require_snapshot(campaign, payload)
    run = scoped_run(session, campaign_id, review_id)
    ensure_current(campaign, run)
    finding_in(run, finding_id)
    rows = decision_rows(session, review_id, finding_id)
    version = rows[-1].version if rows else 0
    if version != payload.expected_decision_version:
        fail(409, "decision_conflict", "Finding decision changed; reload before deciding")
    row = FindingDecision(
        review_id=review_id,
        finding_id=finding_id,
        version=version + 1,
        actor_id=who.id,
        decision=payload.decision,
        reason=payload.reason,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.get(
    "/reviews/{review_id}/findings/{finding_id}/decisions", response_model=list[FindingDecisionOut]
)
def finding_decisions(
    campaign_id: str,
    review_id: str,
    finding_id: str,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    scoped_campaign(session, campaign_id, who)
    run = scoped_run(session, campaign_id, review_id)
    finding_in(run, finding_id)
    return decision_rows(session, review_id, finding_id)


@router.post("/reviews/{review_id}/requests", status_code=201, response_model=ReviewRequestOut)
def request_review(
    campaign_id: str,
    review_id: str,
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
    row = ReviewRequest(campaign_id=campaign_id, review_id=review_id, requested_by=who.id)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.get("/receipt")
def receipt(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    campaign = scoped_campaign(session, campaign_id, who)
    from brandproof.approval import build_receipt

    return build_receipt(session, campaign)


def require_snapshot(campaign, payload: ReviewCreate):
    if (campaign.content_revision, campaign.source_revision) != (
        payload.expected_content_revision,
        payload.expected_source_revision,
    ):
        fail(409, "version_conflict", "Campaign changed; reload before continuing")


def scoped_run(session, campaign_id, review_id):
    run = session.scalar(
        select(ReviewRun).where(ReviewRun.id == review_id, ReviewRun.campaign_id == campaign_id)
    )
    if not run:
        fail(404, "not_found", "Review not found")
    return run


@router.post("/comments", status_code=201, response_model=CommentOut)
def create_comment(
    campaign_id: str,
    payload: CommentCreate,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    lock_campaign(session, campaign)
    require_snapshot(campaign, payload)
    if payload.review_id:
        run = scoped_run(session, campaign_id, payload.review_id)
        if (run.content_revision, run.source_revision) != (
            campaign.content_revision,
            campaign.source_revision,
        ):
            fail(409, "stale_review", "Review is no longer current")
    row = Comment(
        campaign_id=campaign_id,
        review_id=payload.review_id,
        actor_id=who.id,
        actor_role=who.role,
        content_revision=campaign.content_revision,
        source_revision=campaign.source_revision,
        text=payload.text,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.get("/comments", response_model=list[CommentOut])
def list_comments(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    scoped_campaign(session, campaign_id, who)
    return session.scalars(
        select(Comment)
        .where(Comment.campaign_id == campaign_id)
        .order_by(Comment.created_at, Comment.id)
    ).all()

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from brandproof.auth import actor, db, lock_campaign, require_role, scoped_campaign
from brandproof.errors import fail
from brandproof.legal import legal_current
from brandproof.models import Actor
from brandproof.review_models import ReviewRun
from brandproof.workflow import decision_rows, ensure_current, require_snapshot, scoped_run
from brandproof.workflow_models import Approval, ReviewRequest, RevisionAuthor
from brandproof.workflow_schemas import ApprovalCreate, ApprovalOut, ReviewRequestOut

router = APIRouter(prefix="/api/v1/campaigns/{campaign_id}", tags=["human review"])


def current_decisions(session, review_id):
    result = {}
    for row in decision_rows(session, review_id):
        if row.finding_id not in result or row.version > result[row.finding_id].version:
            result[row.finding_id] = row
    return result


def latest_run(session, campaign_id):
    return session.scalar(
        select(ReviewRun)
        .where(ReviewRun.campaign_id == campaign_id)
        .order_by(ReviewRun.created_at.desc(), ReviewRun.id.desc())
        .limit(1)
    )


def latest_request(session, campaign_id):
    return session.scalar(
        select(ReviewRequest)
        .where(ReviewRequest.campaign_id == campaign_id)
        .order_by(ReviewRequest.created_at.desc(), ReviewRequest.id.desc())
        .limit(1)
    )


def decision_ids(session, review_id):
    return {key: value.id for key, value in current_decisions(session, review_id).items()}


def approval_current(session, campaign, row):
    if (row.content_revision, row.source_revision) != (
        campaign.content_revision,
        campaign.source_revision,
    ):
        return False
    run, request = latest_run(session, campaign.id), latest_request(session, campaign.id)
    return bool(
        run
        and legal_current(run)
        and request
        and run.id == row.review_id
        and request.id == row.request_id
        and row.decision_snapshot == decision_ids(session, row.review_id)
    )


def approval_rows(session, campaign_id):
    return session.scalars(
        select(Approval)
        .where(Approval.campaign_id == campaign_id)
        .order_by(Approval.created_at, Approval.id)
    ).all()


def readiness(session, campaign, review_id=None):
    rows = approval_rows(session, campaign.id)
    if not rows:
        return "not_approved"
    row = rows[-1]
    if not approval_current(session, campaign, row) or (review_id and row.review_id != review_id):
        return "stale"
    if row.decision == "request_changes":
        return "changes_requested"
    return "approved_with_manual_checks" if row.manual_checks else "approved"


def render_approval(session, campaign, row):
    values = {column.name: getattr(row, column.name) for column in row.__table__.columns}
    values["is_current"] = approval_current(session, campaign, row)
    run = session.get(ReviewRun, row.review_id)
    values["advertising_snapshot"] = (
        run.checks.get(
            "advertising_risk",
            {
                "status": "not_assessed",
                "reason": "This historical run predates advertising-risk screening.",
            },
        )
        if run
        else {"status": "not_assessed"}
    )
    return values


def build_receipt(session, campaign):
    run = latest_run(session, campaign.id)
    requests = session.scalars(
        select(ReviewRequest)
        .where(ReviewRequest.campaign_id == campaign.id)
        .order_by(ReviewRequest.created_at, ReviewRequest.id)
    ).all()
    return {
        "campaign_id": campaign.id,
        "content_revision": campaign.content_revision,
        "source_revision": campaign.source_revision,
        "readiness": readiness(session, campaign),
        "scope": "caption_and_attached_poster"
        if run and run.checks.get("poster", {}).get("details", {}).get("asset_id")
        else "caption",
        "automated_review_status": run.status if run else None,
        "checks": run.checks if run else {},
        "sources_used": run.sources_used if run else [],
        "requests": [
            ReviewRequestOut.model_validate(row).model_dump(mode="json") for row in requests
        ],
        "approvals": [
            ApprovalOut.model_validate(render_approval(session, campaign, row)).model_dump(
                mode="json"
            )
            for row in approval_rows(session, campaign.id)
        ],
        "finding_decisions": [
            {
                "finding_id": key,
                "decision_id": row.id,
                "decision": row.decision,
                "reason": row.reason,
                "actor_id": row.actor_id,
                "version": row.version,
            }
            for key, row in current_decisions(session, run.id).items()
        ]
        if run
        else [],
        "notice": "Human decision record inside BrandProof, not legal certification or control of external publication. Manual checks are reviewer attestations, not AI completion.",
    }


@router.post("/reviews/{review_id}/approvals", status_code=201, response_model=ApprovalOut)
def approve(
    campaign_id: str,
    review_id: str,
    payload: ApprovalCreate,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "owner", "reviewer")
    lock_campaign(session, campaign)
    require_snapshot(campaign, payload)
    run = scoped_run(session, campaign_id, review_id)
    ensure_current(campaign, run)
    if run.status == "running":
        fail(409, "review_in_progress", "Wait for this review to finish before making a decision")
    newest = latest_run(session, campaign_id)
    if newest.id != review_id:
        fail(409, "superseded_review", "A newer review exists; use its findings")
    request = session.scalar(
        select(ReviewRequest).where(
            ReviewRequest.id == payload.request_id,
            ReviewRequest.campaign_id == campaign_id,
            ReviewRequest.review_id == review_id,
        )
    )
    if not request:
        fail(404, "not_found", "Review request not found")
    if latest_request(session, campaign_id).id != request.id:
        fail(409, "superseded_request", "A newer review request exists")
    authors = set(
        session.scalars(
            select(RevisionAuthor.actor_id).where(RevisionAuthor.campaign_id == campaign_id)
        )
    )
    if request.requested_by == who.id or who.id in authors:
        fail(
            403,
            "self_approval",
            "A different authorised actor who has not edited the content must review this submission",
        )
    if not authors:
        fail(
            409,
            "unknown_content_author",
            "Create a traceable content revision before requesting approval",
        )
    if session.scalar(select(Approval.id).where(Approval.request_id == request.id)):
        fail(409, "already_decided", "This request already has a decision; request review again")
    decisions = current_decisions(session, review_id)
    manual = payload.manual_checks
    if payload.decision == "approve":
        if not run.sources_used or run.excluded_sources:
            fail(409, "sources_incomplete", "Confirm or renew campaign sources before approval")
        unresolved = [
            f["id"]
            for f in run.findings
            if (
                f["severity"] == "error"
                or f["evidence_status"] in {"needs_clarification", "insufficient_evidence"}
            )
            and (f["id"] not in decisions or decisions[f["id"]].decision == "reopen")
        ]
        if unresolved:
            fail(
                409,
                "unresolved_findings",
                "Resolve or explicitly except blocking findings before approval",
            )
        required = {"exact_text", "contextual"}
        if "claim_risk" in run.checks:
            required.add("claim_risk")
        if "advertising_risk" in run.checks:
            required.add("advertising_risk")
        if run.checks.get("poster", {}).get("details", {}).get("asset_id"):
            required.add("poster")
        incomplete = {
            name for name in required if run.checks.get(name, {}).get("status") != "completed"
        }
        if set(manual) != incomplete:
            fail(
                409,
                "checks_incomplete",
                "Explicit reviewer manual-check notes are required for exactly the incomplete checks",
            )
    elif manual:
        fail(422, "unexpected_manual_checks", "Manual coverage belongs only to an approval")
    row = Approval(
        campaign_id=campaign_id,
        review_id=review_id,
        request_id=request.id,
        reviewer_id=who.id,
        content_revision=campaign.content_revision,
        source_revision=campaign.source_revision,
        decision=payload.decision,
        reason=payload.reason,
        manual_checks=manual,
        decision_snapshot=decision_ids(session, review_id),
        coverage_mode="manual_supplement" if manual else "automated_checks_reviewed",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    session.refresh(campaign)
    return render_approval(session, campaign, row)

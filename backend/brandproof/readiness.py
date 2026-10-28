"""Read-only workflow guidance derived from actual approval prerequisites."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from brandproof.approval import current_decisions, latest_request, latest_run, readiness
from brandproof.auth import actor, db, lock_campaign, scoped_campaign
from brandproof.models import Actor
from brandproof.poster_models import PosterAsset
from brandproof.review_leases import recover_expired
from brandproof.source_models import Source, SourceVersion
from brandproof.workflow_models import Approval, RevisionAuthor


class RequiredAction(BaseModel):
    code: str
    message: str
    role: str
    target: str
    finding_id: str | None = None


class ReadinessOut(BaseModel):
    readiness: str
    content_revision: int
    source_revision: int
    actor_role: str
    blockers: list[RequiredAction]
    manual_checks: list[str]
    notice: str


def workflow_readiness(session, campaign, who):
    run = latest_run(session, campaign.id)
    receipt = readiness(session, campaign)
    result = {
        "readiness": receipt,
        "content_revision": campaign.content_revision,
        "source_revision": campaign.source_revision,
        "actor_role": who.role,
        "blockers": [],
        "manual_checks": [],
        "notice": "Guidance for this actor and current saved snapshot. Approval is always revalidated by the server. Typed local drafts are not included.",
    }
    actions = result["blockers"]

    def add(code, message, role, target, finding_id=None):
        actions.append(
            {
                "code": code,
                "message": message,
                "role": role,
                "target": target,
                "finding_id": finding_id,
            }
        )

    if receipt in {"approved", "approved_with_manual_checks"}:
        return result
    sources = session.execute(
        select(Source, SourceVersion)
        .join(
            SourceVersion,
            (Source.id == SourceVersion.source_id)
            & (Source.current_version == SourceVersion.version),
        )
        .where(Source.campaign_id == campaign.id)
    ).all()
    if not sources:
        add(
            "sources_missing",
            "Add and confirm applicable reference rules.",
            "owner",
            "sources-heading",
        )
    for _, version in sources:
        if version.status != "approved":
            add(
                "source_pending",
                f"Confirm pending source “{version.title}” v{version.version} after checking its evidence.",
                "owner",
                "sources-heading",
            )
        elif (version.valid_from and version.valid_from > campaign.publication_date) or (
            version.valid_until and version.valid_until < campaign.publication_date
        ):
            add(
                "source_inapplicable",
                f"Renew “{version.title}” for the publication date, then confirm and rerun.",
                "owner",
                "sources-heading",
            )
    has_poster = session.scalar(
        select(PosterAsset.id).where(PosterAsset.campaign_id == campaign.id).limit(1)
    )
    if not campaign.caption.strip() and not has_poster:
        add("content_missing", "Save a caption or upload a poster.", "creator", "content-heading")
    if not run:
        add(
            "review_missing",
            "Run a review to generate actual findings.",
            "creator",
            "content-heading",
        )
        return result
    if (
        run.content_revision != campaign.content_revision
        or run.source_revision != campaign.source_revision
    ):
        add(
            "review_stale",
            "Content or references changed. Run a new review before requesting approval.",
            "creator",
            "content-heading",
        )
        return result
    if run.status == "running":
        add(
            "review_running",
            "Review is running. Refresh after completion; expired worker leases recover automatically.",
            "creator",
            "results-heading",
        )
        return result
    if not run.sources_used or run.excluded_sources:
        add(
            "review_sources_incomplete",
            "The saved review has missing/excluded references. Resolve them and rerun.",
            "owner",
            "sources-heading",
        )
    decisions = current_decisions(session, run.id)
    for finding in run.findings:
        blocking = finding["severity"] == "error" or finding["evidence_status"] in {
            "needs_clarification",
            "insufficient_evidence",
        }
        decision = decisions.get(finding["id"])
        if blocking and (not decision or decision.decision == "reopen"):
            add(
                "finding_unresolved",
                f"{finding['category']}: edit the asset and rerun, or record an explicit dismissal/exception with a real reason.",
                "reviewer",
                "results-heading",
                finding["id"],
            )
    request = latest_request(session, campaign.id)
    decided = bool(
        request and session.scalar(select(Approval.id).where(Approval.request_id == request.id))
    )
    if not request or request.review_id != run.id or decided:
        add(
            "request_required",
            "Creator: request a fresh human review for this run.",
            "creator",
            "human-review-heading",
        )
    authors = set(
        session.scalars(
            select(RevisionAuthor.actor_id).where(RevisionAuthor.campaign_id == campaign.id)
        )
    )
    if not authors:
        add(
            "unknown_content_author",
            "Save a traceable content revision before requesting approval.",
            "creator",
            "content-heading",
        )
    if who.role not in {"owner", "reviewer"}:
        add(
            "approver_role",
            "Use the Reviewer action panel for approval. Creator cannot approve.",
            "reviewer",
            "human-review-heading",
        )
    elif who.id in authors or (request and request.requested_by == who.id):
        add(
            "self_approval",
            "Choose an authorized actor who neither edited content nor requested this review. Switching requester cannot bypass edit history.",
            "reviewer",
            "human-review-heading",
        )
    required = (
        ["exact_text", "contextual"]
        + (["claim_risk"] if "claim_risk" in run.checks else [])
        + (["poster"] if run.checks.get("poster", {}).get("details", {}).get("asset_id") else [])
    )
    result["manual_checks"] = [
        name for name in required if run.checks.get(name, {}).get("status") != "completed"
    ]
    return result


router = APIRouter(prefix="/api/v1/campaigns/{campaign_id}", tags=["workflow guidance"])


@router.get("/readiness", response_model=ReadinessOut)
def get_readiness(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    campaign = scoped_campaign(session, campaign_id, who)
    lock_campaign(session, campaign)
    if recover_expired(session, campaign_id):
        session.commit()
        lock_campaign(session, campaign)
    return workflow_readiness(session, campaign, who)

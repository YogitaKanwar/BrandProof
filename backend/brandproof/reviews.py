from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from brandproof.auth import actor, db, lock_campaign, require_role, scoped_campaign
from brandproof.contextual import ContextualConfig, ContextualResult, analyze_context
from brandproof.errors import fail
from brandproof.finding_groups import finding_groups
from brandproof.models import Actor, Campaign
from brandproof.poster_review import review_poster
from brandproof.quota import reserve_provider_call
from brandproof.review_models import ContentVersion, ReviewRun
from brandproof.review_schemas import CaptionUpdate, ReviewOut, ReviewStart
from brandproof.rules import exact_checks
from brandproof.schemas import CampaignOut
from brandproof.source_models import Source, SourceVersion
from brandproof.sources import render_source
from brandproof.workflow_models import RevisionAuthor

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
    session.add(
        RevisionAuthor(
            campaign_id=campaign_id, content_revision=payload.expected_revision + 1, actor_id=who.id
        )
    )
    session.commit()
    session.refresh(campaign)
    return campaign


def render_run(run: ReviewRun, campaign: Campaign, session=None):
    from brandproof.approval import readiness

    return {
        "id": run.id,
        "campaign_id": run.campaign_id,
        "content_revision": run.content_revision,
        "source_revision": run.source_revision,
        "caption": run.caption,
        "status": run.status,
        "is_current": run.content_revision == campaign.content_revision
        and run.source_revision == campaign.source_revision,
        "readiness": readiness(session, campaign, run.id) if session else "not_approved",
        "checks": run.checks,
        "sources_used": run.sources_used,
        "excluded_sources": run.excluded_sources,
        "findings": run.findings,
        "finding_groups": finding_groups(run.findings),
        "created_at": run.created_at,
    }


@router.post("/reviews", status_code=201, response_model=ReviewOut)
def start_review(
    campaign_id: str,
    payload: ReviewStart,
    request: Request,
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
    # OCR and deterministic checks belong to the same locked content/source snapshot.
    poster_findings, poster_check = review_poster(session, campaign, active, excluded)
    has_poster = bool(poster_check.get("details", {}).get("asset_id"))
    has_caption = bool(campaign.caption.strip())
    if not has_caption and not has_poster:
        fail(422, "empty_caption", "Save a caption or attach a poster before reviewing")
    findings, coverage = (
        exact_checks(campaign.caption, campaign.content_revision, active)
        if has_caption
        else ([], [])
    )
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
        status="running",
        checks={
            "exact_text": {
                "status": exact_status,
                "reason": "No caption provided."
                if not has_caption
                else None
                if exact_status == "completed"
                else "Some rules lack comparable supported expressions, or require source/scope clarification or renewal.",
                "rules": coverage,
            },
            "contextual": {
                "status": "not_assessed",
                "reason": "Contextual review is in progress.",
            },
            "poster": poster_check,
        },
        sources_used=sources,
        excluded_sources=excluded,
        findings=[*findings, *poster_findings],
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
    caption_snapshot = campaign.caption
    settings = request.app.state.settings
    session.add(run)
    configured_external = (
        settings.external_ai_enabled
        and payload.external_ai_consent
        and settings.ai_provider != "none"
        and settings.ai_model.strip()
        and settings.ai_api_key.get_secret_value().strip()
        and has_caption
    )
    if configured_external:
        session.flush()  # Reserve against an existing run ID only for provider admission.
    quota_reason = (
        reserve_provider_call(session, campaign.workspace_id, run.id, settings)
        if configured_external
        else None
    )
    session.commit()

    # Do not read ORM attributes here: with expire_on_commit=True even a read
    # would reopen a database transaction across the external provider call.
    settings = request.app.state.settings
    result = (
        ContextualResult("unavailable", quota_reason, metadata={"admission": "denied"})
        if quota_reason
        else analyze_context(
            caption_snapshot,
            payload.expected_content_revision,
            active,
            ContextualConfig(
                provider=settings.ai_provider,
                model=settings.ai_model,
                api_key=settings.ai_api_key.get_secret_value(),
                allow_external=settings.external_ai_enabled and payload.external_ai_consent,
            ),
            transport=getattr(request.app.state, "contextual_transport", None),
        )
    )
    excluded_policy_ids = sorted(
        source["source_id"] for source in excluded if source["kind"] in {"tone", "claim_policy"}
    )
    if excluded_policy_ids:
        result.metadata = {
            **result.metadata,
            "excluded_policy_source_ids": excluded_policy_ids,
        }
        no_contextual_sources = (
            result.status == "unavailable"
            and "approved_source_count" in result.metadata
            and not result.metadata["selected_source_count"]
        )
        if result.status == "completed" or no_contextual_sources:
            result.status = "partial"
            result.reason = "Some contextual policies are unapproved or not valid for publication."
    lock_campaign(session, campaign)
    run.checks = {
        **run.checks,
        "contextual": {
            "status": result.status,
            "reason": result.reason,
            "details": result.metadata,
        },
    }
    run.findings = [*run.findings, *result.findings]
    run.status = (
        "completed"
        if exact_status == "completed" and result.status == "completed" and not has_poster
        else "partial"
    )
    session.commit()
    # Observe actual current state, rather than the pre-commit identity-map cache.
    session.refresh(campaign)
    return render_run(run, campaign, session)


@router.get("/reviews", response_model=list[ReviewOut])
def list_reviews(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    campaign = scoped_campaign(session, campaign_id, who)
    return [
        render_run(run, campaign, session)
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
    return render_run(run, campaign, session)

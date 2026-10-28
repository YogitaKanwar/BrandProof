"""Bounded workspace observations, not truth/accuracy or automatic guideline verdicts."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from brandproof.auth import actor, db
from brandproof.models import Actor, Campaign
from brandproof.removal_models import active_campaigns
from brandproof.review_models import ReviewRun
from brandproof.workflow_models import FindingDecision

MAX_RUNS = 500
MAX_DECISIONS = 5000
MIN_REVIEWED = 5


class InsightEvidence(BaseModel):
    campaign_id: str
    campaign_name: str
    review_id: str
    finding_id: str
    content_revision: int
    source_version_id: str | None
    source_id: str | None
    source_version: int | None
    quote: str | None
    message: str
    evidence_status: str
    decision: str | None
    reason: str | None


class GuidelineInsight(BaseModel):
    category: str
    source_id: str | None
    source_version_id: str | None
    source_version: int | None
    observations: int
    reviewed: int
    dismissed: int
    exceptions: int
    reopened: int
    decision_rate: float | None
    potentially_ambiguous: bool
    sample_status: str
    evidence: list[InsightEvidence]
    evidence_truncated: bool


class CategoryInsight(BaseModel):
    category: str
    observations: int
    campaigns: int


class InsightsOut(BaseModel):
    categories: list[CategoryInsight]
    guidelines: list[GuidelineInsight]
    runs_considered: int
    snapshots_considered: int
    truncated: bool
    minimum_reviewed_sample: int
    notice: str


def summarize(session, workspace_id):
    rows = session.execute(
        select(ReviewRun, Campaign)
        .join(Campaign, Campaign.id == ReviewRun.campaign_id)
        .where(
            Campaign.workspace_id == workspace_id, ReviewRun.status != "running", active_campaigns()
        )
        .order_by(ReviewRun.created_at.desc(), ReviewRun.id.desc())
        .limit(MAX_RUNS + 1)
    ).all()
    truncated = len(rows) > MAX_RUNS
    rows = rows[:MAX_RUNS]
    snapshots = {}
    for run, campaign in rows:
        snapshots.setdefault(
            (run.campaign_id, run.content_revision, run.source_revision), (run, campaign)
        )
    run_ids = [run.id for run, _ in snapshots.values()]
    decisions = (
        session.scalars(
            select(FindingDecision)
            .where(FindingDecision.review_id.in_(run_ids))
            .order_by(
                FindingDecision.created_at.desc(),
                FindingDecision.version.desc(),
                FindingDecision.id.desc(),
            )
            .limit(MAX_DECISIONS + 1)
        ).all()
        if run_ids
        else []
    )
    truncated = truncated or len(decisions) > MAX_DECISIONS
    latest = {}
    for row in decisions[:MAX_DECISIONS]:
        key = (row.review_id, row.finding_id)
        previous = latest.get(key)
        if not previous or row.version > previous.version:
            latest[key] = row
    groups = {}
    categories = {}
    for run, campaign in snapshots.values():
        for finding in run.findings:
            category = finding["category"]
            count = categories.setdefault(category, {"observations": 0, "campaigns": set()})
            count["observations"] += 1
            count["campaigns"].add(campaign.id)
            evidence = finding.get("evidence") or {}
            key = (category, evidence.get("source_version_id"))
            group = groups.setdefault(
                key,
                {
                    "category": category,
                    "source_id": evidence.get("source_id"),
                    "source_version_id": evidence.get("source_version_id"),
                    "source_version": evidence.get("source_version"),
                    "observations": 0,
                    "reviewed": 0,
                    "dismissed": 0,
                    "exceptions": 0,
                    "reopened": 0,
                    "evidence": [],
                    "content_revisions": set(),
                },
            )
            group["observations"] += 1
            decision = latest.get((run.id, finding["id"]))
            if decision:
                group["reviewed"] += 1
                field = {"dismiss": "dismissed", "exception": "exceptions", "reopen": "reopened"}[
                    decision.decision
                ]
                group[field] += 1
                group["content_revisions"].add((campaign.id, run.content_revision))
            if len(group["evidence"]) < 50:
                group["evidence"].append(
                    {
                        "campaign_id": campaign.id,
                        "campaign_name": campaign.name,
                        "review_id": run.id,
                        "finding_id": finding["id"],
                        "content_revision": run.content_revision,
                        "source_id": evidence.get("source_id"),
                        "source_version_id": evidence.get("source_version_id"),
                        "source_version": evidence.get("source_version"),
                        "quote": finding["location"].get("quote"),
                        "message": finding["message"],
                        "evidence_status": finding["evidence_status"],
                        "decision": decision.decision if decision else None,
                        "reason": decision.reason if decision else None,
                    }
                )
    output = []
    for group in groups.values():
        sufficient = (
            group["reviewed"] >= MIN_REVIEWED
            and len(group.pop("content_revisions")) >= MIN_REVIEWED
        )
        rate = (
            (group["dismissed"] + group["exceptions"]) / group["reviewed"]
            if group["reviewed"]
            else None
        )
        group.update(
            decision_rate=rate if sufficient else None,
            potentially_ambiguous=bool(sufficient and group["source_version_id"] and rate > 0.5),
            sample_status="sufficient_for_triage_only"
            if sufficient
            else "insufficient_reviewed_revisions",
            evidence_truncated=group["observations"] > len(group["evidence"]),
        )
        output.append(group)
    output.sort(
        key=lambda row: (
            not row["potentially_ambiguous"],
            -row["observations"],
            row["category"],
            row["source_version_id"] or "",
        )
    )
    return {
        "categories": [
            {
                "category": name,
                "observations": row["observations"],
                "campaigns": len(row["campaigns"]),
            }
            for name, row in sorted(categories.items())
        ],
        "guidelines": output,
        "runs_considered": len(rows),
        "snapshots_considered": len(snapshots),
        "truncated": truncated,
        "minimum_reviewed_sample": MIN_REVIEWED,
        "notice": "Finding observations are not confirmed truth violations or measured accuracy. Only the latest completed/partial run per content/source snapshot is counted. Rates use latest explicit dispositions, including reopen, and require five reviewed content revisions. A high dismissal/exception rate is an owner triage hint, not proof a rule is ambiguous. Demo roles are synthetic, not independent real reviewers. At most 500 runs/5000 decisions are summarized; inspect links and reasons.",
    }


router = APIRouter(prefix="/api/v1", tags=["governance"])


@router.get("/governance-insights", response_model=InsightsOut)
def governance_insights(who: Actor = Depends(actor), session: Session = Depends(db)):
    return summarize(session, who.workspace_id)

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from brandproof.auth import actor, db, lock_campaign, require_role, scoped_campaign
from brandproof.document_models import DocumentEvidence, evidence_for
from brandproof.errors import fail
from brandproof.models import Actor, Campaign
from brandproof.schemas import MAX_DB_INTEGER
from brandproof.source_models import Source, SourceVersion
from brandproof.source_schemas import (
    SourceCreate,
    SourceOut,
    SourceUpdate,
    VersionRequest,
)

router = APIRouter(prefix="/api/v1/campaigns/{campaign_id}/sources", tags=["sources"])


def canonical_text(rule: dict) -> str:
    match rule["kind"]:
        case "price":
            amount = format(Decimal(rule["amount"]), "f")
            return f"The approved campaign price is {rule['currency']} {amount}."
        case "date":
            return f"The approved campaign date is {rule['date']}."
        case "terminology":
            return f"Use '{rule['preferred']}' instead of '{rule['term']}'."
        case "required_text":
            return f"Campaign copy must include: {rule['text']}"
        case "brand_color":
            return f"Permitted flat poster background: {rule['hex']} within CIE76 Delta-E {rule['tolerance']}."
        case "contrast":
            return f"Supported poster text/background samples require contrast of at least {rule['minimum_ratio']}:1."
        case "alt_text":
            return "Provide a poster description including the key price/date information. Human assessment of meaning is required."
        case _:
            return rule["guidance"]


def render_source(source: Source, version: SourceVersion, session=None) -> dict:
    return {
        "id": source.id,
        "version_id": version.id,
        "version": version.version,
        "title": version.title,
        "status": version.status,
        "rule": version.rule,
        "text": version.text,
        "valid_from": version.valid_from,
        "valid_until": version.valid_until,
        "confirmed_by": version.confirmed_by,
        "created_at": version.created_at,
        "document_evidence": evidence_for(session, version.id) if session is not None else None,
    }


def get_source(session: Session, campaign_id: str, source_id: str) -> Source:
    source = session.scalar(
        select(Source).where(Source.id == source_id, Source.campaign_id == campaign_id)
    )
    if not source:
        fail(404, "not_found", "Source not found")
    return source


def current(session: Session, source: Source) -> SourceVersion:
    return session.scalar(
        select(SourceVersion).where(
            SourceVersion.source_id == source.id,
            SourceVersion.version == source.current_version,
        )
    )


def bump_source_snapshot(session: Session, campaign_id: str):
    changed = session.execute(
        update(Campaign)
        .where(Campaign.id == campaign_id, Campaign.source_revision < MAX_DB_INTEGER)
        .values(source_revision=Campaign.source_revision + 1)
    )
    if changed.rowcount != 1:
        fail(409, "version_exhausted", "Source snapshot revision limit reached")


def advance(session: Session, source: Source, expected: int):
    result = session.execute(
        update(Source)
        .where(Source.id == source.id, Source.current_version == expected)
        .values(current_version=expected + 1),
        execution_options={"synchronize_session": False},
    )
    if result.rowcount != 1:
        fail(409, "version_conflict", "Source changed; reload before continuing")
    session.refresh(source)


@router.post("", status_code=201, response_model=SourceOut)
def create_source(
    campaign_id: str,
    payload: SourceCreate,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "owner")
    lock_campaign(session, campaign)
    source = Source(campaign_id=campaign_id)
    session.add(source)
    session.flush()
    rule = payload.rule.model_dump(mode="json")
    version = SourceVersion(
        source_id=source.id,
        version=1,
        title=payload.title,
        status="pending",
        rule=rule,
        text=canonical_text(rule),
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
    )
    session.add(version)
    bump_source_snapshot(session, campaign_id)
    session.commit()
    return render_source(source, version, session)


@router.get("", response_model=list[SourceOut])
def list_sources(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    scoped_campaign(session, campaign_id, who)
    rows = session.execute(
        select(Source, SourceVersion)
        .join(
            SourceVersion,
            (Source.id == SourceVersion.source_id)
            & (Source.current_version == SourceVersion.version),
        )
        .where(Source.campaign_id == campaign_id)
        .order_by(Source.id)
    ).all()
    return [render_source(source, version, session) for source, version in rows]


@router.get("/{source_id}/versions", response_model=list[SourceOut])
def versions(
    campaign_id: str,
    source_id: str,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    scoped_campaign(session, campaign_id, who)
    source = get_source(session, campaign_id, source_id)
    return [
        render_source(source, version, session)
        for version in session.scalars(
            select(SourceVersion)
            .where(SourceVersion.source_id == source.id)
            .order_by(SourceVersion.version)
        )
    ]


@router.put("/{source_id}", response_model=SourceOut)
def revise(
    campaign_id: str,
    source_id: str,
    payload: SourceUpdate,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "owner")
    lock_campaign(session, campaign)
    source = get_source(session, campaign_id, source_id)
    advance(session, source, payload.expected_version)
    rule = payload.rule.model_dump(mode="json")
    version = SourceVersion(
        source_id=source.id,
        version=source.current_version,
        title=payload.title,
        status="pending",
        rule=rule,
        text=canonical_text(rule),
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
    )
    session.add(version)
    bump_source_snapshot(session, campaign_id)
    session.commit()
    return render_source(source, version, session)


@router.post("/{source_id}/confirm", response_model=SourceOut)
def confirm(
    campaign_id: str,
    source_id: str,
    payload: VersionRequest,
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    campaign = scoped_campaign(session, campaign_id, who)
    require_role(who, "owner")
    lock_campaign(session, campaign)
    source = get_source(session, campaign_id, source_id)
    previous = current(session, source)
    if source.current_version != payload.expected_version:
        fail(409, "version_conflict", "Source changed; reload before confirming")
    if previous.status != "pending":
        fail(409, "already_confirmed", "Only pending sources can be confirmed")
    advance(session, source, payload.expected_version)
    version = SourceVersion(
        source_id=source.id,
        version=source.current_version,
        title=previous.title,
        status="approved",
        rule=previous.rule,
        text=previous.text,
        valid_from=previous.valid_from,
        valid_until=previous.valid_until,
        confirmed_by=who.id,
    )
    session.add(version)
    session.flush()
    inherited = session.get(DocumentEvidence, previous.id)
    if inherited:
        session.add(
            DocumentEvidence(
                source_version_id=version.id,
                document_id=inherited.document_id,
                page_number=inherited.page_number,
                start=inherited.start,
                end=inherited.end,
                quote=inherited.quote,
            )
        )
    bump_source_snapshot(session, campaign_id)
    session.commit()
    return render_source(source, version, session)

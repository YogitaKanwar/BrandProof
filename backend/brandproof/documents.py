import hashlib
import json
import re
import subprocess
import sys
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from brandproof.auth import actor, db, lock_campaign, require_role, scoped_campaign
from brandproof.document_models import DocumentEvidence, GuidelineDocument
from brandproof.errors import fail
from brandproof.models import Actor
from brandproof.pdf_extract import MAX_BYTES
from brandproof.schemas import MAX_INCREMENT_EXPECTATION
from brandproof.source_models import Source, SourceVersion
from brandproof.source_schemas import SourceCreate, SourceOut
from brandproof.sources import bump_source_snapshot, canonical_text, render_source
from brandproof.timestamps import UTCDateTime

router = APIRouter(
    prefix="/api/v1/campaigns/{campaign_id}/guideline-documents", tags=["guideline documents"]
)


class DocumentPage(BaseModel):
    page_number: int
    text: str
    status: str
    reason: str | None


class DocumentOut(BaseModel):
    id: str
    filename: str
    sha256: str
    created_at: UTCDateTime
    status: str
    pages: list[DocumentPage]
    scope: str
    candidate_limit_reached: bool
    candidate_count: int


class ImportOut(BaseModel):
    document: DocumentOut
    sources: list[SourceOut]
    notice: str


def candidates(extraction):
    found = []
    for page in extraction["pages"]:
        for match in re.finditer(r"[^\r\n]+", page["text"]):
            quote = match.group()
            line = quote.strip()
            rule = None
            if item := re.fullmatch(
                r"(?:Campaign )?price:\s*(INR|USD|EUR|GBP)\s+(\d{1,8}(?:\.\d{1,2})?)\.?", line, re.I
            ):
                rule = {"kind": "price", "currency": item[1].upper(), "amount": item[2]}
            elif item := re.fullmatch(r"(?:Campaign )?date:\s*(\d{4}-\d{2}-\d{2})\.?", line, re.I):
                rule = {"kind": "date", "date": item[1]}
            elif item := re.fullmatch(r"Background colou?r:\s*(#[0-9a-f]{6})", line, re.I):
                rule = {"kind": "brand_color", "hex": item[1]}
            elif item := re.fullmatch(r"Minimum contrast:\s*(\d+(?:\.\d+)?)", line, re.I):
                rule = {"kind": "contrast", "minimum_ratio": float(item[1])}
            elif re.fullmatch(r"Alt text:\s*required", line, re.I):
                rule = {"kind": "alt_text"}
            elif item := re.fullmatch(
                r'Use "([^"\n]{1,100})" instead of "([^"\n]{1,100})"\.?', line, re.I
            ):
                rule = {"kind": "terminology", "term": item[2], "preferred": item[1]}
            elif item := re.fullmatch(r"(Required text|Tone|Claim policy):\s*(.+)", line, re.I):
                kind = {
                    "required text": "required_text",
                    "tone": "tone",
                    "claim policy": "claim_policy",
                }[item[1].lower()]
                rule = {"kind": kind, "text" if kind == "required_text" else "guidance": item[2]}
            if rule:
                try:
                    payload = SourceCreate(
                        title=f"PDF page {page['page_number']}: {rule['kind']}", rule=rule
                    )
                except ValidationError:
                    continue
                found.append(
                    {
                        "payload": payload,
                        "page_number": page["page_number"],
                        "start": match.start(),
                        "end": match.end(),
                        "quote": quote,
                    }
                )
            if len(found) >= 20:
                return found, True
    return found, False


def extract_isolated(raw):
    try:
        process = subprocess.run(
            [sys.executable, "-m", "brandproof.pdf_extract"],
            input=raw,
            capture_output=True,
            timeout=15,
            check=False,
        )
        if process.returncode or len(process.stdout) > 1024 * 1024:
            raise ValueError("Extraction unavailable")
        result = json.loads(process.stdout)
        if "pages" not in result:
            raise ValueError("No extraction")
        return result
    except (subprocess.TimeoutExpired, ValueError, OSError):
        fail(
            422,
            "pdf_unavailable",
            "PDF is invalid, encrypted, unsupported or exceeded extraction limits. No rules imported.",
        )


def render_document(document):
    return {
        "id": document.id,
        "filename": document.filename,
        "sha256": document.sha256,
        "created_at": document.created_at.isoformat(),
        **document.extraction,
    }


@router.post("", status_code=201, response_model=ImportOut)
async def import_document(
    campaign_id: str,
    request: Request,
    expected_source_revision: int = Query(ge=0, le=MAX_INCREMENT_EXPECTATION),
    who: Actor = Depends(actor),
    session: Session = Depends(db),
):
    scoped_campaign(session, campaign_id, who)
    require_role(who, "owner")
    if request.headers.get("content-type", "").split(";")[0].lower() != "application/pdf":
        fail(415, "unsupported_media_type", "Choose a PDF document")
    filename = unquote(request.headers.get("x-brandproof-filename", "guidelines.pdf"))
    if (
        not 1 <= len(filename) <= 160
        or any(ord(c) < 32 for c in filename)
        or "/" in filename
        or "\\" in filename
    ):
        fail(422, "invalid_filename", "Use a short document name without a path")
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > MAX_BYTES:
            fail(413, "file_too_large", "PDF limit is 5 MiB")
    extraction = await run_in_threadpool(extract_isolated, bytes(raw))
    selected, limited = candidates(extraction)
    campaign = scoped_campaign(session, campaign_id, who)
    lock_campaign(session, campaign)
    if campaign.source_revision != expected_source_revision:
        fail(409, "version_conflict", "Sources changed during extraction; reload before importing")
    extraction = {
        **extraction,
        "candidate_limit_reached": limited,
        "candidate_count": len(selected),
    }
    document = GuidelineDocument(
        campaign_id=campaign_id,
        filename=filename,
        sha256=hashlib.sha256(raw).hexdigest(),
        extraction=extraction,
    )
    session.add(document)
    session.flush()
    sources = []
    for candidate in selected:
        page = extraction["pages"][candidate["page_number"] - 1]["text"]
        if page[candidate["start"] : candidate["end"]] != candidate["quote"]:
            fail(422, "invalid_page_quote", "Candidate quotation could not be verified")
        source = Source(campaign_id=campaign_id)
        session.add(source)
        session.flush()
        payload = candidate["payload"]
        rule = payload.rule.model_dump(mode="json")
        version = SourceVersion(
            source_id=source.id,
            version=1,
            title=payload.title,
            status="pending",
            rule=rule,
            text=canonical_text(rule),
        )
        session.add(version)
        session.flush()
        session.add(
            DocumentEvidence(
                source_version_id=version.id,
                document_id=document.id,
                **{k: candidate[k] for k in ["page_number", "start", "end", "quote"]},
            )
        )
        sources.append((source, version))
    if sources:
        bump_source_snapshot(session, campaign_id)
    session.commit()
    return {
        "document": render_document(document),
        "sources": [render_source(s, v, session) for s, v in sources],
        "notice": "Candidate rules are pending. Owner confirmation establishes provenance, not content approval or completeness of PDF interpretation.",
    }


@router.get("", response_model=list[DocumentOut])
def list_documents(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    scoped_campaign(session, campaign_id, who)
    return [
        render_document(row)
        for row in session.scalars(
            select(GuidelineDocument)
            .where(GuidelineDocument.campaign_id == campaign_id)
            .order_by(GuidelineDocument.created_at)
        )
    ]

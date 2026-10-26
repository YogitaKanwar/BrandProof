from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from brandproof.schemas import MAX_DB_INTEGER, MAX_INCREMENT_EXPECTATION, StrictModel


class CaptionUpdate(StrictModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    expected_revision: int = Field(ge=1, le=MAX_INCREMENT_EXPECTATION)
    text: str = Field(min_length=1, max_length=20000)


class ReviewCreate(StrictModel):
    expected_content_revision: int = Field(ge=1, le=MAX_DB_INTEGER)
    expected_source_revision: int = Field(ge=0, le=MAX_DB_INTEGER)


class Location(BaseModel):
    asset: Literal["caption"] = "caption"
    content_revision: int
    start: int | None = None
    end: int | None = None
    quote: str | None = None


class Evidence(BaseModel):
    source_id: str
    source_version_id: str
    source_version: int
    quote: str


class Finding(BaseModel):
    id: str
    category: str
    severity: Literal["error", "warning", "info"]
    evidence_status: Literal["contradicted", "needs_clarification", "insufficient_evidence"]
    message: str
    location: Location
    evidence: Evidence | None
    suggested_replacement: str | None = None


class RuleCoverage(BaseModel):
    source_id: str
    source_version: int
    kind: str
    status: Literal["completed", "partial", "not_assessed"]
    reason: str | None = None


class CheckStatus(BaseModel):
    status: Literal["completed", "partial", "unavailable", "not_assessed"]
    reason: str | None = None
    rules: list[RuleCoverage] = Field(default_factory=list)


class ReviewOut(BaseModel):
    id: str
    campaign_id: str
    content_revision: int
    source_revision: int
    caption: str
    status: Literal["partial", "completed", "failed"]
    is_current: bool
    readiness: Literal["not_approved"] = "not_approved"
    checks: dict[str, CheckStatus]
    sources_used: list[dict]
    excluded_sources: list[dict]
    findings: list[Finding]
    created_at: datetime

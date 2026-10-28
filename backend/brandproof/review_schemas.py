from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_serializer

from brandproof.schemas import MAX_DB_INTEGER, MAX_INCREMENT_EXPECTATION, StrictModel


class CaptionRevision(StrictModel):
    expected_revision: int = Field(ge=1, le=MAX_INCREMENT_EXPECTATION)


class CaptionUpdate(CaptionRevision):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    text: str = Field(min_length=1, max_length=20000)


class ReviewCreate(StrictModel):
    expected_content_revision: int = Field(ge=1, le=MAX_DB_INTEGER)
    expected_source_revision: int = Field(ge=0, le=MAX_DB_INTEGER)


class ReviewStart(ReviewCreate):
    external_ai_consent: StrictBool = False


class Box(BaseModel):
    x: float
    y: float
    width: float
    height: float


class Location(BaseModel):
    asset: Literal["caption", "poster"] = "caption"
    content_revision: int
    poster_id: str | None = None
    boxes: list[Box] = Field(default_factory=list)
    ocr_confidence: float | None = None
    start: int | None = None
    end: int | None = None
    quote: str | None = None

    @model_serializer(mode="wrap")
    def serialize_location(self, handler):
        result = handler(self)
        # Preserve the existing standalone caption-finding serialization contract.
        if self.asset == "caption":
            for field in ("poster_id", "boxes", "ocr_confidence"):
                result.pop(field, None)
        return result


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
    details: dict = Field(default_factory=dict)


class FindingGroup(BaseModel):
    category: str
    source_id: str | None
    source_version: int | None
    finding_ids: list[str]
    assets: list[Literal["caption", "poster"]]


class ReviewOut(BaseModel):
    id: str
    campaign_id: str
    content_revision: int
    source_revision: int
    caption: str
    status: Literal["running", "partial", "completed", "failed"]
    is_current: bool
    readiness: Literal[
        "not_approved", "approved", "approved_with_manual_checks", "changes_requested", "stale"
    ] = "not_approved"
    checks: dict[str, CheckStatus]
    sources_used: list[dict]
    excluded_sources: list[dict]
    findings: list[Finding]
    finding_groups: list[FindingGroup] = Field(default_factory=list)
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

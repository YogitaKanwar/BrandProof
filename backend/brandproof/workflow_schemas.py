from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from brandproof.review_schemas import ReviewCreate
from brandproof.schemas import MAX_INCREMENT_EXPECTATION
from brandproof.timestamps import UTCDateTime


class ApprovalCreate(ReviewCreate):
    request_id: str = Field(min_length=36, max_length=36)
    decision: Literal["approve", "request_changes"]
    reason: str = Field(min_length=10, max_length=2000)
    manual_checks: dict[
        Literal["exact_text", "contextual", "poster", "claim_risk"],
        Annotated[str, Field(min_length=20, max_length=2000)],
    ] = Field(default_factory=dict)


class ApprovalOut(BaseModel):
    id: str
    campaign_id: str
    review_id: str
    request_id: str
    reviewer_id: str
    content_revision: int
    source_revision: int
    decision: str
    reason: str
    coverage_mode: str
    manual_checks: dict[str, str]
    decision_snapshot: dict[str, str]
    created_at: UTCDateTime
    is_current: bool


class ReviewRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    campaign_id: str
    review_id: str
    requested_by: str
    created_at: UTCDateTime


class FindingDecisionCreate(ReviewCreate):
    expected_decision_version: int = Field(ge=0, le=MAX_INCREMENT_EXPECTATION)
    decision: Literal["dismiss", "exception", "reopen"]
    reason: str = Field(min_length=10, max_length=2000)


class FindingDecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    review_id: str
    finding_id: str
    version: int
    actor_id: str
    decision: str
    reason: str
    created_at: UTCDateTime


class CommentCreate(ReviewCreate):
    review_id: str | None = Field(default=None, max_length=36)
    text: str = Field(min_length=1, max_length=3000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    campaign_id: str
    review_id: str | None
    actor_id: str
    actor_role: str
    content_revision: int
    source_revision: int
    text: str
    created_at: UTCDateTime


class RevisionOut(BaseModel):
    revision: int
    caption: str
    created_at: UTCDateTime

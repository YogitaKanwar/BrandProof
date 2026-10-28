from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from brandproof.schemas import MAX_INCREMENT_EXPECTATION, StrictModel
from brandproof.timestamps import UTCDateTime


class PriceRule(StrictModel):
    kind: Literal["price"]
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: Literal["INR", "USD", "EUR", "GBP"]
    scope: Literal["campaign_main_price"] = "campaign_main_price"


class DateRule(StrictModel):
    kind: Literal["date"]
    date: date
    scope: Literal["campaign_main_date"] = "campaign_main_date"


class TerminologyRule(StrictModel):
    kind: Literal["terminology"]
    term: str = Field(min_length=1, max_length=100)
    preferred: str = Field(min_length=1, max_length=100)


class RequiredRule(StrictModel):
    kind: Literal["required_text"]
    text: str = Field(min_length=1, max_length=500)


class ToneRule(StrictModel):
    kind: Literal["tone", "claim_policy"]
    guidance: str = Field(min_length=1, max_length=5000)


Rule = Annotated[
    PriceRule | DateRule | TerminologyRule | RequiredRule | ToneRule,
    Field(discriminator="kind"),
]


class SourceCreate(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    rule: Rule
    valid_from: date | None = None
    valid_until: date | None = None

    @model_validator(mode="after")
    def valid_range(self):
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            raise ValueError("valid_from must not be after valid_until")
        return self


class SourceUpdate(SourceCreate):
    expected_version: int = Field(ge=1, le=MAX_INCREMENT_EXPECTATION)


class VersionRequest(StrictModel):
    expected_version: int = Field(ge=1, le=MAX_INCREMENT_EXPECTATION)


class DocumentCitation(BaseModel):
    document_id: str
    filename: str
    sha256: str
    page_number: int
    start: int
    end: int
    quote: str


class SourceOut(BaseModel):
    id: str
    version_id: str
    version: int
    title: str
    status: Literal["pending", "approved"]
    rule: Rule
    text: str
    valid_from: date | None
    valid_until: date | None
    confirmed_by: str | None
    created_at: UTCDateTime
    document_evidence: DocumentCitation | None = None

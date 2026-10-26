from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OCRWord(BaseModel):
    text: str
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    confidence: float = Field(ge=0, le=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)


class OCRExtraction(BaseModel):
    engine: Literal["tesseract"]
    status: Literal["completed", "partial", "unavailable"]
    reason: str | None
    text: str
    words: list[OCRWord]


class PosterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    campaign_id: str
    content_revision: int
    mime: Literal["image/png"]
    sha256: str
    width: int
    height: int
    ocr: OCRExtraction
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

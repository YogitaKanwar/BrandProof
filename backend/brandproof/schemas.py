from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# SQLAlchemy Integer is signed 32-bit on PostgreSQL; reserve room for mutations.
MAX_DB_INTEGER = 2**31 - 1
MAX_INCREMENT_EXPECTATION = MAX_DB_INTEGER - 1


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CampaignCreate(StrictModel):
    name: str = Field(min_length=1, max_length=160)
    publication_date: date


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    workspace_id: str
    name: str
    publication_date: date
    caption: str
    content_revision: int
    source_revision: int
    created_at: datetime


class DemoActor(BaseModel):
    role: Literal["owner", "creator", "reviewer"]
    access_token: str


class DemoSessionOut(BaseModel):
    workspace_id: str
    mode: Literal["synthetic_demo"]
    notice: str
    expires_at: datetime
    actors: dict[str, DemoActor]

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from brandproof.db import Base
from brandproof.models import new_id, utcnow


class ContentVersion(Base):
    __tablename__ = "content_versions"
    __table_args__ = (UniqueConstraint("campaign_id", "revision"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    revision: Mapped[int] = mapped_column()
    caption: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReviewRun(Base):
    __tablename__ = "review_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    content_revision: Mapped[int] = mapped_column()
    source_revision: Mapped[int] = mapped_column()
    caption: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    checks: Mapped[dict] = mapped_column(JSON)
    sources_used: Mapped[list] = mapped_column(JSON)
    excluded_sources: Mapped[list] = mapped_column(JSON)
    findings: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

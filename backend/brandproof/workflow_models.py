from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from brandproof.db import Base
from brandproof.models import new_id, utcnow


class RevisionAuthor(Base):
    __tablename__ = "revision_authors"
    __table_args__ = (UniqueConstraint("campaign_id", "content_revision"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    content_revision: Mapped[int] = mapped_column()
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))


class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (UniqueConstraint("request_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("review_runs.id"), index=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("review_requests.id"))
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    content_revision: Mapped[int] = mapped_column()
    source_revision: Mapped[int] = mapped_column()
    decision: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text)
    coverage_mode: Mapped[str] = mapped_column(String(30))
    manual_checks: Mapped[dict] = mapped_column(JSON)
    decision_snapshot: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReviewRequest(Base):
    __tablename__ = "review_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("review_runs.id"), index=True)
    requested_by: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FindingDecision(Base):
    __tablename__ = "finding_decisions"
    __table_args__ = (UniqueConstraint("review_id", "finding_id", "version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    review_id: Mapped[str] = mapped_column(ForeignKey("review_runs.id"), index=True)
    finding_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column()
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    decision: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    review_id: Mapped[str | None] = mapped_column(ForeignKey("review_runs.id"), nullable=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    actor_role: Mapped[str] = mapped_column(String(20))
    content_revision: Mapped[int] = mapped_column()
    source_revision: Mapped[int] = mapped_column()
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

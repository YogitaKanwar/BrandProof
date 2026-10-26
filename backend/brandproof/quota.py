"""Persistent conservative provider admission; no queue or retry amplification."""

from datetime import datetime, timedelta

from sqlalchemy import DateTime, ForeignKey, String, func, select, update
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Mapped, mapped_column

from brandproof.db import Base
from brandproof.models import new_id, utcnow
from brandproof.review_models import ReviewRun


class AIQuotaGuard(Base):
    __tablename__ = "ai_quota_guard"
    id: Mapped[int] = mapped_column(primary_key=True)


class AIAdmission(Base):
    __tablename__ = "ai_admissions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("review_runs.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


def reserve_provider_call(session, workspace_id, review_id, settings):
    """Called under campaign lock; serialise admissions globally until commit.

    Reservation counts even failed calls. No refund, external queue or paid fallback.
    A crashed running reservation occupies a slot until explicit operator recovery.
    """
    insert = sqlite_insert if session.bind.dialect.name == "sqlite" else postgres_insert
    session.execute(insert(AIQuotaGuard).values(id=1).on_conflict_do_nothing(index_elements=["id"]))
    session.execute(update(AIQuotaGuard).where(AIQuotaGuard.id == 1).values(id=1))
    since = utcnow() - timedelta(hours=1)
    recent = select(AIAdmission).where(AIAdmission.created_at >= since)
    global_count = session.scalar(select(func.count()).select_from(recent.subquery()))
    workspace_count = session.scalar(
        select(func.count()).select_from(
            recent.where(AIAdmission.workspace_id == workspace_id).subquery()
        )
    )
    running = (
        select(AIAdmission)
        .join(ReviewRun, AIAdmission.review_id == ReviewRun.id)
        .where(ReviewRun.status == "running")
    )
    global_running = session.scalar(select(func.count()).select_from(running.subquery()))
    workspace_running = session.scalar(
        select(func.count()).select_from(
            running.where(AIAdmission.workspace_id == workspace_id).subquery()
        )
    )
    for count, limit, reason in [
        (workspace_count, settings.ai_workspace_hourly_limit, "workspace_hourly_limit"),
        (global_count, settings.ai_global_hourly_limit, "global_hourly_limit"),
        (workspace_running, settings.ai_workspace_concurrency_limit, "workspace_provider_busy"),
        (global_running, settings.ai_global_concurrency_limit, "global_provider_busy"),
    ]:
        if count >= limit:
            return reason
    session.add(AIAdmission(workspace_id=workspace_id, review_id=review_id))
    return None

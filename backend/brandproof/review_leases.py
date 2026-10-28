"""Heartbeats and fencing for automatically recovering interrupted inference.

Legacy running reviews without leases require the existing stopped-worker CLI.
Lease expiration is not a wall-clock provider SLA. Live workers renew leases.
"""

import secrets
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta

from sqlalchemy import DateTime, ForeignKey, String, select, update
from sqlalchemy.orm import Mapped, mapped_column

from brandproof.auth import lock_campaign
from brandproof.db import Base
from brandproof.models import Campaign, utcnow
from brandproof.review_models import ReviewRun

LEASE_SECONDS = 180


class ReviewLease(Base):
    __tablename__ = "review_leases"
    review_id: Mapped[str] = mapped_column(ForeignKey("review_runs.id"), primary_key=True)
    owner: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


def acquire(session, run):
    session.flush()
    owner = secrets.token_hex(32)
    session.add(
        ReviewLease(
            review_id=run.id, owner=owner, expires_at=utcnow() + timedelta(seconds=LEASE_SECONDS)
        )
    )
    return owner


def fence(session, review_id, owner):
    return (
        session.execute(
            update(ReviewLease)
            .where(
                ReviewLease.review_id == review_id,
                ReviewLease.owner == owner,
                ReviewLease.expires_at > utcnow(),
            )
            .values(owner="", expires_at=utcnow())
        ).rowcount
        == 1
    )


@contextmanager
def heartbeat(sessions, review_id, owner):
    stopped = threading.Event()

    def renew():
        while not stopped.wait(10):
            try:
                with sessions.begin() as session:
                    count = session.execute(
                        update(ReviewLease)
                        .where(
                            ReviewLease.review_id == review_id,
                            ReviewLease.owner == owner,
                            ReviewLease.expires_at > utcnow(),
                        )
                        .values(expires_at=utcnow() + timedelta(seconds=LEASE_SECONDS))
                    ).rowcount
                if not count:
                    return
            except Exception:
                # Lost/uncertain DB access cannot authorize a late completion.
                return

    worker = threading.Thread(target=renew, daemon=True)
    worker.start()
    try:
        yield
    finally:
        stopped.set()
        worker.join(timeout=2)


def recover_expired(session, campaign_id=None):
    query = (
        select(ReviewRun.campaign_id)
        .join(ReviewLease)
        .where(
            ReviewRun.status == "running",
            ReviewLease.expires_at <= utcnow(),
            ReviewLease.owner != "",
        )
    )
    if campaign_id:
        query = query.where(ReviewRun.campaign_id == campaign_id)
    count = 0
    for identity in sorted(set(session.scalars(query))):
        campaign = session.get(Campaign, identity)
        lock_campaign(session, campaign)
        rows = session.execute(
            select(ReviewRun, ReviewLease)
            .join(ReviewLease)
            .where(
                ReviewRun.campaign_id == identity,
                ReviewRun.status == "running",
                ReviewLease.expires_at <= utcnow(),
                ReviewLease.owner != "",
            )
            .execution_options(populate_existing=True)
        ).all()
        for run, lease in rows:
            lease.owner = ""
            run.status = "partial"
            run.checks = {
                **run.checks,
                "contextual": {
                    "status": "unavailable",
                    "reason": "process_interrupted",
                    "details": {"recovery": "expired_worker_lease", "manual_review_required": True},
                },
            }
            count += 1
    session.flush()
    return count

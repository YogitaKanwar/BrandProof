"""Manual interrupted-review recovery. Stop every app/worker before running.

Age alone cannot distinguish an interrupted job from a slow live provider call.
This module deliberately does not register automatic startup recovery.
"""

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from brandproof.auth import lock_campaign
from brandproof.models import Campaign
from brandproof.review_models import ReviewRun


def recover_stalled_reviews(session: Session, *, older_than: datetime) -> int:
    """Recover stale running jobs; caller owns commit/rollback and must stop workers.

    Acquire campaign locks in ID order, before reading/mutating review snapshots,
    exactly as live review writers do. Refresh cached runs after acquiring locks.
    Use a dedicated, clean session; naive cutoffs are interpreted as UTC.
    This cannot identify a live-but-slow job: all app/worker processes must be stopped.
    """
    older_than = (
        older_than.replace(tzinfo=UTC) if older_than.tzinfo is None else older_than.astimezone(UTC)
    )
    campaign_ids = session.scalars(
        select(ReviewRun.campaign_id)
        .where(ReviewRun.status == "running", ReviewRun.created_at < older_than)
        .distinct()
        .order_by(ReviewRun.campaign_id)
    ).all()
    count = 0
    for campaign_id in campaign_ids:
        campaign = session.get(Campaign, campaign_id)
        lock_campaign(session, campaign)
        runs = session.scalars(
            select(ReviewRun)
            .where(
                ReviewRun.campaign_id == campaign_id,
                ReviewRun.status == "running",
                ReviewRun.created_at < older_than,
            )
            .execution_options(populate_existing=True)
        ).all()
        for run in runs:
            run.status = "partial"
            run.checks = {
                **run.checks,
                "contextual": {
                    "status": "unavailable",
                    "reason": "process_interrupted",
                    "details": {"recovery": True},
                },
            }
            count += 1
    session.flush()
    return count


class _SafeParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default message can contain secrets from user arguments.
        self.exit(2, json.dumps({"error": "invalid_arguments"}) + "\n")


def main() -> int:
    from brandproof.config import Settings
    from brandproof.db import make_engine, session_factory

    parser = _SafeParser(description=__doc__)
    parser.add_argument("--database-url", help="Default: Settings.database_url")
    parser.add_argument(
        "--older-than-seconds",
        type=int,
        default=300,
        help="Minimum age in seconds, 60–86400 inclusive (default: 300)",
    )
    args = parser.parse_args()
    if not 60 <= args.older_than_seconds <= 86400:
        parser.error("unsafe_age")
    try:
        engine = make_engine(args.database_url or Settings().database_url)
        try:
            with session_factory(engine).begin() as session:
                count = recover_stalled_reviews(
                    session,
                    older_than=datetime.now(UTC) - timedelta(seconds=args.older_than_seconds),
                )
        finally:
            engine.dispose()
    except Exception:
        # Never print exception text, connection strings, SQL parameters or content.
        print(json.dumps({"error": "recovery_failed"}), file=sys.stderr)
        return 1
    print(json.dumps({"count": count}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

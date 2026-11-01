"""Operator-only retention cleanup of expired synthetic workspaces; dry-run default.

Never exposed as a guest HTTP endpoint. No schema migration is required.
"""

import argparse
from datetime import timedelta

from sqlalchemy import delete, exists, func, or_, select

from brandproof.demo_session_models import DemoBrowserSession
from brandproof.models import Actor, Workspace, utcnow


def cleanup_expired(sessions, *, retention_days=7, apply=False):
    from brandproof.db import Base

    if retention_days < 1:
        raise ValueError("Retain expired demos for at least one day")
    cutoff = utcnow() - timedelta(days=retention_days)
    with sessions.begin() as session:
        # Only workspaces explicitly marked as browser demos, with no active role.
        ids = list(
            session.scalars(
                select(Workspace.id)
                .join(DemoBrowserSession, Workspace.id == DemoBrowserSession.workspace_id)
                .where(
                    DemoBrowserSession.expires_at < cutoff,
                    ~exists(
                        select(Actor.id).where(
                            Actor.workspace_id == Workspace.id, Actor.expires_at >= cutoff
                        )
                    ),
                )
            )
        )
        conditions = {Workspace.__table__: Workspace.id.in_(ids)}
        counts = {}
        for table in Base.metadata.sorted_tables:
            if table not in conditions:
                linked = [
                    fk.parent.in_(select(fk.column).where(conditions[fk.column.table]))
                    for fk in table.foreign_keys
                    if fk.column.table in conditions
                ]
                if linked:
                    conditions[table] = or_(*linked)
            if table in conditions:
                counts[table.name] = session.scalar(
                    select(func.count()).select_from(table).where(conditions[table])
                )
        if apply:
            for table in reversed(Base.metadata.sorted_tables):
                if table in conditions:
                    session.execute(
                        delete(table).where(conditions[table]),
                        execution_options={"synchronize_session": False},
                    )
        return {"applied": apply, "expired_workspaces": len(ids), "rows": counts}


def main():
    from brandproof.config import Settings
    from brandproof.main import create_app

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retention-days", type=int, default=7)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--isolated-demo-database", action="store_true")
    args = parser.parse_args()
    if args.apply and not args.isolated_demo_database:
        parser.error(
            "--apply requires --isolated-demo-database and an operator-verified isolated database"
        )
    # Engine construction does not run lifespan/migrations or print its URL.
    app = create_app(database_url=Settings().database_url)
    try:
        print(
            cleanup_expired(
                app.state.sessions, retention_days=args.retention_days, apply=args.apply
            )
        )
    finally:
        app.state.engine.dispose()


if __name__ == "__main__":
    main()

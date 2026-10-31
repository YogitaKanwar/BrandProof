from datetime import timedelta

import pytest
from brandproof.db import make_engine, session_factory
from brandproof.main import create_app
from brandproof.migrations import history, migrate, steps
from brandproof.models import Campaign, Workspace, utcnow
from brandproof.review_leases import ReviewLease, acquire, fence, recover_expired
from brandproof.review_models import ReviewRun
from sqlalchemy import inspect, select, text


def test_additive_migration_adopts_existing_database_without_data_loss(tmp_path):
    app = create_app(database_url=f"sqlite:///{tmp_path / 'old.db'}")
    from brandproof.db import Base
    from brandproof.migrations import BASELINE

    Base.metadata.create_all(app.state.engine, tables=[Base.metadata.tables[n] for n in BASELINE])
    with app.state.engine.begin() as connection:
        connection.execute(
            text("INSERT INTO workspaces (id,created_at) VALUES ('preserve','2026-10-28')")
        )
    assert migrate(app.state.engine)["pending"] == [version for version, _ in steps()]
    assert migrate(app.state.engine)["pending"] == []
    with app.state.engine.connect() as connection:
        assert connection.scalar(text("SELECT id FROM workspaces")) == "preserve"
        assert connection.scalar(
            select(history.c.version).where(history.c.version == "0002_review_leases")
        )
    assert "review_leases" in inspect(app.state.engine).get_table_names()


def test_preflight_is_read_only_and_drift_fails_closed(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'drift.db'}")
    assert migrate(engine, apply=False)["pending"]
    assert inspect(engine).get_table_names() == []
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE workspaces (id INTEGER PRIMARY KEY)")
    with pytest.raises(RuntimeError, match="Schema drift"):
        migrate(engine)
    assert inspect(engine).get_table_names() == ["workspaces"]


def test_expired_worker_recovery_preserves_snapshot_and_fences_late_result(tmp_path):
    app = create_app(database_url=f"sqlite:///{tmp_path / 'lease.db'}")
    migrate(app.state.engine)
    sessions = session_factory(app.state.engine)
    with sessions.begin() as session:
        workspace = Workspace()
        session.add(workspace)
        session.flush()
        from datetime import date

        campaign = Campaign(
            workspace_id=workspace.id, name="Test", publication_date=date(2026, 11, 12)
        )
        session.add(campaign)
        session.flush()
        run = ReviewRun(
            campaign_id=campaign.id,
            content_revision=1,
            source_revision=0,
            caption="Immutable",
            status="running",
            checks={},
            sources_used=[],
            excluded_sources=[],
            findings=[{"id": "keep"}],
        )
        session.add(run)
        owner = acquire(session, run)
        identity, campaign_id = run.id, campaign.id
    with sessions.begin() as session:
        assert recover_expired(session, campaign_id) == 0
        session.get(ReviewLease, identity).expires_at = utcnow() - timedelta(seconds=1)
    with sessions.begin() as session:
        assert recover_expired(session, "another-campaign") == 0
        assert recover_expired(session, campaign_id) == 1
        assert not fence(session, identity, owner)
        run = session.get(ReviewRun, identity)
        assert run.caption == "Immutable" and run.findings == [{"id": "keep"}]
        assert run.status == "partial"
        assert run.checks["contextual"]["reason"] == "process_interrupted"
        assert recover_expired(session, campaign_id) == 0

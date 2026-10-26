"""Manual recovery against real file-backed databases; no provider/network calls."""

import json
import os
import subprocess
import sys
from copy import deepcopy
from datetime import UTC, date, datetime, timedelta, timezone

import pytest
from brandproof.db import Base, make_engine, session_factory
from brandproof.models import Campaign, Workspace
from brandproof.review_models import ReviewRun
from sqlalchemy import select

CUTOFF = datetime(2026, 10, 25, 12, tzinfo=UTC)


@pytest.fixture
def recovery_db(tmp_path):
    url = f"sqlite:///{tmp_path / 'recovery.db'}"
    engine = make_engine(url)
    Base.metadata.create_all(engine)
    sessions = session_factory(engine)
    with sessions.begin() as session:
        workspace = Workspace(id="workspace")
        session.add(workspace)
        session.flush()
        session.add(
            Campaign(
                id="campaign",
                workspace_id=workspace.id,
                name="Private campaign",
                publication_date=date(2026, 11, 1),
                caption="Current draft",
                content_revision=7,
                source_revision=5,
            )
        )
    yield url, sessions
    engine.dispose()


def add_run(session, *, run_id="stalled", campaign_id="campaign", **overrides):
    values = {
        "id": run_id,
        "campaign_id": campaign_id,
        "created_at": CUTOFF - timedelta(seconds=1),
        "content_revision": 2,
        "source_revision": 3,
        "caption": "PRIVATE immutable caption",
        "status": "running",
        "checks": {
            "exact_text": {"status": "completed", "rules": [{"source_id": "old-source"}]},
            "poster": {
                "status": "partial",
                "details": {"asset_id": "old-poster", "ocr_text": "PRIVATE OCR"},
            },
            "contextual": {"status": "not_assessed", "reason": "In progress"},
        },
        "sources_used": [{"id": "old-source", "version": 2, "text": "PRIVATE source"}],
        "excluded_sources": [{"source_id": "expired", "reason": "expired"}],
        "findings": [
            {"id": "exact-finding", "category": "price", "evidence": {"quote": "99"}},
            {"id": "poster-finding", "location": {"asset": "poster", "boxes": []}},
        ],
    }
    values.update(overrides)
    run = ReviewRun(**values)
    session.add(run)
    session.flush()
    return run


def snapshot(run):
    return deepcopy(
        {column.name: getattr(run, column.name) for column in ReviewRun.__table__.columns}
    )


def test_recovery_preserves_exact_poster_findings_and_immutable_snapshot(recovery_db):
    from brandproof.recovery import recover_stalled_reviews

    _, sessions = recovery_db
    with sessions.begin() as session:
        add_run(session)
    with sessions() as session:
        before = snapshot(session.get(ReviewRun, "stalled"))
    with sessions.begin() as session:
        assert recover_stalled_reviews(session, older_than=CUTOFF) == 1
    with sessions() as session:
        after = snapshot(session.get(ReviewRun, "stalled"))
        assert after["status"] == "partial"
        assert after["checks"]["contextual"] == {
            "status": "unavailable",
            "reason": "process_interrupted",
            "details": {"recovery": True},
        }
        for key in before.keys() - {"status", "checks"}:
            assert after[key] == before[key], key
        for key in before["checks"].keys() - {"contextual"}:
            assert after["checks"][key] == before["checks"][key]
        assert session.scalar(select(Campaign.content_revision)) == 7
        assert session.scalar(select(Campaign.source_revision)) == 5


def test_cutoff_is_an_instant_in_any_timezone(recovery_db):
    from brandproof.recovery import recover_stalled_reviews

    _, sessions = recovery_db
    with sessions.begin() as session:
        add_run(session, created_at=CUTOFF + timedelta(hours=1))
    with sessions.begin() as session:
        cutoff = CUTOFF.astimezone(timezone(timedelta(hours=5, minutes=30)))
        assert recover_stalled_reviews(session, older_than=cutoff) == 0


def run_cli(*args, env=None):
    return subprocess.run(
        [sys.executable, "-m", "brandproof.recovery", *args],
        capture_output=True,
        text=True,
        timeout=20,
        env=env,
    )


def test_cli_commits_recovery_and_prints_only_count(recovery_db):
    url, sessions = recovery_db
    with sessions.begin() as session:
        add_run(session)
    result = run_cli("--database-url", url)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"count": 1}
    assert result.stderr == ""
    with sessions() as session:
        run = session.get(ReviewRun, "stalled")
        assert run.status == "partial"
        assert run.checks["contextual"]["details"]["recovery"] is True


@pytest.mark.parametrize("age", ["-1", "0", "59", "86401", "nan", "SECRET-input"])
def test_cli_rejects_unsafe_ages_without_echoing_input(recovery_db, age):
    url, _ = recovery_db
    result = run_cli("--database-url", url, "--older-than-seconds", age)
    assert result.returncode == 2
    assert result.stdout == ""
    assert json.loads(result.stderr) == {"error": "invalid_arguments"}


def test_cli_sanitizes_database_errors_without_tracebacks():
    result = run_cli(
        "--database-url", "invalid-driver://private-user:SECRET-password@private-host/db"
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert json.loads(result.stderr) == {"error": "recovery_failed"}


def test_recent_boundary_completed_partial_and_repeat_are_unchanged(recovery_db):
    from brandproof.recovery import recover_stalled_reviews
    from brandproof.workflow_models import Approval

    _, sessions = recovery_db
    with sessions.begin() as session:
        add_run(session)
        add_run(session, run_id="boundary", created_at=CUTOFF)
        add_run(session, run_id="recent", created_at=CUTOFF + timedelta(seconds=1))
        add_run(session, run_id="completed", status="completed")
        add_run(session, run_id="partial", status="partial")
    with sessions() as session:
        untouched = {
            run.id: snapshot(run)
            for run in session.scalars(select(ReviewRun))
            if run.id != "stalled"
        }
    with sessions.begin() as session:
        assert recover_stalled_reviews(session, older_than=CUTOFF) == 1
        assert recover_stalled_reviews(session, older_than=CUTOFF) == 0
    with sessions.begin() as session:
        assert recover_stalled_reviews(session, older_than=CUTOFF) == 0
        for run_id, before in untouched.items():
            assert snapshot(session.get(ReviewRun, run_id)) == before
        assert session.scalars(select(Approval)).all() == []


@pytest.mark.parametrize("change", ["completed", "recent", "new_snapshot"])
def test_rechecks_fresh_run_after_shared_lock(recovery_db, monkeypatch, change):
    import brandproof.recovery as recovery

    _, sessions = recovery_db
    with sessions.begin() as session:
        add_run(session)
    real_lock = recovery.lock_campaign
    latest = {}

    def writer_wins_before_lock(session, campaign):
        # Force a real second connection to commit between discovery and lock.
        # The recovery Session already has an intentionally stale identity map.
        with sessions.begin() as writer:
            run = writer.get(ReviewRun, "stalled")
            run.checks = {"exact_text": {"status": "partial", "reason": "new evidence"}}
            run.findings = [{"id": "fresh-finding"}]
            if change == "completed":
                run.status = "completed"
            elif change == "recent":
                run.created_at = CUTOFF + timedelta(seconds=1)
        with sessions() as reader:
            latest.update(snapshot(reader.get(ReviewRun, "stalled")))
        real_lock(session, campaign)

    monkeypatch.setattr(recovery, "lock_campaign", writer_wins_before_lock)
    with sessions.begin() as session:
        cached = session.get(ReviewRun, "stalled")
        assert cached.status == "running"
        assert recovery.recover_stalled_reviews(session, older_than=CUTOFF) == (
            1 if change == "new_snapshot" else 0
        )
    with sessions() as session:
        actual = snapshot(session.get(ReviewRun, "stalled"))
        if change == "new_snapshot":
            assert actual["checks"]["exact_text"] == latest["checks"]["exact_text"]
            assert actual["findings"] == latest["findings"]
            assert actual["status"] == "partial"
        else:
            assert actual == latest


def test_locks_each_campaign_once_in_shared_order(recovery_db, monkeypatch):
    import brandproof.recovery as recovery

    _, sessions = recovery_db
    with sessions.begin() as session:
        for campaign_id in ["z-campaign", "a-campaign"]:
            session.add(
                Campaign(
                    id=campaign_id,
                    workspace_id="workspace",
                    name="Private",
                    publication_date=date(2026, 11, 1),
                )
            )
        session.flush()
        add_run(session, run_id="z-run", campaign_id="z-campaign")
        add_run(session, run_id="a-run-1", campaign_id="a-campaign")
        add_run(session, run_id="a-run-2", campaign_id="a-campaign")
        add_run(session, created_at=CUTOFF)
    locked = []
    real_lock = recovery.lock_campaign

    def record_lock(session, campaign):
        locked.append(campaign.id)
        real_lock(session, campaign)

    monkeypatch.setattr(recovery, "lock_campaign", record_lock)
    with sessions.begin() as session:
        assert recovery.recover_stalled_reviews(session, older_than=CUTOFF) == 3
    assert locked == ["a-campaign", "z-campaign"]


def test_caller_can_roll_back_recovery(recovery_db):
    from brandproof.recovery import recover_stalled_reviews

    _, sessions = recovery_db
    with sessions.begin() as session:
        add_run(session)
    with sessions() as session:
        assert recover_stalled_reviews(session, older_than=CUTOFF) == 1
        session.rollback()
    with sessions() as session:
        assert session.get(ReviewRun, "stalled").status == "running"


def test_cli_uses_settings_database_url_and_default_300_seconds(recovery_db):
    url, sessions = recovery_db
    now = datetime.now(UTC)
    with sessions.begin() as session:
        add_run(session, run_id="old", created_at=now - timedelta(seconds=600))
        add_run(session, run_id="recent", created_at=now - timedelta(seconds=120))
    result = run_cli(env={**os.environ, "BRANDPROOF_DATABASE_URL": url})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"count": 1}
    assert result.stderr == ""
    with sessions() as session:
        assert session.get(ReviewRun, "old").status == "partial"
        assert session.get(ReviewRun, "recent").status == "running"


@pytest.mark.parametrize("age", ["60", "86400"])
def test_cli_accepts_inclusive_age_bounds(recovery_db, age):
    url, _ = recovery_db
    result = run_cli("--database-url", url, "--older-than-seconds", age)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"count": 0}
    assert result.stderr == ""


def test_cli_help_requires_stopping_all_app_workers():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "Stop every app/worker before running" in result.stdout
    assert "default: 300" in " ".join(result.stdout.split())
    assert result.stderr == ""


def test_recovery_statements_compile_for_postgresql_while_executing_sqlite(recovery_db):
    from brandproof.recovery import recover_stalled_reviews
    from sqlalchemy import event
    from sqlalchemy.dialects import postgresql

    _, sessions = recovery_db
    with sessions.begin() as session:
        add_run(session)
    compiled = []
    engine = sessions.kw["bind"]

    def compile_statement(connection, clauseelement, multiparams, params, execution_options):
        compiled.append(str(clauseelement.compile(dialect=postgresql.dialect())))

    event.listen(engine, "before_execute", compile_statement)
    try:
        with sessions.begin() as session:
            assert recover_stalled_reviews(session, older_than=CUTOFF) == 1
    finally:
        event.remove(engine, "before_execute", compile_statement)
    assert any(sql.startswith("UPDATE campaigns") for sql in compiled)
    assert any(sql.startswith("UPDATE review_runs") for sql in compiled)
    assert any("review_runs.created_at <" in sql for sql in compiled)

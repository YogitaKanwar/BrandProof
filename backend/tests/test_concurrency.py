from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest
from brandproof.review_models import ContentVersion, ReviewRun
from sqlalchemy import event, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.dml import Update
from test_reviews import add_source


def test_two_first_caption_saves_have_one_winner_and_immutable_initial_history(
    client, owner, campaign, monkeypatch
):
    first_writes = Barrier(2)
    original = Session.execute

    def synchronized_first_write(session, statement, *args, **kwargs):
        if (
            isinstance(statement, Update)
            and statement.table.name == "campaigns"
            and not session.info.get("first_caption_write")
        ):
            session.info["first_caption_write"] = True
            # Pause before execute/autoflush: in the original bug both sessions
            # have queued the absent initial history row before either can write.
            first_writes.wait(timeout=5)
        return original(session, statement, *args, **kwargs)

    monkeypatch.setattr(Session, "execute", synchronized_first_write)
    base = f"/api/v1/campaigns/{campaign['id']}"

    def save(text):
        try:
            return client.put(
                f"{base}/caption",
                headers=owner,
                json={"expected_revision": 1, "text": text},
            ).status_code
        except Exception as error:
            return type(error).__name__

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, ["First copy", "Other copy"]))
    assert sorted(results, key=str) == [200, 409], results
    with client.app.state.sessions() as session:
        history = session.scalars(
            select(ContentVersion)
            .where(ContentVersion.campaign_id == campaign["id"])
            .order_by(ContentVersion.revision)
        ).all()
        assert [(v.revision, v.caption) for v in history][:1] == [(1, "")]
        assert [v.revision for v in history] == [1, 2]


@pytest.mark.parametrize("phase", ["collection", "insertion"])
@pytest.mark.parametrize(
    "mutation", ["caption", "create_source", "revise_source", "confirm_source"]
)
def test_review_snapshot_insertion_serializes_with_every_mutator(
    client, owner, campaign, monkeypatch, mutation, phase
):
    base = f"/api/v1/campaigns/{campaign['id']}"
    source = add_source(
        client,
        owner,
        campaign,
        {"kind": "required_text", "text": "Terms apply"},
        confirm=mutation != "confirm_source",
    )
    assert (
        client.put(
            f"{base}/caption",
            headers=owner,
            json={"expected_revision": 1, "text": "Workshop. Terms apply."},
        ).status_code
        == 200
    )
    current = client.get(base, headers=owner).json()
    ready, attempted, finished = Event(), Event(), Event()
    completed_before_insert = []
    original_add = Session.add

    def pause_review():
        ready.set()
        assert attempted.wait(5), "Mutator never attempted a database write"
        completed_before_insert.append(finished.wait(0.3))

    def pause_insert(session, instance, *args, **kwargs):
        if phase == "insertion" and isinstance(instance, ReviewRun):
            pause_review()
        return original_add(session, instance, *args, **kwargs)

    def observe_attempt(_conn, _cursor, statement, _parameters, _context, _many):
        if phase == "collection" and not ready.is_set() and "JOIN source_versions" in statement:
            # Pause before collecting any source rows, not just before insertion.
            pause_review()
        if ready.is_set() and statement.startswith(("UPDATE", "INSERT")):
            attempted.set()

    monkeypatch.setattr(Session, "add", pause_insert)
    event.listen(client.app.state.engine, "before_cursor_execute", observe_attempt)

    def mutate():
        try:
            if mutation == "caption":
                return client.put(
                    f"{base}/caption",
                    headers=owner,
                    json={"expected_revision": 2, "text": "Changed. Terms apply."},
                )
            if mutation == "create_source":
                return client.post(
                    f"{base}/sources",
                    headers=owner,
                    json={
                        "title": "New source",
                        "rule": {"kind": "required_text", "text": "New"},
                    },
                )
            if mutation == "revise_source":
                return client.put(
                    f"{base}/sources/{source['id']}",
                    headers=owner,
                    json={
                        "expected_version": source["version"],
                        "title": "Changed",
                        "rule": {"kind": "required_text", "text": "Changed"},
                    },
                )
            return client.post(
                f"{base}/sources/{source['id']}/confirm",
                headers=owner,
                json={"expected_version": source["version"]},
            )
        finally:
            finished.set()

    try:
        with (
            ThreadPoolExecutor(max_workers=1) as reader,
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="mutator") as writer,
        ):
            pending = reader.submit(
                client.post,
                f"{base}/reviews",
                headers=owner,
                json={
                    "expected_content_revision": 2,
                    "expected_source_revision": current["source_revision"],
                },
            )
            assert ready.wait(5)
            edit = writer.submit(mutate)
            response = pending.result(timeout=10)
            changed = edit.result(timeout=10)
    finally:
        event.remove(client.app.state.engine, "before_cursor_execute", observe_attempt)
    assert changed.status_code in (200, 201), changed.text
    assert response.status_code == 201, response.text
    assert completed_before_insert == [False], "Edit committed between snapshot check and insert"
    run = response.json()
    assert run["content_revision"] == 2
    assert run["source_revision"] == current["source_revision"]
    stored = client.get(f"{base}/reviews/{run['id']}", headers=owner).json()
    assert stored["is_current"] is False  # A later edit may invalidate the linearized run.
    assert stored["caption"] == "Workshop. Terms apply."


def test_review_response_refreshes_campaign_after_commit(client, owner, campaign, monkeypatch):
    base = f"/api/v1/campaigns/{campaign['id']}"
    client.put(
        f"{base}/caption",
        headers=owner,
        json={"expected_revision": 1, "text": "Original"},
    )
    original_commit = Session.commit
    edited = []

    def commit_then_edit(session):
        # Lease creation flushes the run before commit; observe both pending
        # and flushed running records while preserving the post-commit race.
        is_review = (
            any(
                isinstance(row, ReviewRun) and row.status == "running"
                for row in [*session.new, *session.identity_map.values()]
            )
            and not edited
        )
        original_commit(session)
        if is_review:
            changed = client.put(
                f"{base}/caption",
                headers=owner,
                json={"expected_revision": 2, "text": "Edited after review commit"},
            )
            edited.append(changed.status_code)

    monkeypatch.setattr(Session, "commit", commit_then_edit)
    response = client.post(
        f"{base}/reviews",
        headers=owner,
        json={"expected_content_revision": 2, "expected_source_revision": 0},
    )
    assert response.status_code == 201, response.text
    assert edited == [200]
    assert response.json()["is_current"] is False

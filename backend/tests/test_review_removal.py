from brandproof.models import Campaign
from brandproof.review_models import ContentVersion, ReviewRun
from brandproof.source_models import SourceVersion
from conftest import headers
from sqlalchemy import func, select
from test_reviews import add_source, review_copy


def snapshot(client, base, owner):
    current = client.get(base, headers=owner).json()
    return {
        "expected_content_revision": current["content_revision"],
        "expected_source_revision": current["source_revision"],
    }


def test_delete_hides_access_but_undo_preserves_versions_findings_and_other_campaigns(
    client, demo, owner, campaign
):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    run = review_copy(client, owner, campaign, "Book for INR 599.")
    base = f"/api/v1/campaigns/{campaign['id']}"
    before_campaign = client.get(base, headers=owner).json()
    before_sources = client.get(base + "/sources", headers=owner).json()
    before_receipt = client.get(base + "/receipt", headers=owner).json()
    other = client.post(
        "/api/v1/campaigns",
        headers=owner,
        json={"name": "Keep this campaign", "publication_date": "2026-11-12"},
    ).json()
    expected = snapshot(client, base, owner)
    with client.app.state.sessions() as session:
        stored_findings = session.get(ReviewRun, run["id"]).findings
    response = client.request("DELETE", base, headers=owner, json=expected)
    assert response.status_code == 200
    removed = response.json()
    assert removed["deleted"] and removed["retained_history"]
    assert [row["id"] for row in client.get("/api/v1/campaigns", headers=owner).json()] == [
        other["id"]
    ]
    for suffix in ["", "/sources", "/reviews", "/revisions", "/receipt"]:
        assert client.get(base + suffix, headers=owner).status_code == 404
    assert (
        client.put(
            base + "/caption",
            headers=owner,
            json={"expected_revision": 2, "text": "Must not write"},
        ).status_code
        == 404
    )
    with client.app.state.sessions() as session:
        assert session.get(Campaign, campaign["id"]) is not None
        assert session.scalar(select(func.count()).select_from(ContentVersion)) == 2
        assert session.scalar(select(func.count()).select_from(SourceVersion)) == 2
        assert session.get(ReviewRun, run["id"]).findings == stored_findings
    restore = {**expected, "expected_deletion_id": removed["deletion_id"]}
    assert client.post(base + "/restore", headers=owner, json=restore).json() == before_campaign
    assert client.get(base + "/sources", headers=owner).json() == before_sources
    assert client.get(base + "/receipt", headers=owner).json() == before_receipt
    assert client.get(base + "/reviews/" + run["id"], headers=owner).json() == run
    assert len(client.get("/api/v1/campaigns", headers=owner).json()) == 2


def test_delete_permissions_stale_snapshot_running_guard_and_restore_generation(
    client, demo, owner, campaign
):
    base = f"/api/v1/campaigns/{campaign['id']}"
    expected = snapshot(client, base, owner)
    for role in ["creator", "reviewer"]:
        assert (
            client.request("DELETE", base, headers=headers(demo, role), json=expected).status_code
            == 403
        )
    other = client.post("/api/v1/demo-sessions").json()
    assert client.request("DELETE", base, headers=headers(other), json=expected).status_code == 404
    assert (
        client.request(
            "DELETE", base, headers=owner, json={**expected, "expected_source_revision": 1}
        ).status_code
        == 409
    )
    run = review_copy(client, owner, campaign, "A saved caption.")
    expected = snapshot(client, base, owner)
    with client.app.state.sessions.begin() as session:
        session.get(ReviewRun, run["id"]).status = "running"
    assert (
        client.request("DELETE", base, headers=owner, json=expected).json()["error"]["code"]
        == "review_in_progress"
    )
    with client.app.state.sessions.begin() as session:
        session.get(ReviewRun, run["id"]).status = "partial"
    first = client.request("DELETE", base, headers=owner, json=expected).json()
    restore = {**expected, "expected_deletion_id": first["deletion_id"]}
    assert client.post(base + "/restore", headers=headers(other), json=restore).status_code == 404
    assert (
        client.post(base + "/restore", headers=headers(demo, "creator"), json=restore).status_code
        == 403
    )
    assert client.post(base + "/restore", headers=owner, json=restore).status_code == 200
    second = client.request("DELETE", base, headers=owner, json=expected).json()
    assert first["deletion_id"] != second["deletion_id"]
    assert client.post(base + "/restore", headers=owner, json=restore).status_code == 409
    assert (
        client.post(
            base + "/restore",
            headers=owner,
            json={**restore, "expected_deletion_id": second["deletion_id"]},
        ).status_code
        == 200
    )


def test_additive_startup_preserves_legacy_tables_and_saved_rows(client, owner, campaign):
    from brandproof.db import Base
    from brandproof.main import create_app
    from brandproof.removal_models import CampaignRemoval
    from fastapi.testclient import TestClient
    from sqlalchemy import inspect, text

    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    review_copy(client, owner, campaign, "Book for INR 599.")
    engine = client.app.state.engine
    # This disposable fixture database now represents the deployed legacy schema.
    CampaignRemoval.__table__.drop(engine)
    names = inspect(engine).get_table_names()

    def snapshot():
        with engine.connect() as connection:
            return {
                name: (
                    [
                        (column["name"], str(column["type"]), column["nullable"])
                        for column in inspect(connection).get_columns(name)
                    ],
                    sorted(
                        repr(tuple(row))
                        for row in connection.execute(text(f'SELECT * FROM "{name}"'))
                    ),
                )
                for name in names
            }

    before = snapshot()
    with TestClient(create_app(database_url=str(engine.url))) as restarted:
        assert restarted.get("/api/v1/health").status_code == 200
        assert set(inspect(engine).get_table_names()) - set(names) == {"campaign_removals"}
        assert snapshot() == before
        assert (
            restarted.get(f"/api/v1/campaigns/{campaign['id']}", headers=owner).status_code == 200
        )
    with TestClient(create_app(database_url=str(engine.url))):
        assert snapshot() == before
    assert "campaign_removals" in Base.metadata.tables


def test_postgres_upgrade_ddl_creates_only_the_additive_removal_table():
    from brandproof.db import Base
    from brandproof.removal_models import CampaignRemoval
    from sqlalchemy import create_mock_engine
    from sqlalchemy.dialects import postgresql

    statements = []
    engine = create_mock_engine(
        "postgresql+psycopg://",
        lambda sql, *args, **kwargs: statements.append(
            str(sql.compile(dialect=postgresql.dialect()))
        ),
    )
    Base.metadata.create_all(engine, tables=[CampaignRemoval.__table__], checkfirst=False)
    assert len(statements) == 1
    assert "CREATE TABLE campaign_removals" in statements[0]
    assert "FOREIGN KEY(campaign_id) REFERENCES campaigns (id)" in statements[0]
    assert "FOREIGN KEY(removed_by) REFERENCES actors (id)" in statements[0]
    assert not any(word in statements[0] for word in ["DROP TABLE", "ALTER TABLE", "DELETE FROM"])

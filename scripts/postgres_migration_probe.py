"""CI-only upgrade probe in its own schema; never connects to production."""

import json
import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url


def main():
    from brandproof.config import Settings
    from brandproof.db import Base
    from brandproof.main import create_app
    from brandproof.migrations import BASELINE, migrate

    url = make_url(Settings().database_url)
    if (
        os.environ.get("BRANDPROOF_EPHEMERAL_CI") != "1"
        or url.host not in {"127.0.0.1", "localhost"}
        or url.database != "brandproof_test"
    ):
        raise SystemExit("Refused: requires explicitly marked loopback ephemeral CI database")
    url = url.set(drivername="postgresql+psycopg")
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text("CREATE SCHEMA brandproof_migration_probe"))
    engine = create_engine(
        url, connect_args={"options": "-csearch_path=brandproof_migration_probe"}
    )
    app = create_app(database_url=url.render_as_string(hide_password=False))
    try:
        Base.metadata.create_all(engine, tables=[Base.metadata.tables[name] for name in BASELINE])
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO workspaces (id,created_at) VALUES ('preserve-ci',CURRENT_TIMESTAMP)"
                )
            )
        assert migrate(engine, apply=False)["pending"]
        assert migrate(engine)["pending"]
        assert migrate(engine)["pending"] == []
        with engine.connect() as connection:
            assert (
                connection.scalar(text("SELECT id FROM workspaces WHERE id='preserve-ci'"))
                == "preserve-ci"
            )
        assert {
            "document_evidence",
            "alt_text_versions",
            "review_leases",
            "legal_profile_versions",
        } <= set(inspect(engine).get_table_names())
        print(
            json.dumps(
                {
                    "postgres_legacy_upgrade": "passed",
                    "idempotent_retry": "passed",
                    "retained_rows": "passed",
                }
            )
        )
    finally:
        app.state.engine.dispose()
        engine.dispose()
        admin.dispose()


if __name__ == "__main__":
    main()

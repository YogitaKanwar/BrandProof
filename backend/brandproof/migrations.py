"""Versioned additive migrations. Never drop data or silently repair schema drift.

Deployment preflight: back up the database, run --check, then --apply with all
old workers stopped. Startup applies the same idempotent steps under a DB lock.
Unknown versions or changed existing columns fail closed. Rollback is an older
application with these additive tables retained, never destructive downgrade.
"""

import argparse
import json
from pathlib import Path

from sqlalchemy import Column, MetaData, String, Table, inspect, select, text

from brandproof.db import Base

history = Table("schema_migrations", MetaData(), Column("version", String(40), primary_key=True))
BASELINE = json.loads(Path(__file__).with_name("migration_baseline.json").read_text())


def steps():
    return [
        ("0001_legacy", list(BASELINE)),
        ("0002_review_leases", ["review_leases"]),
        ("0003_guideline_documents", ["guideline_documents", "document_evidence"]),
        ("0004_alt_text", ["alt_text_versions"]),
        ("0005_review_removal", ["campaign_removals"]),
        ("0006_advertising_profile", ["legal_profile_versions"]),
    ]


def validate_table(connection, name, expected):
    found = {c["name"]: c for c in inspect(connection).get_columns(name)}
    if set(found) != set(expected):
        raise RuntimeError(f"Schema drift in {name}; explicit migration required")
    for key, spec in expected.items():
        if isinstance(spec, dict):
            column = found[key]
            if (
                column["type"]._type_affinity.__name__ != spec["type"]
                or column["nullable"] != spec["nullable"]
                or getattr(column["type"], "length", None) != spec["length"]
            ):
                raise RuntimeError(f"Schema drift in {name}; explicit migration required")


def column_spec(table):
    return {
        c.name: {
            "type": c.type._type_affinity.__name__,
            "nullable": c.nullable,
            "length": getattr(c.type, "length", None),
        }
        for c in table.columns
    }


def migrate(engine, *, apply=True):
    if engine.dialect.name not in {"sqlite", "postgresql"}:
        raise RuntimeError("Unsupported migration database")
    with engine.connect() as connection:
        if engine.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        else:
            connection.begin()
            connection.execute(text("SELECT pg_advisory_xact_lock(748260028)"))
        try:
            existing = set(inspect(connection).get_table_names())
            applied = (
                set(connection.scalars(select(history.c.version)))
                if history.name in existing
                else set()
            )
            known = {version for version, _ in steps()}
            if applied - known:
                raise RuntimeError(
                    "Database is newer than this application; upgrade the application"
                )
            for _, names in steps():
                for name in names:
                    if name in existing:
                        validate_table(
                            connection,
                            name,
                            BASELINE.get(name, column_spec(Base.metadata.tables[name])),
                        )
            pending = [version for version, _ in steps() if version not in applied]
            if apply:
                history.create(connection, checkfirst=True)
                for version, names in steps():
                    if version in applied:
                        continue
                    Base.metadata.create_all(
                        connection, tables=[Base.metadata.tables[name] for name in names]
                    )
                    connection.execute(history.insert().values(version=version))
                connection.commit()
            else:
                connection.rollback()
            return {"pending": pending, "applied": apply, "destructive": False}
        except Exception:
            connection.rollback()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    from brandproof.main import create_app

    app = create_app()
    try:
        print(json.dumps(migrate(app.state.engine, apply=args.apply)))
    except Exception:
        # Connection exceptions can contain credentials. Never echo them.
        print(json.dumps({"error": "migration_preflight_failed", "destructive": False}))
        raise SystemExit(1) from None
    finally:
        app.state.engine.dispose()


if __name__ == "__main__":
    main()

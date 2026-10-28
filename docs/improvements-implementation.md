# Authorized improvements implementation

Feature branch: `feat/brandproof-improvements-20261028`, based on production `36cb8ae`.
Original local documentation additions and assessment are preserved and remain uncommitted. Production deployment requires review; this feature branch must not auto-deploy.

## Stage G1 — migrations and interrupted-review safety

- Added explicit numbered additive schema steps, an inspected legacy baseline, schema drift/newer-version refusal, SQLite writer locking and PostgreSQL transaction advisory locking. No drop/alter/destructive downgrade. `python -m brandproof.migrations --check` reports pending steps; `--apply` applies them. Back up and stop old workers before production migration. An older application may run with additive tables retained; do not delete them to roll back.
- Added worker-owned 180-second leases, ten-second heartbeats and finalization fencing. Expired leased runs recover to partial/unavailable on startup or review reads, preserving findings/inputs. Healthy slow workers renew; legacy unleased jobs retain the stopped-worker recovery CLI.
- Focused migration/lease/contextual/manual-recovery suites: 122 passed. Existing frontend production build/lint passed. Full PostgreSQL/container acceptance remains a separate final stage; no production migration was run.

Subsequent stages and final validation will be recorded here.

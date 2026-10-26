# BrandProof backend

Campaign review API for team YOGI2KANWAR, Codex 48. Implementation began during the permitted build window on 26 October 2026.

This is the first backend milestone, not the finished hackathon product. It runs locally and performs real deterministic text checks. It does not yet include AI inference, poster OCR, comments or human content approval.

## Run locally

Requires Python 3.12+ and uv. From the repository root:

    uv sync --extra dev
    uv run uvicorn brandproof.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log

Open http://127.0.0.1:8000/docs for interactive Swagger documentation.
Health: http://127.0.0.1:8000/api/v1/health
Contract: docs/openapi.json

On first startup, the app creates its initial tables and data/brandproof.db. SQLite is the exercised development database. SQLAlchemy and the psycopg driver provide a PostgreSQL configuration path, but PostgreSQL has NOT been tested. The current schema bootstrap is not a migration system; use a fresh database for this initial milestone and do not assume future upgrades can alter old tables automatically.

Optional configuration uses .env or environment variables; copy the names from .env.example. Never commit real secrets or data. BRANDPROOF_DATABASE_URL selects storage; BRANDPROOF_CORS_ORIGINS is a JSON list of exact authorised frontend origins. Configuration is read when creating the app.

## Tests and real HTTP smoke test

    uv run pytest -q
    uv run ruff check backend scripts
    uv run ruff format --check backend scripts
    uv run python scripts/smoke.py
    uv run python scripts/parser_smoke.py

The smoke test requires a running API. It creates a new fictional sandbox, confirms four rules, finds four errors, verifies persisted findings, checks corrected copy has no exact findings, and verifies the historical run becomes stale after an edit. Clean copy still returns a partial review because semantic and poster checks are unavailable. The saved docs/examples/live-review.json is actual HTTP output from fictional inputs, not a fabricated model response. It contains no bearer tokens.

## What works

- Persistent, isolated demo workspaces and 24-hour bearer tokens for owner/creator/reviewer roles.
- Campaign creation/read/list with explicit publication date.
- Typed price/date/terminology/required-text sources, plus stored tone/claim-policy guidance for later contextual analysis.
- Owner confirmation and immutable source version history. Revisions become pending until reconfirmed; the previous approved version remains historical, not active.
- Caption revisions with optimistic version conflicts.
- Exact price, ISO-date, whole-term and literal required-wording checks with actual text offsets and exact source/version evidence.
- Multiple prices/dates or conflicting approved main-price/main-date rules request clarification rather than an unsafe replacement. A finite scope grammar also abstains on cashback, deposits, registration deadlines, negation and unknown surrounding wording.
- Exact-check coverage is reported per rule. Missing/unsupported comparable expressions remain not_assessed; an available approved source alone cannot establish a completed comparison.
- Validity is assessed against the campaign publication date. Pending, expired and not-yet-valid sources are excluded and explicitly reported.
- Persisted review snapshots; historical results remain unchanged and expose is_current after content/source edits.
- Uniform validation/auth/conflict errors and generated OpenAPI schemas.

## Important boundaries

This is a fictional-data local demo. Role switching is deliberately available to a sandbox visitor. It is NOT production authentication, verified human identity or independent human sign-off. Tokens are scoped to one workspace, stored as hashes and expire; private accounts are not implemented.

The API is loopback-bound by default. Public session quotas, ingress/body limits, sandbox cleanup, production auth, migrations, deployment hardening and remote persistence are still needed before public judge access. Do not expose the current server directly to the internet or send confidential content.

Rules are bounded, not general semantic understanding. Only the campaign main price and main date are represented. Monetary syntax and date recognition are limited; dates currently require ISO YYYY-MM-DD and terminology/required wording use literal case-insensitive matching. The engine does not yet resolve arbitrary commercial conditions, all currencies, translations, date prose, negation, typography or claim truth. Review status remains partial and readiness remains not_approved for every run. No API endpoint approves content yet.

No model key was configured and no external model requests have been made. Tone, claim analysis and image checks are honestly marked unavailable/not assessed rather than simulated.

## Team handoff

See docs/FRONTEND_HANDOFF.md for the integration order, role permissions, request examples, result structure and stale-state behaviour. docs/STATUS.md maps this milestone to the plan. frontend implementation belongs to Yogita and is intentionally not generated here.

## Integrity and provenance

Rushab's assigned backend work was implemented with significant assistance from OpenAI models through Hermes Agent. The source and test changes are AI-assisted; team members should review and understand the code they submit. No frontend contribution is claimed for Yogita by this milestone. Actual human contributions must be recorded separately.

Dependencies are declared in pyproject.toml; exact resolved versions are in uv.lock. Third-party libraries are reused components, not original team work. Track their licences and any later templates/services in the final submission. The team repository is https://github.com/YogitaKanwar/BrandProof; its current commit history is the publication record. A project licence has not yet been chosen.

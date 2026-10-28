# BrandProof

Campaign review API for team YOGI2KANWAR, Codex 48. Implementation began during the permitted build window on 26 October 2026.

The React app and FastAPI backend implement approved-source checks, real poster OCR, conservative owner-confirmed logo comparison, collaboration and revision-bound human approval. The combined product is verified locally; no public deployment is claimed. See [free hosting setup](docs/FREE_HOSTING.md) for the prepared single-origin Render Free + Neon Free route. Groq openai/gpt-oss-120b has completed a genuine live API probe with persisted findings. A frozen six-case synthetic evaluation yielded three assessed development matches and three unassessed heldout cases; this is not evidence of representative model accuracy. See docs/examples/live-model-evaluation.json.

## Run locally

Requires Python 3.12+, uv, local Tesseract with English language data, and a TrueType font for image tests/smoke scripts (the current scripts use /usr/share/fonts/noto/NotoSans-Regular.ttf). Pillow is a Python dependency. From the repository root:

    uv sync --extra dev
    uv run uvicorn brandproof.main:create_app --factory --host 127.0.0.1 --port 8001 --no-access-log

Open http://127.0.0.1:8001/docs for interactive Swagger documentation.
Health: http://127.0.0.1:8001/api/v1/health
Contract: docs/openapi.json

For frontend development, run `npm ci` then `npm run dev` in `frontend/`; Vite proxies `/api` to port 8001. For the packaged app, run `npm run build` in `frontend/`, set `BRANDPROOF_FRONTEND_DIST=./frontend/dist`, and open port 8001 directly. Local HTTP requires `BRANDPROOF_DEMO_COOKIE_SECURE=false`; HTTPS hosting defaults to secure cookies.

On first startup, the app creates its initial tables and data/brandproof.db. SQLite is the exercised development database. SQLAlchemy and the psycopg driver provide a PostgreSQL configuration path, but PostgreSQL has NOT been tested. The current schema bootstrap is not a migration system; use a fresh database for this initial milestone and do not assume future upgrades can alter old tables automatically.

Optional configuration uses .env or environment variables; copy the names from .env.example. Never commit real secrets or data. BRANDPROOF_DATABASE_URL selects storage; BRANDPROOF_CORS_ORIGINS is a JSON list of exact authorised frontend origins. Configuration is read when creating the app.

## Tests and real HTTP smoke test

    uv run pytest -q
    uv run ruff check backend scripts
    uv run ruff format --check backend scripts
    uv run python scripts/smoke.py
    uv run python scripts/parser_smoke.py
    uv run python scripts/workflow_smoke.py

The smoke test requires a running API. It creates a new fictional sandbox, confirms four rules, finds four errors, verifies persisted findings, checks corrected copy has no exact findings, and verifies the historical run becomes stale after an edit. Clean copy returns a partial review when contextual AI is disabled. The additional workflow smoke exercises real poster OCR, comments, explicit suggestion acceptance, finding decisions, manual-supplement approval and stale readiness after a poster edit. Its reviewer actions are scripted synthetic tests, not human user feedback. The saved docs/examples/live-review.json is actual HTTP output from fictional inputs, not a fabricated model response. It contains no bearer tokens.

## What works

- Persistent, isolated demo workspaces and 24-hour bearer tokens for owner/creator/reviewer roles.
- Same-browser refresh recovery through a 24-hour HttpOnly, SameSite=Strict cookie. Recovery retains workspace/actor identity and does not extend expiry; role bearer tokens remain in memory. Secure cookies default on; local HTTP requires the explicit example override. Serve frontend and API under the same origin for browser recovery.
- Campaign creation/read/list with explicit publication date.
- Typed price/date/terminology/required-text sources and tone/claim-policy guidance for bounded contextual retrieval.
- Owner confirmation and immutable source version history. Revisions become pending until reconfirmed; the previous approved version remains historical, not active.
- Caption revisions with optimistic version conflicts.
- Exact price, ISO-date, whole-term and literal required-wording checks with actual text offsets and exact source/version evidence.
- Multiple prices/dates or conflicting approved main-price/main-date rules request clarification rather than an unsafe replacement. A finite scope grammar also abstains on cashback, deposits, registration deadlines, negation and unknown surrounding wording.
- Exact-check coverage is reported per rule. Missing/unsupported comparable expressions remain not_assessed; an available approved source alone cannot establish a completed comparison.
- Validity is assessed against the campaign publication date. Pending, expired and not-yet-valid sources are excluded and explicitly reported.
- Persisted review snapshots; historical results remain unchanged and expose is_current after content/source edits.
- Raw PNG/JPEG upload, canonical private PNG storage, real local OCR with coordinates/confidence and OCR-based exact poster findings.
- Consent-gated Groq/OpenRouter adapter, bounded approved-source keyword retrieval, strict span/citation validation and fail-closed errors. Provider contracts are tested offline; genuine Groq API examples are separately recorded.
- Persisted comments, explicit caption suggestion application, append-only finding decisions, creator review requests and eligible-reviewer approval/request-changes.
- Self-approval protection and revision-/request-/decision-bound readiness; explicit manual notes supplement incomplete checks without relabelling them automated successes.
- Findings grouped by category and the same approved source/version without losing caption/image locations.
- Persistent global/workspace provider budgets and concurrency admission, with no hidden retries or paid fallback.
- Manual interrupted-run recovery preserving snapshots and incomplete coverage.
- Uniform validation/auth/conflict errors and generated OpenAPI schemas.

## Important boundaries

This is a fictional-data local demo. Role switching is deliberately available to a sandbox visitor. It is NOT production authentication, verified human identity or independent human sign-off. Tokens are scoped to one workspace, stored as hashes and expire; private accounts are not implemented.

The local command is loopback-bound. The hosting package is intended for a fictional-data hackathon demo. Public session quotas, ingress limits, sandbox cleanup, production auth and migrations remain work; hosted PostgreSQL, HTTPS, restart and private-window acceptance are pending. Do not send confidential content.

Rules are bounded, not general semantic understanding. Only the campaign main price and main date are represented. Monetary syntax and date recognition are limited; dates currently require ISO YYYY-MM-DD and terminology/required wording use literal case-insensitive matching. The engine does not yet resolve arbitrary commercial conditions, all currencies, translations, date prose, negation, typography or claim truth. Review status and human readiness are separate. Incomplete automation remains visible even if a reviewer explicitly records a manual-supplement approval. BrandProof records decisions; it does not control publication on external platforms.

The configured local Groq model has been exercised, but the reduced synthetic evaluation is not a successful heldout benchmark: one heldout output was rejected and two provider requests were unavailable. Original evidence is retained without tuning/retries. External contextual calls default off and require server-side configuration plus explicit consent per review; only caption and selected approved text are sent. Missing configuration, refusal, invalid output, quota limits and timeouts stay incomplete. No embeddings or vector database are claimed. Logo comparison is a conservative template candidate requiring manual verification, not certified visual compliance. Typography, contrast/accessibility and contextual poster claims still need manual review. A process crash may leave an in-flight running review; stop all workers before using python -m brandproof.recovery --older-than-seconds 300. Recovery marks contextual coverage unavailable and never approves content. This is not a durable job queue.

## Deployment and operational evidence

See docs/FREE_HOSTING.md for the current setup and docs/BACKEND_DEPLOYMENT.md for operational boundaries. The multi-stage Dockerfile builds React and includes Python/Tesseract in one service. PostgreSQL stores image bytes as well as review records. A GitHub Actions workflow checks the image against PostgreSQL; inspect its actual result before treating it as verified. Local Docker build/runtime is unavailable because daemon access is denied. Remote deployment and persistence acceptance remain pending.

## Team handoff

See docs/FRONTEND_HANDOFF.md for role permissions, API contracts and stale-state behaviour. docs/task-status.md records current integration verification. Yogita owns the frontend; Rushab owns backend/AI/OCR/database. The current branch combines the latest pushed frontend/OCR/logo work with session recovery.

## Integrity and provenance

The project includes significant AI-assisted implementation and testing, including OpenAI models through Hermes Agent and Codex. Team members should review and understand the code they submit. Actual human contributions should be recorded separately from generated implementation.

Dependencies are declared in pyproject.toml; exact resolved versions are in uv.lock. Third-party libraries are reused components, not original team work. Track their licences and any later templates/services in the final submission. The team repository is https://github.com/YogitaKanwar/BrandProof; its current commit history is the publication record. A project licence has not yet been chosen.

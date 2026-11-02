# BrandProof

Evidence-first campaign review for **YOGI2KANWAR**, Codex 48. BrandProof compares saved captions and PNG/JPEG posters with owner-confirmed rules, preserves evidence/source versions, and records reasoned human decisions. Automated checks and human approval are separate.

**[Passwordless judge demo](https://brand-proof-tau.vercel.app/#/demo)** · [Repository](https://github.com/YogitaKanwar/BrandProof) · [Final QA](docs/ROUND3_FINAL_QA.md) · [Walkthrough](docs/JUDGE_FINAL_WALKTHROUGH.md)

The public Vercel frontend proxies `/api/*` to the Render Docker API and PostgreSQL database. On 2 November 2026 both providers reported source `e01f52b6ee02b6c85c480619cfc82cc486a56123`. Fetched main `d251daa` has the same application files; this final-hardening patch requires its own release approval. Historical reports retain their original scope.

Release candidate **5eac376** is published in [PR #14](https://github.com/YogitaKanwar/BrandProof/pull/14). Fresh Docker/PostgreSQL/legacy-upgrade and frontend CI passed. The [isolated full-stack preview](https://brandproof-round3-preview-20261102.onrender.com/#/demo) uses its own disposable SQLite data and passed the judge, combined improvements and error-recovery browser suites without the description reload workaround. Production remains unchanged; [review the release gate](docs/ROUND3_PRODUCTION_RELEASE_GATE_2026-11-02.md) before approval.

## Exactly three Round 3 improvements

1. **PDF import with traceable evidence.** Text-layer directives become pending candidates with exact page quotes, offsets and document digests. Explicit Owner confirmation creates immutable approved versions. Unsupported/scanned pages remain incomplete. Editing a rule clears a quotation that no longer supports it.
2. **Measured visual consistency and accessibility.** Supported flat backgrounds expose observed/approved colour, CIE76 deviation and tolerance. Reliable OCR-word samples expose foreground/background, measured contrast and the confirmed target. Description checks cover presence and literal OCR prices/dates. Uncertain measurements remain partial; this is not WCAG certification.
3. **Governance Insights.** Persisted findings/latest dispositions are grouped by category and exact source version, with campaign counts, reasons and saved-evidence links. Rates require five distinct reviewed campaign/content revisions for that group. Identical reruns contribute the latest snapshot only. Regulation groups never recommend weakening obligations.

Existing OCR/boxes, deterministic caption checks, conservative logo comparison, bounded English claim-risk/cited India advertising-risk review, revision conflicts, human approval/staleness and removal/Undo support this workflow. They are not additional Round 3 promises.

## Architecture and stack

React 19 / TypeScript / Vite → same-origin API proxy → Python / FastAPI / Pydantic / SQLAlchemy → SQLite locally or PostgreSQL in hosting/CI. Bounded pypdf worker handles PDFs; Pillow normalizes images; local Tesseract provides OCR. Optional Groq/OpenRouter is disabled by default and consent-gated.

API: [OpenAPI](docs/openapi.json) and [integration handoff](docs/FRONTEND_HANDOFF.md). Locked dependencies: `uv.lock`, `frontend/package-lock.json`.

## Requirements

- Python **3.12–3.14**; Docker/CI uses 3.12. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Node **24**, npm, Git.
- Tesseract with English language data on `PATH`.
- TrueType test font. Set `BRANDPROOF_TEST_FONT`; Noto Sans is the intended expanded measurement fixture.
- Docker/PostgreSQL are optional locally and required for the container/PostgreSQL CI recipe.

### Windows / PowerShell

Install Python, Node, uv and Tesseract through trusted installers. No PowerShell execution-policy change is needed: use `npm.cmd`.

```powershell
git clone https://github.com/YogitaKanwar/BrandProof.git
cd BrandProof
uv sync --locked --extra dev
Copy-Item .env.example .env
$env:PATH = 'C:\Program Files\Tesseract-OCR;' + $env:PATH
$env:BRANDPROOF_TEST_FONT = 'C:\Windows\Fonts\arial.ttf'
tesseract --version
tesseract --list-langs
cd frontend
npm.cmd ci --no-audit --no-fund
cd ..
uv run uvicorn brandproof.main:create_app --factory --host 127.0.0.1 --port 8001 --no-access-log
```

Arial runs ordinary fixtures; some conservative measurements may abstain. Use Noto Sans for the expanded feature smoke. Do not loosen thresholds for another font.

### Linux

Install Python, Node 24 and uv. On Debian/Ubuntu, install `tesseract-ocr tesseract-ocr-eng fonts-noto-core` through the package manager; other distributions provide equivalent packages.

```bash
git clone https://github.com/YogitaKanwar/BrandProof.git
cd BrandProof
uv sync --locked --extra dev
cp .env.example .env
export BRANDPROOF_TEST_FONT=/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf
tesseract --version
tesseract --list-langs
cd frontend
npm ci --no-audit --no-fund
cd ..
uv run uvicorn brandproof.main:create_app --factory --host 127.0.0.1 --port 8001 --no-access-log
```

Use the exact reviewed commit for acceptance. Open a second terminal for `cd frontend` then `npm run dev -- --host 127.0.0.1` (`npm.cmd` on Windows). Vite proxies API calls to port 8001. Open its printed URL. Swagger: `http://127.0.0.1:8001/docs`; health: `/api/v1/health`.

For one origin, build in `frontend` with `npm run build`, set `BRANDPROOF_FRONTEND_DIST=./frontend/dist`, then start the backend. Alternatively, `uv run python scripts/judge_demo_preview.py --port 8017` builds/serves loopback with its own `.cache/judge-demo-preview.db`, normal quotas and AI off.

## Environment

Copy `.env.example` locally. Never commit `.env`, passwords or tokens.

| Variable | Meaning / local value |
| --- | --- |
| `BRANDPROOF_DATABASE_URL` | `sqlite:///./data/brandproof.db`; PostgreSQL URLs use psycopg 3 |
| `BRANDPROOF_DEMO_COOKIE_SECURE` | `false` only on local HTTP; `true` for HTTPS |
| `BRANDPROOF_CORS_ORIGINS` | JSON array of exact frontend origins; no wildcard |
| `BRANDPROOF_FRONTEND_DIST` | Optional built UI directory |
| `BRANDPROOF_PUBLIC_ORIGIN` | Exact public origin behind a proxy; Render URL detected |
| `BRANDPROOF_EXTERNAL_AI_ENABLED` | `false` by default |
| `BRANDPROOF_AI_PROVIDER/MODEL/API_KEY` | Three separate optional server-only variables; see template |
| `BRANDPROOF_DEMO_SESSIONS_HOURLY_LIMIT` | Default 20 new sessions/hour |
| `BRANDPROOF_DEMO_OPERATIONS_HOURLY_LIMIT` | Default 300 expensive operations/hour |
| `BRANDPROOF_TEST_FONT` | Real test font path; not a product setting |

External AI also requires explicit `external_ai_consent: true` per review. Never expose provider secrets via Vite variables. Current public acceptance reports AI unavailable.

## Database and migrations

SQLite needs no server; startup creates `data`. Six ordered additive versions cover legacy tables, review leases, documents/evidence, descriptions, removals and advertising profiles. The older bootstrap-only README is obsolete.

For PostgreSQL, create a dedicated development database and set its private URL in the environment. `postgres://`, `postgresql://` and `postgresql+psycopg://` are supported. Tests must use isolated fictional databases. Startup locks migrations and rejects unknown history/schema drift.

`uv run python -m brandproof.migrations --check` is read-only: app construction does not enter startup lifespan. Before a reviewed upgrade, back up the actual database, stop old workers and inspect pending steps/recovery. Explicit `--apply` applies them; API startup also applies pending steps. Do not start a new executable against production as an informal probe. An older executable may reject newer history; deployment rollback is not proven schema recovery.

## Docker / PostgreSQL CI

```bash
docker build --tag brandproof:local .
docker run --rm -p 8000:8000 -e BRANDPROOF_DEMO_COOKIE_SECURE=false brandproof:local
```

This disposable SQLite container loses its database when removed. For durable development, supply a private URL for a dedicated PostgreSQL database reachable from the container. Never bake passwords into images. **No Compose file is supplied.**

`.github/workflows/hosting-check.yml` is the complete PostgreSQL 16 recipe: image build, database health, real caption/parser/OCR/approval/session workflows, legacy upgrade/idempotence, feature smoke, full backend suite and frontend lint/tests/build. `scripts/postgres_migration_probe.py` requires `BRANDPROOF_EPHEMERAL_CI=1` and must only target its disposable CI database. Current executed/unrun gates are in [final QA](docs/ROUND3_FINAL_QA.md).

## Tests

```bash
uv run pytest -q --tb=short
uv run ruff check backend scripts
uv run ruff format --check backend scripts
cd frontend
npm run lint
npm test
npm run build
```

With an isolated API on port 8001, run `npm run verify` in `frontend` for build/lint/unit and seven HTTP suites. Also run `node tests/removals-live.mjs` and `npm run test:pdf`. Override `BRANDPROOF_TEST_API_URL` for another port.

From the root, with the same API:

```bash
uv run python scripts/smoke.py --base-url http://127.0.0.1:8001 --output .cache/review.json
uv run python scripts/parser_smoke.py --base-url http://127.0.0.1:8001 --output .cache/parser.json
uv run python scripts/workflow_smoke.py --base-url http://127.0.0.1:8001 --output .cache/workflow.json
uv run python scripts/improvements_smoke.py --base-url http://127.0.0.1:8001
```

For genuine browser acceptance, start dedicated Chrome/Chromium with `--headless=new --remote-debugging-port=9223 --user-data-dir=<absolute disposable directory>`; never use a personal profile. Set `BRANDPROOF_TEST_URL=http://127.0.0.1:8017/#/demo` to match the local preview. Run `npm run test:demo`, `npm run test:improvements`, `npm run test:errors` in `frontend`. These use fresh browser contexts. The last is loopback-only and injects 503/timeouts. Only fictional screenshots/sanitized outcomes are saved. Historical `test:browser` uses its older Vite-preview setup; it is not substituted for the judge journeys.

Eighteen optional antialiasing cases use Linux Noto Sans/Serif/Mono paths and skip if unavailable; ordinary tests remain required. No code coverage percentage or representative OCR/model accuracy is claimed.

Generate the final report: `uv run --with reportlab python scripts/build_round3_report.py`. It reads [submission source](docs/ROUND3_SUBMISSION_CONTENT.md) and does not rewrite public guideline PDFs. Render/inspect the generated PDF before submission.

## Judge workflow

Demo → optional Workshop Campaign → References/PDF → Content → Results → Human Review → Governance Insights. Compact PDF: three rules; extended: seven. Both specify **INR 899**; flawed sample caption/poster use **INR 599**. Confirm inspected candidates explicitly; repeated imports create separate pending candidates and conflicting rules require reconciliation. Fixing a caption does not fix its poster. Source confirmation is not content approval. See [walkthrough](docs/JUDGE_FINAL_WALKTHROUGH.md).

## Troubleshooting / verified boundaries

- **Cold start, 502, timeout:** wait for health, then retry deliberately. After uncertain saves, reload saved state before resubmitting. Writes are not automatically replayed. Free-host availability is not guaranteed.
- **Refresh/access:** frontend/API must share an origin and cookies must be enabled. Use the secure-cookie override only on local HTTP. Recovery lasts up to 24 hours and cannot restore expired/revoked access. Reset revokes old roles and starts a separate workspace.
- **429:** respect demo quotas; **409:** reload/reconcile real revisions while preserving drafts.
- **No PDF candidates:** scans and unsupported narrative rules need manual transcription. Limits: 5 MiB / 30 pages; supported explicit directives only.
- **Partial OCR/measurements/logo:** small/rotated/noisy text, photos, gradients and bounded logo timeouts require human inspection. Do not interpret limited samples as complete conformity.
- **Interrupted review:** there is no durable job queue. Stop workers before the recovery procedure in `docs/BACKEND_DEPLOYMENT.md`; recovery never approves content.

Use **fictional, non-confidential content only**. Guest actors are synthetic roles, not verified identity, brand ownership or independent sign-off. Tokens stay in memory; a 24-hour HttpOnly/SameSite cookie supports recovery. Reset/logout revoke access but retain audit history. Removal hides a campaign, retains evidence and offers in-page Undo until reload. BrandProof records decisions; it does not control external publishing.

[Known limitations](docs/ROUND3_KNOWN_LIMITATIONS.md) disclose bounded parsing, unavailable contextual AI, limited visual/legal scope, hosting retention and operational gaps. No full WCAG/brand/legal certification or restorable production backup is claimed.

## Team and provenance

Team-supplied ownership: **Yogita Kanwar**, frontend/integration; **Rushab Ramhari Patil**, backend/OCR/AI/database. Significant implementation/testing used coding-assistant support. No hours, percentages or independent user feedback are inferred. Dependencies are reused libraries; no project licence has been selected.

Current records: [requirements matrix](docs/ROUND3_REQUIREMENTS_MATRIX.md), [final QA](docs/ROUND3_FINAL_QA.md), [configured runtime](docs/configured-backend-tests.md), [submission source](docs/ROUND3_SUBMISSION_CONTENT.md). Dated historical releases do not override current evidence.

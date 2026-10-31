# Round 3 local acceptance — 31 October 2026

Outcome: implemented and verified the local candidate for the three promised improvements and the bounded advertising-risk addition. This is not full manual-browser, PostgreSQL/container or public-deployment acceptance.

## Provenance and environment

- Branch: `feat/brandproof-improvements-20261028`; base commit `ca6dd8c20c0338656b523a1689693bded6413d7a` plus the current local diff. Existing design edits were preserved.
- Arch Linux; project Python 3.12 virtual environment with frozen dependencies. Real local Tesseract; Noto Sans, Serif and Mono available. CPU/OCR runs used `OMP_THREAD_LIMIT=2 OMP_NUM_THREADS=2`; no GPU or system package install.
- Isolated SQLite databases in pytest temporary directories. Real HTTP runtime: `127.0.0.1:8001`, database `/tmp/brandproof-round3/app.db`; frontend built and served by FastAPI. External AI explicitly disabled; no provider credentials read into reports.
- No merge, push, production database mutation, deployment, hosting charge or submission. User explicitly selected local release only because hosting ownership was unclear.

## Latest observed checks

Commands below ran via `agent-env`; npm commands ran in `frontend`.

| Check / command | Observed result |
| --- | --- |
| `.venv/bin/pytest -q --tb=short --junitxml=/tmp/brandproof-round3-final.xml` | **574 passed**, 50.32 seconds, 132 dependency deprecation warnings |
| `npm test` | **56 passed**, zero failures/skips |
| `npm run build` | Passed, 48 modules; includes new advertising profile and sample PDF |
| `npm run lint` | Passed |
| `.venv/bin/ruff check backend scripts` | Passed |
| `.venv/bin/ruff format --check backend scripts` | Passed |
| `git diff --check` | Passed |
| Saved `docs/openapi.json` compared with local `/openapi.json` | Equal |
| Local `/api/v1/health` | Database OK |
| Seven real-HTTP frontend suites | All passed: API/session/campaign, sources, reviews, posters, collaboration, approval, consent |
| `scripts/improvements_smoke.py --base-url http://127.0.0.1:8001` | Passed PDF pending evidence/confirmation, OCR boxes, draft controls, measured background/contrast, cited advertising risk, description revisions, readiness, Insights and human-decision path |
| `uv build --wheel --out-dir /tmp/brandproof-round3/wheel` | Passed; wheel contains legal pack, routes and migration metadata |
| Isolated import of unpacked wheel | Passed import, six-step fresh SQLite migration and legal API-contract check |
| Actual local process restart | Eight table digests/row counts unchanged: guideline documents, document evidence, source versions, reviews, approvals, finding decisions, descriptions and profiles |
| Fictional public PDF fixture through real extractor | Completed extraction, seven supported candidates, exact quotations, no candidate truncation |
| Rendered project PDF and fixture | All six report pages plus the one-page fixture visually inspected; updated report page 5 inspected again after adding test totals |

The real poster HTTP suite truthfully reported partial OCR on its own small fixture. Provider consent tests remained unavailable because external AI was disabled. Scripted exceptions/notes/approvals are labelled synthetic QA; they are not customer feedback or genuine substantiation.

Permanent credential-free evidence: `docs/evidence/round3-backend-tests.xml` and `docs/evidence/round3-restart-digests.json`. Temporary credentials remain only in live test-process memory; the old token-writing restart script was deliberately not used.

## Coverage that matters

### PDF promise

Existing flow plus new tests cover exact pending/confirmed quotation offsets, unchanged evidence on confirmation, modified-rule citation separation, mixed extractable/blank pages, scanned/blank unavailability, narrative extraction with zero candidates, malformed/encrypted/type/byte/page limits, bounded worker timeout, candidate/text limits, stale revision and owner permissions. Repeated imports retain separate pending candidates; UI warns about duplicates/conflicts. Extraction completion does not establish full rule coverage.

### Visual/accessibility promise

The original three antialiasing failures were reproduced and repaired. Real HTTP/Tesseract black/white and grey/white inputs now produce contrast measurements; grey produces a source-cited finding and real word boxes. Tests cover three installed fonts, three sizes, black/white and the chosen brand colours, mixed ink, interior shading/gradient/noise, confidence, exact thresholds, incomplete OCR and the 100-word cap. The 24px samples deliberately abstain because too little solid ink is available. Background target, observation, distance and tolerance remain inspectable.

Description tests cover missing, present, whitespace-empty, permission/revision conflicts, changed-poster specificity and historical text snapshots. A description edit stales an actual scripted approval receipt. Description presence and literal price/date coverage do not prove semantic quality or full accessibility.

### Governance promise

Tests cover five-snapshot minimum, rates below/at threshold, changed/reopened dispositions, identical rerun replacement, exclusion of older identical-run decisions, multiple campaigns, separate source versions, truncation, deleted-campaign visibility and workspace isolation. Regulatory groups show rule/pack identity, retain evidence/reasons and never mark regulation as an ambiguous brand guideline to weaken. Denominator and distinct reviewed snapshots are explicit in UI/API.

### Advertising-risk addition

Twenty-four tests in `test_legal.py` verify the source PDF checksum/quote, thirteen labelled content fixtures, applicability profiles, owner permissions, stale writes, isolation, required decision and manual notes, historical receipt scope, pack/profile staleness, source-review expiry, restart and real OCR citations. The thirteen content fixtures comprise six expected signals and seven negative controls; all matched their expected bounded outcomes. This is a small developer fixture set, not representative legal accuracy.

The final coaching instrument could not be retrieved from the official host. Its pack remains disabled. General 2022 substantiation review can still flag selection/placement promises, with partial sector coverage. Other jurisdictions/languages and sector-specific law remain unsupported. Existing claim-risk and legal reasons share one finding instead of producing duplicate alerts.

## Outstanding acceptance and decisions

1. **Manual UI acceptance:** browser security policy rejected binding the existing local tab. No alternate surface or browser execution workaround was attempted. The new legal UI has build/type/lint and API-contract evidence, not fresh manual desktop/mobile acceptance or new screenshots.
2. **PostgreSQL/container execution:** Docker socket access was denied and local PostgreSQL binaries were unavailable. No root or permission change was attempted. CI/probe definitions are prepared, but no current-commit remote CI success is claimed.
3. **Public release:** user requested local-only release. GitHub homepage metadata points to `https://brand-proof-tau.vercel.app`; homepage returned 200 and API health returned 429 during read-only inspection. GitHub exposed no deployment entries. No healthy public workflow or final deploy SHA was established.
4. **Hosting retention:** actual team-owned hosting account/database expiry is unconfirmed. Do not repeat the previously reported 27 November 2026 expiry as newly verified.
5. **Team contributions/final submission:** role mapping and submission copy are prepared; final personal contribution declarations and official submission belong to the team. Forms were not filled.

The warnings are Pillow `getdata()` and pypdf legacy configuration deprecations. No runtime failure was observed from them; future compatibility cleanup is separate. All-input correctness, live external model quality, legal certification and full WCAG compliance are not established.

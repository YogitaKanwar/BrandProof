# Final QA report — 2026-10-27

Verdict: NOT READY for verified Round 2 release. This audit is incomplete because the required runtime cannot execute; historical successes are not counted as current evidence.

## Environment and repository

Windows/PowerShell, Node 24.22.1. Tested integration/round2-backend-pr1 at 878e95c65fd99619c48251bac6ea86b5087d4ebb. Initial worktree clean. `git fetch --all --prune` succeeded after sandbox escalation. HEAD and origin/integration/round2-backend-pr1 have zero divergence. Remote main f3d53ee already contains this frontend checkpoint via PR #4; its tree has no difference from HEAD. No merge, reset, push or deployment performed. Other remote branches were fetched, not merged. Original plan.pdf preserved; scope read from plan.md.

## Fresh command results

| Command (frontend directory unless specified) | Outcome |
| --- | --- |
| npm.cmd run lint | PASS |
| npm.cmd run build | PASS, includes tsc -b and Vite |
| npm.cmd test | 33 passed, zero failed/skipped |
| npm.cmd run test:api | FAILED at demo-session creation, HTTP 404 |
| npm.cmd run test:sources | FAILED at demo-session creation, HTTP 404 |
| npm.cmd run test:reviews | FAILED at demo-session creation, HTTP 404 |
| npm.cmd run test:posters | FAILED at demo-session creation, HTTP 404 |
| npm.cmd run test:collaboration | FAILED at demo-session creation, HTTP 404 |
| npm.cmd run test:approval | FAILED at demo-session creation, HTTP 404 |
| npm.cmd run test:consent | FAILED at demo-session creation, HTTP 404 |
| npm.cmd run test:browser | BLOCKED, CDP :9223 connection refused; repeated after attempted dedicated headless Chrome launch |
| root: .\.venv\Scripts\python.exe -m pytest -q --junitxml=docs/qa-audit-results.xml | BLOCKED by Windows Application Control, both normal and escalated execution; no JUnit produced |
| npm.cmd run preview -- --host 127.0.0.1 | Started successfully at :4173 |

Counts: 33 unit tests passed; seven HTTP scripts failed before assertions could exercise journeys; browser suite and backend suite blocked. Lint/build are two additional passing checks. No fabricated aggregate test denominator for unexecuted suites. Backend Ruff and formatting blocked by unavailable executable runtime; uv/ruff not found on PATH. Frontend dependencies exist and build; backend dependency usability is unverified.

## API and configured-runtime diagnosis

GET http://127.0.0.1:8000/api/v1/health returned 404. GET /openapi.json returned 200 with title **SpeakEZ API** and zero /api/v1/ routes. This is a different service, not evidence of a BrandProof endpoint defect. Saved docs/openapi.json identifies BrandProof API with 21 paths. Do not stop or alter the unrelated service. Vite's default proxy target is http://127.0.0.1:8000; a correct BrandProof service and target are required.

No live Groq call was made. OCR, real PNG/JPEG extraction, boxes, contextual evidence, quota/outage handling and complete consented journey remain unverified. No configured-runtime acceptance was granted. See configured-backend-tests.md.

## Functional verification Y01–Y10

| Task | Fresh evidence and remaining scope |
| --- | --- |
| Y01 | Unit client/storage/error tests pass; connected creation, refresh and public access blocked |
| Y02 | Source validation/version/client unit tests pass; real confirmation/history blocked |
| Y03 | Caption/results/client unit tests pass; persisted reviews blocked |
| Y04 | Image signature/size unit tests pass; upload and canonical images blocked |
| Y05 | Envelope and Unicode offset unit tests pass; real findings/evidence blocked |
| Y06 | Integration correction/comment/decision script blocked |
| Y07 | Manual-check validation unit test passes; real roles, approvals and stale receipts blocked |
| Y08 | Coordinate scaling unit test passes; genuine OCR and browser overlays blocked |
| Y09 | 33 automated unit tests plus lint/build pass; browser/accessibility/user testing blocked |
| Y10 | Audit documentation updated; no public release URL or deployed judging verification |

## Security and UX boundaries

Targeted scans of tracked frontend files found no Groq/OpenAI key-shaped strings or private-key headers; these patterns are not a comprehensive secret audit. Storage references inspected are development draft paths; connected memory-only behavior is covered by unit tests. No dangerouslySetInnerHTML reference found in frontend/src. No provider secrets or session tokens were printed. Cross-workspace permissions, 401/403/409/422, prompt injection, persisted evidence validation, restart durability and concurrent edits are not freshly verified against BrandProof. Browser focus/keyboard, mobile/tablet overflow, overlay alignment and judge simulation remain unverified; no manual checks claimed passed.

## Defects, changes and next action

See BUG_TRACKER.md. No confirmed frontend implementation defect was established, so no speculative code fixes or backend edits were made. Documentation is the only source change. Restore an allowed Python runtime, run BrandProof on a free local port with isolated synthetic test storage, point frontend/tests to that actual API, and provide a working dedicated Chrome CDP session. Then rerun the complete real journey and negative/security/browser checks. Public HTTPS, persistence/restart, configured OCR/Groq and real usability acceptance remain required before release readiness can be established.

## Environment isolation follow-up — 2026-10-27 (supersedes counts above)

Fixed frontend Vite dev/preview default target and .env.example to http://127.0.0.1:8001. Client remains same-origin /api/v1 so credentials stay in headers. All seven HTTP scripts and browser concurrency probes now share tests/live-config.mjs; BRANDPROOF_TEST_API_URL overrides the default http://127.0.0.1:8001/api/v1. Each script checks /openapi.json for BrandProof API and its session route before creating any session. Three focused preflight regressions cover another service, expected contract and unreachable host.

Process inspection: Get-Process identified SpeakEZ's Python at C:/Users/Admin/AppData/Local/SpeakEZ/Python311/python.exe (PID 5568) and four Node processes. CIM process inspection was denied (HRESULT 0x80041003); listener inspection did not yield usable ownership data. HTTP independently confirmed :8000 returns SpeakEZ API, while :8001 is unreachable. SpeakEZ was neither terminated nor modified.

Attempted documented startup using the existing environment:

    .\.venv\Scripts\python.exe -m uvicorn brandproof.main:create_app --factory --host 127.0.0.1 --port 8001 --no-access-log

Exact error: `Program 'python.exe' failed to run: An Application Control policy has blocked this file`.

Confirmed OS cause: Microsoft-Windows-CodeIntegrity/Operational events 3033 and 3077 identify .venv/Scripts/python.exe and the cached CPython executable as failing Enterprise signing level requirements under policy {0283ac0f-fff1-49ae-ada1-8a933130cad6}. The log establishes policy rejection; why this organisation selected that policy or whether an exception is appropriate requires its administrator. No policy was disabled, executable relocated to evade enforcement, or SpeakEZ runtime reused.

Fresh verification after changes: lint PASS; TypeScript/production build PASS; 36 unit tests PASS, zero failures/skips. All seven API scripts were rerun and exit nonzero at the new preflight because :8001/openapi.json is unreachable; these are BLOCKED journeys, not seven application assertion failures. Campaign/source/caption/findings/poster/comment/decision/approval and OCR/Groq remain unexecuted. Browser journey remains blocked by backend preflight; earlier CDP failure is also unresolved. No backend logic changed. Vite dev reloads configuration; existing preview processes require restart to load the new target. No working connected-user link is claimed.

Alternative host: use the team's approved Linux development machine with Python 3.12+, uv, Tesseract English and the documented Noto font. From repo root run `uv sync --extra dev`, then `uv run uvicorn brandproof.main:create_app --factory --host 127.0.0.1 --port 8001 --no-access-log`. Keep it private; use an authorised SSH tunnel if testing from Windows, or run frontend and tests on that machine. Set BRANDPROOF_API_TARGET and BRANDPROOF_TEST_API_URL to the reachable private endpoint as needed. Verify OpenAPI before testing. A Windows alternative is an IT-approved Python 3.12+ distribution allowed by the current policy. Neither option requires bypassing security or public deployment.

Next action: obtain an approved runtime/host, start BrandProof :8001, restart frontend preview, and rerun verify plus genuine browser/configured-runtime acceptance. Verdict remains NOT READY for verified release.

## Latest requested retest — 2026-10-27

Fresh `npm.cmd run verify`: build PASS, lint PASS, 36 unit tests PASS (zero failed/skipped); test:api BLOCKED by ECONNREFUSED at :8001/openapi.json. Fail-fast verification did not execute the remaining six HTTP scripts or browser suite. Port :8000 still identifies SpeakEZ API and was left unchanged. Retried documented Uvicorn startup on :8001: `Program 'python.exe' failed to run: An Application Control policy has blocked this file`. No policy bypass or backend changes. Runtime-dependent tests remain blocked; next action is an approved Python runtime or private approved Linux test host. Release readiness remains NOT READY.


## Signed Python runtime retest ? 2026-10-27 (latest evidence)

Local application is running and core integration is verified; configured OCR/Groq and release acceptance remain incomplete. This section supersedes earlier runtime-blocked results, not their historical record.

- Official Python 3.14.10 at `C:/Users/Admin/AppData/Local/Programs/Python/Python314/python.exe`: Authenticode Valid; executes. Created `.venv-check` without altering `.venv`; its Python also has Valid signature and executes under current security policies.
- Installed repository dependencies using existing uv 0.13.5 with `UV_PROJECT_ENVIRONMENT=.venv-check`, workspace-local `UV_CACHE_DIR=.cache/uv`, `uv sync --extra dev --python <official interpreter> --locked`. Network access required sandbox escalation; installation succeeded without changing uv.lock. All 39 installed packages resolved for Python 3.14; runtime/import/API tests passed subject to the prerequisites below. This establishes exercised compatibility, not universal support.
- Backend runs in dedicated terminal session on 127.0.0.1:8001 with access logging disabled and separate synthetic SQLite storage `data/qa-python314-20261027.db`; original database preserved. Health returns status/database ok; OpenAPI title is BrandProof API; /docs returns 200. SpeakEZ still identifies itself on :8000 and was untouched.
- Frontend development server runs at http://127.0.0.1:5174/; production preview at http://127.0.0.1:4173/. Both returned HTTP 200 and proxy health to BrandProof successfully. Existing :5173 was occupied and its proxy returned 404, so it is not the verified URL for this run. Vite configuration already defaults to backend :8001.

| Fresh check | Actual outcome |
| --- | --- |
| Frontend lint / TypeScript + Vite build | PASS |
| Frontend unit tests | 36 passed, 0 failed/skipped |
| Seven real API scripts | All PASS: session/campaign, sources, reviews, posters, collaboration, approval, consent |
| Approved INR 499 versus caption INR 599 | Genuine contradicted finding with approved source v2 evidence; correction/history/staleness verified |
| PNG and additional synthetic JPEG uploads | PASS upload/private retrieval/revision guards; OCR unavailable, tool_missing |
| Connected browser suite | PASS all 22 reported groups, Sources ? Content ? Findings ? Human Review; desktop/320px/390px, comments, corrections, manual-note/role guards, stale receipts, conflicts, refresh and outage handling; no uncaught JS errors |
| Backend pytest | 310 passed, 21 failed, 1 collection error; 86.78s using --continue-on-collection-errors |
| Backend Ruff lint and format | PASS; 68 files already formatted |

Backend test failures and collection error report `OSError: cannot open resource` for hardcoded `/usr/share/fonts/noto/NotoSans-Regular.ttf`; local Tesseract is also absent. Initial normal pytest stopped at collection; the continued run above exposes remaining results. No test or backend code was changed to hide failures. Detailed local evidence: `.cache/backend-python314-full.log` and `.cache/qa-python314-full.xml` (ignored runtime artifacts).

Groq/provider is none, model/key are not configured, and external AI is disabled. Consent false and explicit true both correctly preserve incomplete contextual status; no live provider call or OCR extraction success is claimed. No secrets or bearer tokens printed or stored by test clients; backend retains documented token hashes. Browser refresh deliberately ends in-memory demo access while preserving server data; this is tested behavior, not resumable authentication.

Chrome CDP initially refused :9223 inside the sandbox; a dedicated hidden Chrome process launched with approved escalation made the real connected suite executable (`BRANDPROOF_TEST_BACKEND=1 npm.cmd run test:browser`). No public deployment, push, merge, backend modifications or security-policy changes performed. `.venv-check/` and `.cache/` are ignored to protect local environment artifacts.

Remaining: install/approve local Tesseract English and provide the documented font runtime (or run the unchanged suite on approved Linux); separately configure server-side Groq and obtain explicit per-review consent before a live check. Real OCR evidence/boxes, configured-provider acceptance, service restart durability, public hosting and human usability acceptance remain unverified. See configured-backend-tests.md. Running terminals must remain open to keep local URLs available.


## Completion Sprint 1 - OCR/Groq/backend diagnosis (2026-10-27)

Read current scope, handoff, QA reports and OCR/contextual implementation before changes. No backend production code or test edits, database deletion, security bypass, push, merge or deployment.

### OCR installation and actual extraction

User explicitly approved Tesseract installation. Installed the UB Mannheim 64-bit build 5.5.3.20260724 linked from Tesseract's installation documentation: https://tesseract-ocr.github.io/tessdoc/Installation and https://github.com/UB-Mannheim/tesseract/wiki . Installer completed with exit 0. Installed at `C:/Program Files/Tesseract-OCR/tesseract.exe`; `--version` works and `--list-langs` lists eng and osd. English traineddata exists (4,113,088 bytes). Authenticode returns UnknownError with a certificate-validity-period error for installer/executable; normal Windows execution allowed both. No security policy or trust settings changed. Installer SHA256: BEE9E3434BD94FD65387D9BE28CD467A41F61B1275383B55B0F59A1331270AE4. winget itself could not execute (file cannot be accessed); downloaded installer from the linked release instead.

Using an actual Windows Arial font to generate separate synthetic PNG and JPEG probes, direct Tesseract CLI returned exit 0 and recognised `Workshop INR 599` in both formats. Parsing genuine TSV through unchanged BrandProof parse_tsv returned completed with real boxes: Workshop (36,72,283,59), INR (346,72,103,46), 599 (471,72,101,47), on 1100x240 image. These are direct-tool diagnostic results, not successful end-to-end application OCR.

Confirmed production portability defect: backend/brandproof/ocr.py registers subprocess stdin/stdout/stderr pipes with selectors.DefaultSelector. Windows selectors support sockets, not pipes (https://docs.python.org/3.14/library/selectors.html). A local subprocess-pipe probe reproduced WinError 10038 with socket initialisation; a direct production runner call reproduced WinError 10093 without initialisation. extract_text catches OSError and returns unavailable/extraction_failed. Tesseract installation alone cannot resolve this.

Actual application-route probes with Tesseract on process PATH, using FastAPI TestClient, separate `.cache/sprint1-ocr-api.db`, approved INR 499 source and real INR 599 PNG/JPEG uploads: upload succeeded, OCR unavailable/extraction_failed, persisted reviews partial with zero poster findings. No contradiction/coordinates invented. Frontend end-to-end highlight alignment remains BLOCKED because the application produces no genuine OCR boxes. Existing percentage-scaling unit test passes but is not image alignment acceptance. The already-running :8001 process retains its earlier PATH and its HTTP poster test still reports tool_missing; it must be restarted with the Tesseract directory on PATH after backend compatibility is addressed. No dedicated OCR executable setting exists; runner invokes `tesseract` from PATH.

Rushab review required: implement a Windows-compatible bounded subprocess reader while preserving timeout, stdout/stderr caps and cleanup. Do not replace bounded draining with unbounded output capture in production. Verify on both Windows and Linux with real OCR afterward. This sprint does not authorise us to implement backend changes.

### Font and prior failure grouping

The hardcoded `/usr/share/fonts/noto/NotoSans-Regular.ttf` is in backend/tests/test_ocr.py and scripts/workflow_smoke.py. It generates synthetic image fixtures; the production upload/OCR path does not need that font. Windows Arial can render probe images; existing suite remains unchanged. Missing Noto/Linux path is a test portability/prerequisite issue, not a production text-extraction font dependency.

Fresh full unchanged suite before installation: **310 passed, 21 failed, 1 collection error**, 116.96s, zero skipped. Parsed JUnit identifies **20 failures** with OSError/cannot open resource (font), **one failure** test_blank_image_is_unreadable_not_success (expected partial/unreadable, got unavailable because Tesseract absent), and **one collection error** test_posters.py from import-time poster_bytes rendering with missing font. This corrects earlier broad statements that all 21 failures were font errors. The newly confirmed Windows subprocess defect is an additional application issue that was masked by missing prerequisites.

Evidence: `.cache/backend-sprint1.log`, `.cache/qa-sprint1.xml`; post-install rerun evidence is `.cache/backend-sprint1-ocr-installed.log`, `.cache/qa-sprint1-ocr-installed.xml`. Do not classify font failures as corrected or skip them silently. Rushab should review a portable fixture-font configuration or run with the documented Linux font runtime, then rerun all collected tests including the previously blocked poster module.

### Groq

Inspected existing adapter, consent gate, evidence/span validation and persisted review implementation. Settings resolve provider=none, model absent, key absent, external AI disabled; no root .env. Checked BRANDPROOF_AI_API_KEY and BRANDPROOF_AI_MODEL existence in Process/User/Machine scopes without printing values: all absent. No key requested in chat, no secret printed, no live external call made. Existing documented model remains openai/gpt-oss-120b; not replaced with another model. Explicitly consented real HTTP review correctly reports unavailable while unconfigured; this is an error-path test, not Groq acceptance.

User action: set BRANDPROOF_AI_PROVIDER=groq, BRANDPROOF_AI_MODEL=openai/gpt-oss-120b, BRANDPROOF_AI_API_KEY=<local secret>, BRANDPROOF_EXTERNAL_AI_ENABLED=true in ignored root .env, then notify us. Never paste key into chat. Once configured, reload backend settings and run exactly one authorised synthetic consented contextual review; verify actual validated evidence and persisted response, preserving partial/refusal/error states without retries. Until then Groq working status is BLOCKED. Offline provider tests do not count as a live Groq response.

### Frontend regression and remaining scope

Fresh frontend lint/build and all 36 unit tests pass. Real HTTP poster upload/private retrieval/revision/error checks pass with truthful OCR unavailable status. Refresh recovery and deployment remain outside completed scope; no redesign. Existing prior connected browser journey passed, but real OCR highlight acceptance remains incomplete. All installation artifacts/probe databases stay ignored under .cache; project databases and environments preserved.


### Post-install full-suite result - 2026-10-27

With `C:/Program Files/Tesseract-OCR` explicitly on process PATH, the unchanged full suite completed: **310 passed, 21 failed, 1 collection error, 0 skipped**, 119.76s. The 20 font-rendering failures and import-time collection error remain. Blank-image OCR still fails because production Windows pipe selection returns unavailable/extraction_failed despite a working engine; this is now the confirmed runner compatibility defect, not missing Tesseract. Evidence: `.cache/backend-sprint1-ocr-installed.log` and `.cache/qa-sprint1-ocr-installed.xml`. No further reruns can resolve unchanged prerequisites/code; Rushab review is required. Latest local health and frontend HTTP checks remain ok/200. No Groq credentials arrived during this run; genuine provider call remains blocked.


## Completion Sprint 1 fixes and live acceptance - 2026-10-27 (latest evidence)

Local OCR and one live Groq review now WORK. This supersedes the preceding blocked OCR/Groq status. User explicitly authorised focused backend fixes for Rushab review; no existing backend edits were overwritten. No push, merge, deployment, security-policy change, credential logging or environment/database deletion.

### Changes

- backend/brandproof/ocr.py: replace unsupported Windows subprocess-pipe selectors with three concurrent workers, bounded reads and overall deadline. Preserve stderr/stdout limits, shell=False, child kill/reap on error, memory-only image transport, existing TSV parser and canonical image coordinates.
- backend/tests/test_ocr.py and scripts/workflow_smoke.py: portable installed font candidates plus BRANDPROOF_TEST_FONT override. No redistributed font files, deleted assertions or blind skips.
- backend/tests/test_ocr_process.py: three new real-pipe regressions for stdout/stderr overflow and blocked-input timeout; child cleanup asserted.
- frontend/tests/browser-smoke.mjs: opt-in real OCR box alignment against API-returned coordinates at 1440/390/320px. No UI redesign.

### Genuine OCR acceptance

Restarted BrandProof on 127.0.0.1:8001 with Tesseract on process PATH, original synthetic QA database preserved. Real HTTP PNG and JPEG posters containing Workshop INR 599 both extracted successfully and contradicted confirmed INR 499 source v2. Actual boxes, confidence around 0.958 and source quotes persisted unchanged on GET. Existing fixture poster is honestly partial/low_confidence, not relabelled clean.

Connected browser journey passed all 23 reported groups, including genuine poster contradiction and box geometry matching rendered image within 1.5 CSS pixels at desktop/390/320px. Inspected the 390px screenshot: INR and price are highlighted on the actual image. Screenshots remain local under frontend/node_modules/.cache/brandproof-screenshots/real-ocr-overlay-*.png. Empty-image, PNG/JPEG and poster revision/history cases pass the relevant backend tests. No fabricated OCR or provider output.

### Exactly one genuine Groq request

Root ignored .env exists. Settings load groq, existing openai/gpt-oss-120b model, key-present=true, external-enabled=true without exposing credentials. Restarted backend with these settings. Created approved synthetic claim policy explicitly stating job placement is not guaranteed; caption claimed guaranteed placement. First review with consent false returned contextual unavailable. Exactly one consent-true provider request completed: contextual status completed, one validated contradicted claim finding, rejected_finding_count=0, correct exact caption span and approved source v2 quote. Overall review remained partial; no human approval or universal model accuracy claimed.

Retrieved review checks/findings match the original response. Read-only database verification after process restart also matches, accounting for the API's default empty rules field; total ai_admissions rows in this synthetic database is exactly 1. No retries or second paid request. Review ID 3f976f91-bce0-4321-9569-3350cd2644a5. Sanitised single-attempt evidence: .cache/groq-single-completion-attempt.json; real PNG/JPEG findings: .cache/poster-completion-evidence.json. No bearer tokens saved in these artifacts.

Automated seven-script/browser regressions temporarily set external AI disabled in the server process, preserving actual partial/error states without extra provider calls. Afterwards restored server from .env with Groq enabled and Tesseract PATH; optional UI consent remains off by default. Backend remains on 8001; SpeakEZ untouched.

### Regression evidence and limits

First full restored backend run: 358 passed, zero failures/errors; 41 targeted OCR/poster tests passed; three new subprocess safety tests passed separately. Final combined suite result appended below. Frontend lint, TypeScript/Vite build, all 36 unit tests, all seven real API scripts and connected browser/real-overlay checks pass. Backend Ruff lint and format pass. The prior 20 font failures, one collection error and blank-image runner failure are resolved on this Windows runtime.

Focused review artifacts: docs/RUSHAB_OCR_REVIEW.md and docs/rushab-ocr-review.patch (backend/fixture/smoke files only, including new test file). Rushab should review cancellation/bounds/cleanup and run Linux CI; Linux execution was not available here. Same-session refresh recovery, production authentication, public deployment, broader provider/real-world accuracy evaluation and real human usability acceptance remain open. Local success is not production release approval.


### Final combined verification - 2026-10-27

**Backend: 361 passed, 0 failed, 0 errors, 0 skipped in 132.09s.** Full suite includes the three new real-pipe regressions. Evidence: .cache/backend-completion-final.log and .cache/qa-completion-final.xml. Ruff lint/format pass. Frontend lint/build/36 tests, all seven real HTTP scripts and connected browser 23 groups pass. Actual PNG/JPEG INR 499-versus-599 poster contradictions and desktop/mobile genuine-box alignment verified. Exactly one Groq provider admission, successful validated/persisted result, no retry. Backend is restored with .env Groq enabled and Tesseract PATH on 127.0.0.1:8001; health/database ok, docs 200, frontend :5174 returns 200. SpeakEZ still identifies on :8000 unchanged.

No immediate user setup action is needed. Rushab review and Linux CI remain required before merging the focused backend diff; same-workspace refresh recovery, deployment, broader model evaluation and human usability acceptance remain separate. Nothing pushed, merged or deployed.


## Full application retest requested before poster upload - 2026-10-27

Fresh unchanged full backend suite: 361 passed, 0 failed/errors/skipped, 120.05s (.cache/backend-full-retest.log and .cache/qa-full-retest.xml). Ruff lint/format pass. Frontend lint/build, 36 unit tests, all seven genuine API scripts and all 23 connected browser groups pass, including real OCR poster contradiction and desktop/mobile box alignment. Fixture OCR low_confidence stays partial. Automated provider calls disabled only during HTTP/browser regression; final server restored with existing Groq .env settings and Tesseract PATH. Provider admission count remains exactly 1; no additional live Groq call made. Frontend :5174 and backend :8001/docs return 200, direct/proxied health status/database ok, API identity BrandProof verified. Synthetic sample poster available locally at .cache/sample-poster-inr599.png; confirm INR 499 source, upload sample, then run review for supported contradiction. Session refresh recovery and deployment remain open. No push/merge/deploy or SpeakEZ changes.


## Image selection / grey Run review flow fixed - 2026-10-27

User repeatedly reported that adding an image disabled review. Confirmed UI flow: pending image preview set posterPending and disabled the only primary review action, requiring a separate upload step. Updated frontend so selected image offers explicit Upload poster and run review. On click it awaits real revision-checked upload/canonical OCR, refreshes campaign, then reviews the acknowledged saved revision; upload/conflict failure aborts review and preserves the selected image. Caption edits still require save; concurrent writes still return 409 and require explicit reconciliation. No backend changes, auto-approval or silent AI consent.

Files: frontend/src/ContentWorkspace.tsx, LiveCaption.tsx, LivePoster.tsx; frontend/tests/browser-smoke.mjs. Fresh lint/build and 36 unit tests pass. Connected browser 24 groups pass: selected poster plus caption save, combined-action 409 with no created run, explicit reconciliation/retry, real OCR boxes at desktop/mobile, and poster-only PNG then JPEG reviews against confirmed INR 499 with actual INR 599 contradictions. Provider admission count remains 1 (no new Groq calls). Original backend 361-pass result remains from preceding full run; backend was unchanged in this fix. No push/merge/deploy; current frontend :5174 serves the change without full-page refresh.


## Brand-logo comparison feature - 2026-10-27

User explicitly requested this new feature. Added private owner-only reference upload/confirmation, immutable versions/history, revision-bound snapshot provenance, conservative bounded local template comparison, and frontend reference upload/preview plus possible-mismatch findings. Confirmed logo replacement invalidates prior review currency. Pending references are excluded; uncertain matches never approve content. No provider calls or new dependencies. Empty findings/close candidates do not prove a correct logo; tiny changes, backgrounds, rotations and small logos require human inspection. See LOGO_COMPARISON_REVIEW.md for exact supported scope, new routes and focused backend patch for Rushab.

Six focused backend tests pass; first full suite 366 passed before the additional immutable-snapshot test. Frontend lint/build/36 unit tests pass. Connected browser with BRANDPROOF_TEST_BACKEND=1 BRANDPROOF_TEST_OCR=1 BRANDPROOF_TEST_LOGO=1 passes all 25 groups, including actual logo reference upload/owner confirmation and real PNG/JPEG reviews that show possible mismatch and the historical reference image. Matching synthetic example scores 0.9745 and remains partial; altered example scores 0.7329 and warns. These are raw similarities, not calibrated confidence or representative accuracy.

Final combined suite result follows. Runtime :8001 reloaded; UI :5174 contains Brand logo under Brand Information. No reset, existing-data deletion, external notification, extra Groq call, push/merge or deployment. Linux/real-logo quality acceptance and Rushab review remain outstanding.


### Final logo-feature verification - 2026-10-27

Full combined backend suite: **367 passed, 0 failed/errors/skipped**, 167.57s (.cache/backend-logo-combined.log / .cache/qa-logo-combined.xml). Backend Ruff lint/format and frontend lint/build/36 tests pass. Connected browser 25 groups pass with owner logo confirmation, real missing-logo warning, historical image and PNG/JPEG poster journey. Actual HTTP matching-versus-altered sample: matching candidate 0.9745/no warning; altered candidate 0.7329/one needs_clarification warning; both remain partial and persisted. Evidence .cache/logo-live-evidence.json; raw score is not calibrated confidence. Provider admissions remain exactly one from earlier Groq acceptance; no extra provider calls. Frontend :5174 returns 200 and backend health/database ok after feature restart. Focused new backend patch: rushab-logo-review.patch; scope/limits and Rushab review notes: LOGO_COMPARISON_REVIEW.md. No push/merge/deploy. Small alterations, rotations and complex/low-resolution backgrounds remain manual-review scope.


## Full-poster logo reference false reassurance fixed - 2026-10-27

User reported a visible logo mismatch despite similar-candidate result. Inspected latest saved reference/poster locally: reference was an entire 800x400 workshop poster (logo plus separated caption), and comparison reduced the whole foreground layout to 16x16. Changed small logo was overwhelmed by matching layout; score 0.9757 wrongly suppressed mismatch warning. Confirmed defect, not user approval or absence of an alteration.

Added conservative reference-suitability guard: widely separated artwork/text blocks produce not_assessed with an explicit logo-reference-needs-cropping finding, including on persisted real API review. Such references are no longer presented as similar candidates. This heuristic may also abstain on legitimate separated brand lockups; owner must provide a tightly cropped logo and inspect fine details. It does not solve all subtle-logo detection limits or silently approve/replace the user's reference. Existing user review remains historical.

Fresh verification: seven focused logo tests pass (new full-reference regression), backend Ruff pass, frontend lint/build pass, connected browser 25 groups pass, and genuine API reference/poster reproduction persists the new clarification finding. No additional Groq call; full 367-test result above predates this guard and is not claimed as a fresh full-suite rerun. Local server reloaded. User next step: upload logo-only reference, explicitly confirm and run a new review. No push/merge/deploy.


## GitHub publication verification - 2026-10-27

Final pre-push full backend suite: **368 passed, 0 failed/errors/skipped**, 136.94s. Backend Ruff lint/format pass; frontend lint/build and 36 tests pass. Latest connected browser check passed 25 groups; seven live API scripts passed during completion sprint. No additional provider call was made. Secrets-aware staged-content scan found no local credential match or credential-shaped value. No environment files, database/image storage, caches, binaries, screenshots or local patch exports included. User authorised normal push of integration/round2-backend-pr1; main is not merged or deployed. Teammate message and work list are in TEAM_UPDATE.md. Backend and logo limits remain explicitly documented for Rushab review.

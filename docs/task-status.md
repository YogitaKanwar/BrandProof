# BrandProof task status

## Recent Reviews deletion and judging answers - 28 October

- Added owner-authorized connected Delete/Cancel/Confirm and Undo on the feature branch, retaining audit records. Lists/insights and ordinary access exclude removed campaigns; running reviews and stale revisions are blocked. Exact deletion IDs guard Undo against later deletions. Local-draft deletion retained.
- Additive schema step `0005_review_removal`; full backend 516 passed, frontend 51 passed, lint/format/build, seven HTTP suites, 26 existing browser groups and genuine delete/Undo/reload journey passed. API contract updated. Original local documentation additions preserved.
- Judge-facing answers list only verified public `36cb8ae` features. Exactly three proposed Round 3 deliveries: PDF guideline import/evidence, measured visual/accessibility checks, and governance insights. See [copy-ready answers](judges-submission-2026-10-28.md). Connected deletion is not deployed; prior CI/review/migration/deployment gates remain.

Updated: 2026-10-28. Current branch: `feat/brandproof-improvements-20261028`.

## Authorized improvements completed locally - 28 October

- Feature branch `feat/brandproof-improvements-20261028` from production `36cb8ae`; understandable stage commits, original documentation backups/edits retained. No unreviewed production deployment or main/integration merge.
- Implemented expanded fictional demo/readiness, contextual caption + high-confidence OCR provenance, unverified draft candidates, bounded PDF pending/page evidence, scoped palette/contrast and poster-specific alt text, governance/sample guards, additive migrations and leased/fenced automatic recovery.
- Final local checks: 514 backend tests, 50 frontend tests, lint/format/build, seven HTTP suites, 26 existing browser groups and the full new-feature HTTP/browser journey passed. Backend wheel built and independently started with packaged migrations; running/saved OpenAPI equal.
- Production H probe on unchanged `36cb8ae`: 5,155,064-byte PNG 200/10.32s; logo review 201/3.994s but truthful time-limit/manual result. First proxied health 502 then 200 after warming. Render PostgreSQL remains Free/available, expires 27 November; quotas/provider enablement untouched.
- Gates: fresh Docker/PostgreSQL CI, reviewed backup/migration/release approval, optional private provider configuration/consented acceptance, cold-start/retention and representative real-user/image evaluation. No larger quota, paid plan or provider switch assumed.
- Full mapping/tests/release instructions: [final report](improvements-final-report.md), [implementation](improvements-implementation.md), [PR text](improvements-pr.md). User chose manual PR opening; branch/PR text are prepared.

## Strict-zero-budget deployment execution - 28 October

- After user completed repository access, Render Free Docker service creation succeeded: srv-dbgtr7nb9u1s73981s70, assigned https://brandproof-api-slz9.onrender.com, initial deployment dep-dbgtr7vb9u1s73981st0. Explicit free compute, one instance, Singapore, automatic deploys off. Database is now available on its Free plan. No public health acceptance yet; private database URL and dashboard health-check path remain required. Database URL is explicitly empty pending private setup, preventing SQLite fallback.
- Vercel create_project retry still returned 403; asked user for dashboard project creation in the verified Hobby team. Added frontend/vercel.json with the actual Render hostname and relative API proxy; UI unchanged. Asked user to configure Render database URL and health path privately. No database credentials requested in chat.

- User confirmed Render workspace Hobby/free, no attached payment method and no card required. Created PostgreSQL 16 brandproof-db on explicit free plan in Singapore: dpg-dbgtpn5g1s2s73c9tg60-a, expires 2026-11-27T11:30:36.905505Z, disk autoscaling off. Internal connection URL is not exposed by MCP and must be configured privately in Render after a web service exists.
- Free Docker web creation attempted with explicit integration branch, autoDeploy no, secure cookies and external AI disabled. Render returned HTTP 400: repository URL invalid or unfetchable. No service created; private GitHub repository authorization is required before retry. No temporary SQLite deployment was accepted.
- Vercel team authorization still requires browser action; supplied a new 10-minute consent link. Public URLs/live acceptance remain pending. No paid resources or upgrades selected.

- User authorized normal integration-branch push and only strictly free public resources. Fresh scan covered all 10 unpublished trees / 327 unique blobs: no detected credential matches or sensitive tracked paths. Pushed and independently verified GitHub SHA 5a8aeb1705382c9b4d892b90d04d04c5d017216d. Main unchanged; release tests remain those recorded below.
- Paid hosting proposal is superseded by the user's strict USD 0 budget. Target: Render Free web + Free PostgreSQL 16 (1 GB, 30-day expiry), Vercel Hobby, Groq free usage only after private configuration. No card, paid trial, workspace upgrade or usage overage authorized.
- Render billing is a required manual gate: MCP exposes no billing/payment-method/spend-limit reader. Official Free documentation says bandwidth/build overages can bill when a payment method exists; without one, services/builds are suspended instead. Asked user to verify Hobby/free workspace, no attached payment method and no card requirement before creation. No Render resource created.
- Vercel active account reports Hobby, no trial, excess data-cache billing false. create_project in the verified team returned HTTP 403 / no permission to create project; list_projects still empty. CLI executable and authentication files absent. Team authorization path checked; no frontend deployed or public URL claimed.
- Public application/OCR/Groq/persistence checks have not run because cloud deployment is blocked by billing verification and Vercel creation authorization. Local application/UI/backend source unchanged.

## Release preparation and verified hosting connections - 28 October

- Read-only MCP verified Render BrandProof and Vercel yogitakanwar's projects, both identifying yogi2kanwar@gmail.com. No existing services/databases/projects returned. No resources created or deployment performed.
- Fresh fetch confirms remote 627be7a and local 8e93438, nine ahead/zero behind. Both cdda60f backend PR1 and a93f782 frontend checkpoints remain ancestors; main remains b73d535. All nine commit trees scanned (323 unique blobs), plus current 198 tracked files: no detected credential matches or sensitive tracked paths. Local .env, environments, databases and caches are ignored and outside Docker's allowlisted context.
- Fresh release checks: 445 backend tests pass in 145.14 seconds; Ruff lint/format (70 files), frontend build/lint, 47 unit tests, seven genuine HTTP suites, real Tesseract workflow and 26 browser groups pass. External AI disabled. Initial HTTP attempt had no server; initial browser attempt lacked exact local preview CORS origin. Both rerun successfully against isolated data/release-qa-20261028.db with exact localhost origins, no product/backend edits.
- Preserved and verified the pre-existing browser clear-cookie/reload test fix. Preparing a local checkpoint containing that fix and deployment/acceptance documentation only; normal branch push requires user approval. Docker CLI unavailable on current PATH; earlier Linux Docker/PostgreSQL CI is historical evidence, not a fresh container run.
- Proposed resources and alternatives are in VERCEL_RENDER_DEPLOYMENT.md: Singapore PostgreSQL 16 (0.1c-256mb, 1 GB) and Docker API (0.5c-512mb), Vercel Hobby static frontend/global CDN. Base USD 13.30/month before taxes/usage/AI; no workspace upgrade. Resource/public-deployment approval and private database/Groq configuration remain pending. Health-check dashboard setting and hostname-dependent rewrite are explicit remaining steps.

## Fresh GitHub integration and deployment gate - 28 October

- Fetched all refs. Integration initially matched its remote at 627be7a; origin/main contained merge commits with the same tree. Newly fetched fix/demo-session-resume had nine further commits through 8e93438. After explicit user approval for backend/session/hosting integration, fast-forwarded the integration branch to 8e93438. Main and a93f782 preserved. No push or deployment. The existing frontend/.env.example port edit is preserved in named stash pre-pull-env-example-20261028; incoming file already includes it. Integration now matches fetched fix/demo-session-resume and is nine commits ahead of its own remote.
- Fresh current-checkout checks: backend 445 passed (148.83s), Ruff lint/format pass (70 files); frontend build/lint and 47 unit tests pass; seven genuine HTTP scripts and 26 connected browser groups pass. Real PNG/JPEG OCR, responsive boxes, owner logo workflow, roles/receipts/staleness and same-campaign reload recovery exercised. External AI disabled; no provider call. Initial pre-pull backend run lacked Tesseract PATH (357 pass/11 fail); corrected current run supersedes that result.
- Browser-test setup fix: clearing cookies followed by hash navigation retains memory state, so explicitly reload before asserting disconnected entry. No product/backend changes made locally.
- Verified local runtime: API 127.0.0.1:8001, production preview 127.0.0.1:4173; separate fictional data/deployment-qa-20261028.db. Secure-cookie disabled only for local HTTP process. Hosted settings remain secure.
- Vercel/Render preparation: see VERCEL_RENDER_DEPLOYMENT.md for frontend root/build, relative API rewrite, exact origins and PostgreSQL durability. Actual Render hostname required before generating deployable Vercel config. Relevant plugins discovered but not connected; team-owned account connections requested. Fetched notes flag an unrelated Vercel account: do not use it.
- Remaining: connect intended accounts, privately configure durable PostgreSQL, deploy Render/Vercel, then verify hosted HTTPS, cookie/private-image proxy, upload/review latency and restart/redeploy/sleep durability. No cloud resources or paid resources created; no hosted acceptance claimed.

## Combined app and free hosting preparation - 28 October

- Preserved the local session work as f7491d4 and merged origin/main 833c6ff (including Yogita's OCR, combined upload/review and owner-confirmed logo work) into this feature branch as 27dffb8. Main was not changed.
- Added optional serving of the built React app from FastAPI, a multi-stage complete-app Dockerfile, automatic psycopg 3 selection for ordinary hosted PostgreSQL URLs, and a Render Free Blueprint with external Neon storage, secure same-origin cookies and external AI disabled. No cloud resources or public project URL exist.
- Fresh combined backend suite: **445 passed, 0 failed/skipped, 39.05s**. Ruff lint/format passed. Frontend build/lint and **47 unit tests** passed; all seven real HTTP scripts passed against an isolated local database. The first aggregate verify attempt reached HTTP tests before the server started; those seven scripts were then explicitly rerun successfully against port 8001.
- GitHub Actions container/PostgreSQL acceptance **passed**: run 40671322353 on 2e369f1 built the complete image, connected to PostgreSQL 16 and passed real caption/parser/OCR/human-workflow smoke scripts plus simulated TLS-offload origin/secure-cookie recovery and forged-origin rejection. Local Docker runtime is unavailable (daemon access denied). Actual Render/Neon public HTTPS/sleep/redeploy acceptance remains pending.
- Packaged browser verification produced four source-backed fictional-caption findings and restored the exact campaign/review on reload. Three backend HTTP smoke scripts passed, including completed Tesseract OCR, explicit correction, persisted records, manual-supplement approval and stale approval after poster replacement. No new external model calls were made.
- Pushed this feature branch and opened draft PR #6. Main remains unchanged by this continuation. The updated Round 2 PDF is a submission draft until a real public project URL and public source access are supplied.
- Confirmed and fixed a TLS-termination defect: HTTPS browser origins could be rejected behind an HTTP container proxy. The app now accepts the exact configured public origin (automatic Render metadata), with strict validation and no trust in arbitrary forwarded headers. Full suite rerun after the fix: 445 passed in 39.05s.
- User says the connected Vercel account is not theirs; it must not be used. User requested preparation of free hosting. See FREE_HOSTING.md. Repository is private; organiser-required public source access still needs a team-owner action.
- Historical records below describe earlier checkpoints and runtimes; they are not current release claims.


## Current local acceptance - 27 October

- Completed the existing backend session-recovery work and connected frontend startup to it. A 24-hour HttpOnly, SameSite=Strict cookie restores the same workspace and actor identities after refresh. Role bearers remain in memory; resume neither creates another sandbox nor extends expiry. Missing cookies remain distinct from server/provenance failures. Existing local-draft deep links remain local.
- Added an optional editable fictional workshop example. It creates real campaign/source/caption records and confirms only the fictional sample rules. Findings, corrections, reviewer notes and approvals are not pre-populated. Partial setup failures leave acknowledged records visible.
- Local verification: **419 backend tests passed**, backend lint/format passed; frontend production build/lint and **44 frontend tests passed**. All seven frontend real-HTTP scripts passed against an isolated local database. Three backend HTTP smoke scripts passed, including real Tesseract extraction, poster contradiction, explicit suggestion/comments/decisions and stale approval after image replacement.
- Browser verification in the Codex in-app browser: created a real campaign and source, ran a price review, reloaded the exact review URL and observed the same saved caption, confirmed source and persisted finding. The example entry creates real editable data and requires an explicit review. This is development verification with fictional data, not external user feedback.
- Updated the dedicated Chrome regression script for resume. The full Chrome/CDP script was **not rerun in this environment**; previous 22-group results below are historical. Public HTTPS/redeploy tests and live contextual-model acceptance remain open. AI was explicitly disabled for this verification run.
- Current checkout already contains merged frontend PRs in its history. Historical notes below describing main as unchanged refer to the earlier integration checkpoint, not today's Git state. No merge, deployment or publication was performed in this continuation.

## Earlier integration baseline - 26 October

Six task flows are implemented and verified against the local API; four tasks remain partial. This is a local integration milestone, not final hosted acceptance.

| Task | Status | Implemented / remaining |
| --- | --- | --- |
| Y01 | Partial | App shell, navigation, real demo sessions, same-browser resume and campaign create/list/get work. Hosted deployment and its cookie/persistence acceptance remain. |
| Y02 | Implemented locally | Six typed rules, explicit owner confirmation, pending/approved states, validity, versions/history and conflict preservation. Brand context is separate and unparsed. |
| Y03 | Implemented locally | Caption saves, expected revisions, conflict reconciliation, real review initiation/history and honest running/partial/failed states. Run Review now shows a spinner and brings returned results/errors into view. |
| Y04 | Implemented locally | Validated PNG/JPEG selection/drop/preview, real upload/replacement and private canonical/historical retrieval. No server-delete route exists. |
| Y05 | Implemented locally | Severity, evidence/source snapshots, suggested actions, coverage, related findings and stale runs. Empty or unavailable checks never imply success. |
| Y06 | Implemented locally | Persisted comments, explicit correction acceptance, before/current comparison, revisions and versioned finding decisions. No automatic correction or stale overwrite. |
| Y07 | Implemented locally | Creator requests, authorised demo reviewer decisions/request-changes, exact incomplete-check notes, receipts and stale readiness/history. Synthetic roles are not production authentication. |
| Y08 | Partial | Historical poster binding and responsive OCR-box renderer implemented; bounds/geometry tested. Genuine extracted-box acceptance requires working OCR. |
| Y09 | Partial | Local regression, responsive/error/permission checks pass. Configured-backend, real-user accessibility/usability and hosted acceptance remain. |
| Y10 | Partial | Integration/setup/release documentation prepared. Final public verification, release URL and submission materials remain. |

## Changes ready for review

- Backend PR #1 (`cdda60fd48371662a1380f82029836960271aa76`) merged on the integration branch. Original frontend checkpoint `a93f782` remains protected on `frontend/connected-review-milestone`; main is unchanged.
- One Sources → Content → Findings → Human Review workspace retains the navy/white/teal design. Brand inputs are simplified; optional fact and technical details are collapsed.
- Fixed direct `/#/new` entry, connected draft creation and discoverable owner confirmation. Local-only drafts remain explicit and separate; local deletion supports confirmation and persists.
- Run Review has visible busy feedback, automatic focus/scroll to actual results and visible request failures. No approved sources used is explained honestly.
- Added expired-session regression, genuine visible-pointer entry/confirmation tests and fail-fast `npm.cmd run verify`.
- Backend implementation is unchanged from PR #1. Checkpoint `031ccd1` was pushed to this integration branch; the user-walkthrough fixes below are recorded in the next checkpoint on the same branch. Main and deployments are unchanged.
- Team update: [rushab-update-email.md](rushab-update-email.md) contains the handoff email draft; it has not been sent.

## User-walkthrough fixes

- Unsaved captions, reference edits, pending images, comments and reviewer notes trigger a leave warning. Cancel preserves edits; reload warns before losing temporary state. No automatic server save or token persistence was added.
- Run Review is blocked while an image is selected, validating or uploading. Upload/remove is explicit. A caption saved after choosing an image advances only its acknowledged local revision; a real concurrent poster write still returns 409 and requires explicit reconciliation.
- Automated summaries show check coverage and snapshot freshness. Human readiness comes from the actual receipt; Recent Reviews now loads receipt statuses, including approval with manual checks, changes requested and stale readiness.
- Missing publication dates get a focused, accessible field error before any request. Lost demo access explains the refresh limitation and separate-workspace consequences instead of claiming the draft is deleted.
- Removed the main development banner and duplicate setup choices. Preview details stay in the header, revisions are collapsed, source context explicitly remains unparsed, and optional tone/claim-policy rules require actual consented AI coverage.
- Sticky References / Content / Results shortcuts and a direct Human Review link reduce mobile scrolling. Unavailable checks have a compact coverage warning. Server deletion remains unavailable; disabled delete buttons were removed from server campaigns.

## Verification observed

- Latest run: production build and lint passed; **33 frontend tests**, **all 7 genuine HTTP scripts**, and **22 browser check groups** passed on both dev `:5173` and production preview `:4173`.
- Real API coverage: campaigns/session/auth/errors, INR 499 pending v1 → approved v2, source/caption revisions, evidence, poster upload/private retrieval, corrections/comments, reviewer permissions, manual-note guards, receipts, stale approvals and explicit AI consent.
- Browser checks include the reported `/#/new` URL, owner confirmation, visible review progress/results/errors, unsaved-edit cancellation on Back/navigation/reload, explicit discard, selected-image blocking, genuine concurrent-upload 409, receipt-based dashboard status, local deletion, mobile widths 390/320 and no uncaught JavaScript errors. Test data/notes are fictional scripted actions, not human feedback.
- Backend latest full run: **310 passed, 21 failed, 1 collection error**. Twenty failures plus collection are missing Linux Noto fonts; the other failure expects OCR partial but missing Tesseract produces unavailable. Backend Ruff lint/format passed. This suite is not fully green.

## Remaining blockers and acceptance

- **Session refresh:** implemented and verified locally. Production must serve frontend and API under the same origin, retain the cookie through the proxy, and use HTTPS/Secure cookies. Resume does not preserve unsaved editor changes or provide production identity.
- **OCR / contextual AI:** real Linux Tesseract extraction and the poster-price workflow passed on 27 October. Earlier tool_missing results were from Windows. Responsive genuine-box browser acceptance and fresh live contextual claim/citation quality remain to be verified. The latest local test server deliberately disabled external AI.
- **Release:** public HTTPS API/frontend, CORS/private images, durable storage/restart, security/retention, accessibility/usability acceptance and submission evidence remain. No confidential-data or production-identity claims.
- **Deletion:** only browser-local drafts can be deleted. Backend campaign/poster deletion requires an actual API contract.
- See [configured-backend-tests.md](configured-backend-tests.md), [regression-report.md](regression-report.md) and [release-checklist.md](release-checklist.md).

## Manual verification

1. Open `http://127.0.0.1:5173/#/new`, start connected review and create a campaign.
2. Add a price fact, save it, then explicitly confirm as owner. Enter a conflicting caption and save it.
3. Run review: check visible progress, actual results/evidence and unavailable coverage. For poster-only review, upload the file to the server first.
4. Exercise explicit corrections/comments and creator/reviewer controls. Source confirmation is not content approval. Refresh and verify the saved campaign, source versions, findings and receipts return; unsaved edits must still warn before leaving.

## Historical teammate runtime notes (before this integration)

4. Exercise explicit corrections/comments and creator/reviewer controls. Source confirmation is not content approval; refreshing still loses demo access.

## Fresh audit — 2026-10-27

- Fetched all remote refs; integration HEAD 878e95c matches its remote. Remote main already contains this checkpoint; no merge/push/deploy performed.
- Fresh lint/build passed and 33 frontend unit tests passed. Seven HTTP scripts failed at session creation with 404: port 8000 serves SpeakEZ API, not BrandProof.
- Backend pytest blocked by Windows Application Control, including escalated execution. Browser CDP unavailable after attempted launch. Historical results above are not fresh acceptance.
- No frontend/backend code changed. See FINAL_QA_REPORT.md and BUG_TRACKER.md. Next: restore approved BrandProof runtime on a free port, align targets and rerun genuine API/browser/configured-provider acceptance. Current release verdict: NOT READY.

## Port isolation follow-up — 2026-10-27

- Frontend dev/preview proxy and HTTP/browser tests target :8001; shared configurable OpenAPI identity guard prevents tests creating sessions against another service.
- Fresh lint/build pass; 36 unit tests pass. Seven HTTP reruns blocked at unreachable :8001 preflight. No connected workflow or release acceptance claimed.
- Actual Uvicorn :8001 startup denied by Enterprise Code Integrity signing policy (3033/3077); approved Python/Linux runtime required. SpeakEZ untouched; backend logic unchanged. Full evidence and alternative-host command in FINAL_QA_REPORT.md.

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


## Caption save clarity ? 2026-10-27

User reported disabled Save caption at :5174. Reproduced successful genuine save/run journey there; exact user state not established. Added explicit empty/unchanged/busy/conflict explanations and ?Caption saved? button label for unchanged saved text, with accessible description. Conflict protection remains intact. Updated browser assertion for revised saved-state explanation. Lint/build and 36 unit tests pass; connected :5174 browser suite passes all 22 groups and real caption review script passes (confirmed INR 499 vs INR 599 contradiction and source v2 evidence). OCR poster coordinates and live contextual AI remain unavailable; no backend changes.


## Completion Sprint 1 - 2026-10-27

- User-approved Tesseract 5.5.3 installation succeeded; English data verified. Direct genuine PNG/JPEG OCR reads Workshop INR 599 and returns coordinates.
- Application OCR remains BLOCKED: confirmed backend Windows incompatibility in selectors over subprocess pipes (WinError 10038/10093). Real application PNG/JPEG probes return extraction_failed and partial reviews without poster findings. Rushab review needed; no backend/tests changed. Existing :8001 also needs updated process PATH on restart.
- Font is a test-image fixture prerequisite, not a production OCR dependency. Pre-install fresh suite: 310 passed, 21 failed, 1 collection error; 20 failures + collection error are missing Linux Noto fixture font, remaining failure is missing OCR tool. No skipped tests or masked assertions.
- Groq BLOCKED: provider none, key/model absent, server disabled; no root .env or Process/User/Machine key/model configuration. User asked to configure locally without sharing key in chat. No paid/live calls made; one consented review pending configuration.
- Fresh frontend lint/build/36 unit tests and real poster/consent HTTP scripts pass; actual OCR highlight acceptance remains blocked.
- See FINAL_QA_REPORT.md and BUG_TRACKER.md for installation details, root causes and evidence. Refresh recovery/deployment remain open. No push/merge/deployment or security changes.


### Post-install full-suite result - 2026-10-27

With `C:/Program Files/Tesseract-OCR` explicitly on process PATH, the unchanged full suite completed: **310 passed, 21 failed, 1 collection error, 0 skipped**, 119.76s. The 20 font-rendering failures and import-time collection error remain. Blank-image OCR still fails because production Windows pipe selection returns unavailable/extraction_failed despite a working engine; this is now the confirmed runner compatibility defect, not missing Tesseract. Evidence: `.cache/backend-sprint1-ocr-installed.log` and `.cache/qa-sprint1-ocr-installed.xml`. No further reruns can resolve unchanged prerequisites/code; Rushab review is required. Latest local health and frontend HTTP checks remain ok/200. No Groq credentials arrived during this run; genuine provider call remains blocked.


## Completion Sprint 1 - fixes accepted locally (2026-10-27)

OCR is working end to end after explicitly authorised Windows runner and portable fixture-font fixes. Genuine PNG/JPEG INR 599 posters contradict confirmed INR 499 v2, with real persisted coordinates/evidence. Browser geometry and inspected mobile screenshot confirm alignment at desktop/390/320px. Exactly one consented Groq request completed with one validated claim finding, no rejections, persisted unchanged across GET/process restart. No-consent stayed unavailable. Overall review stayed partial. Automatic regressions disabled provider calls; final server restored to .env Groq enablement/Tesseract PATH.

Frontend lint/build/36 unit tests, seven HTTP scripts, connected browser 23 groups and Ruff pass. First full backend run: 358 passed plus three new process regression tests passed separately; final combined result follows. Rushab review patch and summary: RUSHAB_OCR_REVIEW.md, rushab-ocr-review.patch. No push/merge/deploy or security changes. Linux CI, same-session refresh recovery, broader provider evaluation, production identity/public hosting and human acceptance remain.


### Final combined verification - 2026-10-27

**Backend: 361 passed, 0 failed, 0 errors, 0 skipped in 132.09s.** Full suite includes the three new real-pipe regressions. Evidence: .cache/backend-completion-final.log and .cache/qa-completion-final.xml. Ruff lint/format pass. Frontend lint/build/36 tests, all seven real HTTP scripts and connected browser 23 groups pass. Actual PNG/JPEG INR 499-versus-599 poster contradictions and desktop/mobile genuine-box alignment verified. Exactly one Groq provider admission, successful validated/persisted result, no retry. Backend is restored with .env Groq enabled and Tesseract PATH on 127.0.0.1:8001; health/database ok, docs 200, frontend :5174 returns 200. SpeakEZ still identifies on :8000 unchanged.

No immediate user setup action is needed. Rushab review and Linux CI remain required before merging the focused backend diff; same-workspace refresh recovery, deployment, broader model evaluation and human usability acceptance remain separate. Nothing pushed, merged or deployed.


## Full application retest requested before poster upload - 2026-10-27

Fresh unchanged full backend suite: 361 passed, 0 failed/errors/skipped, 120.05s (.cache/backend-full-retest.log and .cache/qa-full-retest.xml). Ruff lint/format pass. Frontend lint/build, 36 unit tests, all seven genuine API scripts and all 23 connected browser groups pass, including real OCR poster contradiction and desktop/mobile box alignment. Fixture OCR low_confidence stays partial. Automated provider calls disabled only during HTTP/browser regression; final server restored with existing Groq .env settings and Tesseract PATH. Provider admission count remains exactly 1; no additional live Groq call made. Frontend :5174 and backend :8001/docs return 200, direct/proxied health status/database ok, API identity BrandProof verified. Synthetic sample poster available locally at .cache/sample-poster-inr599.png; confirm INR 499 source, upload sample, then run review for supported contradiction. Session refresh recovery and deployment remain open. No push/merge/deploy or SpeakEZ changes.


## Run review disabled report - 2026-10-27

User reports grey Run review button at local app. Backend health ok; connected browser/real OCR journey freshly passes all 23 groups without external AI consent or additional model calls. Exact user state remains unconfirmed; requested the helper text below button to distinguish pending poster upload, unsaved caption, revision conflict, missing content or local-only preview. No speculative code change or user-specific resolution claimed. Choose-image preview requires explicit Upload poster before review; changed caption requires Save caption. Investigation pending user state.


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

## Manual acceptance audit - 2026-10-28

User requested broad manual browser testing and a handoff for Sol to implement changes. Tested commit 8e93438 using the built UI/FastAPI at :8001 with a separate fictional-data SQLite database. Full results, 56 case entries (including limitations and partial observations), seven prioritised issues and explicit unverified boundaries are in MANUAL_QA_2026-10-28.md. Core caption/reference/correction/human-decision flow passed, including approval staleness, two-tab conflict protection, network-error draft preservation and local process-restart recovery. Actual OCR has layout misses and line-flattening limitations; no universal visual-accuracy claim. Other issues: workflow timestamp timezone, clearing a saved caption, conflict currentness display, expired-reference wording and logo punctuation.

Fresh supporting checks: 445 backend tests passed in 39.21s; 47 frontend tests, frontend lint and production build passed. No external provider call, deployment, merge, push or application-code change. Only QA documentation added; runtime left on :8001 with the isolated test database. Public hosting/remote persistence and representative AI/visual accuracy remain unverified in this pass.


## Manual-audit defects fixed - 2026-10-28

User explicitly requested all seven audited fixes, including the confirmed backend defects. Switched bounded Tesseract segmentation to variable-size column mode, retained real TSV lines/offsets, and made phrase matching whitespace-tolerant. The previously omitted large price now has real OCR boxes; the unqualified multiline example produces a supported contradiction. Negative-language/conditional guards remain conservative. Added explicit caption removal with poster requirement, role/version checks, immutable history and stale prior decisions. Normalised workflow/campaign/source/revision timestamps to UTC-aware responses. Conflicts immediately stale the visible review and block dependent mutations. Expired references show applicability on the card and confirmation message; logo punctuation and OCR coverage wording corrected.

Validation: 451 full backend tests passed in 40.62s; seven focused audit regression tests subsequently passed including one added real multiline case. Frontend 48 tests, lint, build; backend Ruff lint/format and git diff whitespace checks pass. Browser retests confirmed caption removal and poster-only review, price extraction, multiline supported contradiction, corrected old comment time, immediate conflict gating/reconciliation, expired confirmation and logo wording. See MANUAL_QA_2026-10-28.md for exact baseline/fix evidence. API handoff and OpenAPI updated. No external provider call, production deployment or main merge.


## Local claim-risk screening — 2026-10-28

User explicitly requested fixing the missed “Guaranteed results in 30 days” case. Added bounded local English promise screening independent of approved sources and external AI. New caption/OCR poster findings are warnings requiring clarification, with real spans/boxes and no invented evidence or factual replacement. Coverage records the screening version, per-asset counts and limits; incomplete OCR remains partial. New partial claim coverage requires explicit finding disposition and dedicated reviewer notes before approval. Historical runs without claim screening remain compatible. UI distinguishes potential promises from cited contradictions, preserves no-findings/not-approved behavior and accommodates four coverage cards. OpenAPI/API handoff updated; scope and judge demo are in CLAIM_RISK_SCREENING.md.

Fresh final checks: **497 backend tests passed in 44.48s**, **49 frontend tests passed**, frontend build/lint, backend Ruff lint/format and git diff whitespace checks passed. Browser acceptance on the isolated local QA database confirmed no-source/no-AI promise detection, ordinary-duration negative case, stale historical result after correction, real poster OCR/highlights and persisted results across reload. Automated API tests verify unresolved-finding and dedicated-manual-note approval guards. These are synthetic functional checks, not representative detection accuracy. No external provider call, push, main merge or production deployment. Runtime :8001 serves the updated UI/API with external AI disabled.

## New Review startup hotfix — 2026-10-28

Confirmed incident: public API returned 502 while Render Free was asleep; backend logs showed normal idle shutdown and a successful restart. Direct health recovered after roughly 24 seconds; public campaign creation/list/get then passed. Backend code and deployment configuration unchanged.

Isolated fix based on production 36cb8ae: same-origin, credential-free health GET retries for up to 90 seconds before session creation, browser-session resume and campaign creation. Show accessible startup progress. Validate database health, share concurrent checks and cache readiness for 15 seconds. Never retry POST writes or silently replace a failed session. Preserve form input; ambiguous gateway errors advise reloading Recent Reviews before another submission. No Round 3 feature code included.

Validation: 52 frontend tests passed, lint and production build passed. Real public API session/campaign persistence, role guards and workspace isolation passed. Browser verified actual public New Review and refresh persistence. Built hotfix was additionally supplied only to the disposable browser at the public origin: two simulated health 502s recovered, visible startup message, exactly one session/campaign creation, Sources workspace and refresh restoration passed. Local preview-to-production testing correctly encountered the backend origin guard; final verification used the actual allowed public origin. Production update and post-deploy acceptance follow through the existing Vercel project.
## Dashboard deletion release backport — 2026-10-28

User explicitly requested making the prepared Delete option live. Isolated the tested removal feature on integration/round2-backend-pr1 from production 298c776, retaining the New Review cold-start fix and excluding unrelated improvements. Added owner-only revision-checked removal/restore endpoints, normal-access filtering, Delete/Cancel/Confirm/Undo dashboard controls and mobile-safe confirmation. Existing startup adds only campaign_removals; no existing data/table/column is deleted or altered. Future feature-branch migration 0005 recognizes this table. API handoff and OpenAPI updated.

Validation: 501 backend tests passed in 219.00s, 53 frontend unit tests passed, backend Ruff check/format, frontend lint/build, seven actual HTTP suites and all 26 existing local browser groups passed (including Tesseract, poster and logo reference). Dedicated browser deletion passed cancel/no write, confirmed hiding, same-review Undo, mobile confirmation, deletion persistence after reload and unchanged workspace. Legacy schema/data startup idempotence and PostgreSQL DDL compilation passed; no live PostgreSQL sandbox/backup is claimed. A fictional production persistence probe is held in process memory for post-Render-deploy verification. See REVIEW_DELETION_RELEASE.md for narrow release order, limits and rollback behavior. Main and the broad feature branch are unchanged.


## Latest feature-branch local retest — 2026-10-30

User requested restart and testing of ca6dd8c. Synced frozen dependencies, built UI, started isolated SQLite runtime at :8001 with real Tesseract and external AI disabled. Frontend 54 tests/build/lint pass; real feature HTTP smoke and all seven frontend HTTP suites pass. Manual browser confirms PDF pending page evidence/confirmation, actual findings, background measurement, alt-text save/staleness/review, explicit unverified draft save gate, governance sample guard/exact evidence links and same-session recovery after process restart. All 17 saved review snapshots were unchanged across restart.

Full backend result: **513 passed, 3 failed** in 47.99s. Confirmed contrast detector rejects ordinary antialiased Noto text; exact dominant ink fraction 76.61% is below its 80% guard. Actual HTTP upload/Tesseract/rule/review reproduction also yields partial contrast with no measurement. No false pass was returned. Ruff lint passes; formatting/diff checks fail on the preserved pre-existing approval.py edit. No application/test fix, push, merge, public deployment or live model call. See LOCAL_RETEST_2026-10-30.md for evidence and limits.

## Visual refresh — 30 October 2026

User-authorized frontend beautification on `feat/brandproof-improvements-20261028`: navy navigation with inline vector icons, a larger two-tone overview heading, explanatory numbered workflow, dedicated fictional-example entry, calmer campaign rows, and consistent reference/finding/readiness/insights surfaces. Mobile rules support narrow screens and preserve visible focus and reduced-motion preferences. No dependency or backend changes.

Validation: production build and lint passed; all 54 frontend unit tests passed. Manual CUA checks against the built frontend on port 8001 covered overview, new-review navigation/date validation/cancel, existing review navigation, source/content/results anchors, insights data, example campaign creation and a genuine review returning eight findings. Pending policy exclusion and incomplete coverage remained visible. Tested 390px and 320px layouts; fixed inherited body minimum-width overflow and verified final 305px client/scroll width equality at a 320px viewport. Keyboard Tab reached New Review with a visible outline. Screenshots: `/home/KARMA/Documents/Codex/2026-10-24/i/outputs/brandproof-design/`. Local only; not committed, pushed or deployed. Earlier contrast-sampling defect and unrelated approval.py edit are unchanged.

### Visual direction refinement — 30 October 2026

Following the user's request for a simpler, less templated appearance, removed the oversized marketing headline, uppercase taglines, shield decorations and dark navigation. Replaced them with a compact BrandProof monogram, white sidebar, plain “Your reviews” heading, restrained separators, less rounding/shadow and a short example invitation. Existing workflow controls and evidence semantics are unchanged. Build and lint passed again. Desktop screenshot inspected; manual responsive verification recorded in this turn. Not pushed or deployed.

### Colour refinement — 30 October 2026

User requested more distinctive colours while retaining the simple layout. Updated the visual-system palette to ink-blue text, ivory canvas, pale-blue navigation and evidence surfaces, with terracotta/coral primary actions and monogram. Warning/error and confirmed-source status colours retain their semantic roles. Production build, lint and scoped diff whitespace check passed. Inspected the actual built overview in CUA and saved `outputs/brandproof-design/colour-overview.png` in the Codex workspace. Measured white-on-primary contrast: 4.95:1; main text on ivory: 11.43:1. This is a palette check, not a full accessibility audit. Local changes only.

### User-supplied palette selection — 30 October 2026

Selected reference image 2: Desert Sun `#dc9750` and Dark Blue `#1e2640`. Applied orange primary actions and monogram with navy text (not white), navy headings, warm neutral canvas and a pale orange example invitation. Kept the simplified layout and semantic finding colours. Build/lint passed; inspected the rebuilt overview in CUA. Local only.

### Palette correction — 31 October 2026

Corrected the pale interpretation after user feedback: the sidebar now uses exact Dark Blue `#1e2640`, with exact Desert Sun `#dc9750` for the active navigation and primary actions. Light sidebar text and Desert Sun keyboard focus preserve readability; the example action uses navy with light text. Built and linted successfully. CUA computed styles confirmed RGB(30,38,64) sidebar and primary text, and RGB(220,151,80) active navigation/primary background. Inspected and saved `outputs/brandproof-design/corrected-desert-sun.png`. Changes remain local.

### Top-bar refinement — 31 October 2026

User requested navbar adjustment. Connected the header visually to the navy sidebar, reduced desktop height to 66px, aligned the breadcrumb with content, and replaced the greenish status pill with a navy session dropdown, Desert Sun indicator/focus and explicit expand chevron. The readable white dropdown retains existing actions. Build/lint passed. Manually opened/closed the session dropdown and checked at 390px: page client/scroll widths both 375px, dropdown right edge 355px. Saved `outputs/brandproof-design/topbar.png`. Local only.


## 31 October 2026 — T00/T01 contrast repair

Reproduced and repaired the three contrast failures with solid-core, blend-colour and glyph-edge guards. Added real-OCR HTTP, font/size, uncertainty and threshold regressions; measurement details/UI now include sampled colours and target ratio. Removed the pre-existing unreachable approval tail after preserving a local backup. Full backend: 542 passed; frontend: 54 passed, lint/build passed; Ruff and whitespace checks pass. Manual UI acceptance blocked by browser security policy. No public deployment or legal implementation claimed. Evidence: T00_T01_RETEST_2026-10-31.md.


## 31 October — Round 3 local candidate

Completed local PDF/visual/Insights acceptance and the curated India advertising-risk profile/evidence/approval path. All 574 backend and 56 frontend tests pass; seven real-HTTP suites and the expanded smoke pass. Verified six-step SQLite migrations, wheel contents/import and actual process restart with eight unchanged table digests. Added the six-page report, downloadable fictional guidelines, legal scope and release/submission handoffs. Preserve the earlier styling work. Manual UI and PostgreSQL/container checks are unverified because browser/Docker access was denied. Public homepage metadata found via GitHub; API returned 429. User requested local-only release after hosting ownership was unclear. No push/merge/deploy/submit. Current source: ROUND3_LOCAL_ACCEPTANCE_2026-10-31.md.


## 31 October — authorised integration into main

User explicitly requested pushing the completed feature work to main. Merged feature b8acc3c with origin/main 43fc4a5, retaining main's cold-start readiness checks for delete/restore, disabled controls during deletion, deletion browser journey, and two extra backend regressions. Adapted the legacy-removal fixture to the versioned migration history without changing production migration behaviour.

Merged-tree checks: frontend 56 tests, lint/build and backend Ruff lint/format pass. Full backend run passed 575 tests; one assertion was placed before deletion during conflict resolution. Moved it after deletion and reran all four removal tests successfully. No product code changed after that full run. Whitespace and conflict checks pass. This authorises GitHub main publication; it does not establish a deployed/public acceptance result.

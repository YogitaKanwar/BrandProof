# Final tests requiring a fully configured backend

## Connected deletion local acceptance - 28 October 2026

- Feature-branch only: 516 backend tests / 51 frontend tests, lint/format/build, seven HTTP suites, all 26 existing browser groups and new connected delete cancel/confirm/Undo/reload acceptance passed. Data/history preservation, owner/workspace/revision/running-job guards and old-Undo rejection tested. Saved OpenAPI matches running :8014.
- Added `0005_review_removal` only; no production schema or deployment change. Public provider metadata and HTTP contract still verify `36cb8ae`, with no connected DELETE/PDF import routes. Copy-ready judging answers separate that public release from the review branch.
- An old browser assertion expected connected deletion to be absent; it now asserts the new Delete button. The new end-to-end test exercises its real API actions, rather than simulating success. No existing user review was deleted during this work; acceptance used isolated fictional data.

## Feature-branch local acceptance - 28 October 2026

This is local feature acceptance, not a deployment of the improvements. Existing production remains `36cb8ae`.

- Branch `feat/brandproof-improvements-20261028`: all authorized implementation slices complete. Backend 514 passed, frontend 50 passed; lint/format/build/dependencies, wheel build/installed-wheel startup, OpenAPI parity, seven actual HTTP suites, 26 existing browser groups and new PDF/draft/description/governance/readiness browser journey passed.
- Production resource probe used only fictional records, with no settings/code migration: 5,155,064-byte PNG HTTP 200 in 10.32s; logo review 201 in 3.994s with not-assessed/manual time-limit result. Initial health 502, subsequent 200 after direct warmup. Database available, expiry 27 November; provider unavailable and quotas unchanged. These are single samples, not a controlled sleep/load test.
- New PostgreSQL legacy-upgrade/idempotence and production-container CI are configured; do not infer their result from SQLite or the prior production release. Backup/restore, reviewed migration/app deployment, public new-feature/redeploy acceptance and live consented provider acceptance remain explicit release gates.
- Complete evidence/limits: [improvements final report](improvements-final-report.md). Local evidence `.cache/improvements-20261028/backend-final.xml`, `production-resources.json`, isolated local/wheel databases, and browser screenshots under `frontend/node_modules/.cache/improvements/`. Scripted fictional decisions are not independent human evaluation.

## Fresh pre-push release acceptance - 28 October 2026

- Backend: 445 passed in 145.14 seconds, zero failures/skips; .cache/release-20261028.xml. Ruff lint and format pass (70 files).
- Frontend: build/lint, 47 unit tests, seven genuine HTTP suites and all 26 connected browser groups pass against isolated local HTTP/SQLite. Exact preview CORS origin configured for QA after the initial browser setup failure; no backend code change.
- Genuine Tesseract workflow: completed extraction, real poster price finding, explicit suggestion, persisted records, approval with real scripted manual-check notes, then stale receipt after poster edit. Evidence .cache/release-workflow.json. Browser covered PNG/JPEG INR 599 vs confirmed INR 499, responsive boxes, historical images, logo-reference confirmation and same-workspace refresh recovery.
- External AI disabled throughout; no fresh Groq call. Existing OCR/Groq implementations and historical acceptance are included; Groq requires private cloud configuration and explicit consented live acceptance.
- Render/Vercel account verification passed. No resources/public URLs yet. PostgreSQL durability, public HTTPS/proxy cookies/private images, near-limit upload latency and restart persistence remain untested. Docker CLI absent from current PATH; earlier CI evidence below is retained with its original commit scope.

## Fresh local evidence - 28 October 2026

Integration includes approved session/hosting branch at 8e93438. Fresh backend 445/445, frontend 47/47, seven HTTP suites and 26 connected browser groups pass. Actual Tesseract PNG/JPEG contradictions, desktop/mobile boxes, reference-logo workflow and same-campaign cookie recovery exercised on local HTTP/SQLite. Browser clear-cookie scenario explicitly reloads to discard memory state. Backend evidence: .cache/deployment-current.xml and .cache/deployment-current.log (ignored local artifacts). External AI disabled; no fresh provider-quality claim.

Hosted acceptance remains pending: team-owned Vercel/Render connections, privately configured PostgreSQL, HTTPS API rewrite with private response/cookie handling, near-limit upload/review latency, same-workspace reload, redeploy/restart/sleep durability and retained original image. Instructions: VERCEL_RENDER_DEPLOYMENT.md. No public URL or cloud resource created. Earlier checklists/results below retain their original dates and scope.

These are remaining acceptance tests, not features silently reported complete. Continue frontend work against local responses; do not wait for public hosting or fabricate outputs.

- [ ] Real Tesseract extraction on canonical PNG/JPEG, including rotated/transparent inputs, blank images, low-confidence text and unavailable/tool timeout. Windows currently returns tool_missing.
- [ ] Approved reference price INR 499 vs actual poster INR 599 -> real poster contradiction. Inspect real boxes at desktop/mobile sizes; verify old-run overlays keep their historical poster after replacement.
- [ ] Live Groq: consent false makes no external call; explicit true with server enablement/key/model produces actual validated contextual output. Verify unsupported guarantees mean missing substantiation/clarification, not proven falsehood. Preserve refusals/quotas/timeouts as incomplete.
- [ ] Overlay DOM and screenshots with genuine OCR boxes. Pure percentage/bounds tests pass locally but do not prove OCR quality.
- [x] Replay full backend suite on its documented Linux/font/Tesseract runtime. On 27 October: 419 passed, including the new session-recovery tests; lint and formatting passed. The earlier Windows prerequisite failures remain historical evidence, not the current Linux result.
- [ ] Public HTTPS frontend/API: CORS/authenticated private images, exact revisions, comments, source/caption/poster stale receipts and provider outage. Test page refresh/session contract honestly.
- [ ] Persistent database/images/receipts survive actual service restart/redeploy; verify storage/retention/security limits from BACKEND_DEPLOYMENT.md.
- [ ] Real reviewer usability and accessibility feedback. Test actual incomplete-check notes without prefilled attestations; scripted local approvals are not user feedback.
- [ ] Final release URL, submission screenshots/materials, ownership/provenance and account-specific provider quota checks.

Local additions verified 27 October: session-cookie resume preserves the existing campaign/actor identity across reload; three real HTTP smoke scripts passed with completed Tesseract extraction and poster-price findings. The seven frontend HTTP scripts passed; their small poster fixture correctly reported partial/low-confidence OCR. No fresh live-model call, public deployment or full Chrome/CDP regression is claimed by these results.

This checklist does not authorise a paid service, public deployment or system-level OCR installation.

## Hosting preparation - 28 October

Latest combined suite: 445 backend tests passed, 47 frontend tests passed, build/lint/format passed, and all seven actual HTTP integration scripts passed. FastAPI serves the built UI and real API together on port 8001. External AI is off for this run. Browser reload restored the same campaign and four findings. Three local HTTP smoke scripts passed with real OCR and human workflow. Free hosting setup is prepared in FREE_HOSTING.md and render.yaml; no public service or account was created. Docker daemon access remains denied locally.

**Container/PostgreSQL CI passed:** [run 40671322353](https://github.com/YogitaKanwar/BrandProof/actions/runs/40671322353), commit 2e369f1, 28 October 10:21 UTC. The complete image built; UI/health and caption/parser/OCR/human-workflow smoke scripts passed against PostgreSQL 16. This does not establish public HTTPS, Neon TLS, sleep/redeploy persistence, actual external-model quality or independent human acceptance. Those checklist items remain open.

## Historical teammate runtime notes (before this integration)

No paid service, public deployment, system-level OCR install or backend modification is authorised by this checklist.


## Current local runtime evidence ? 2026-10-27

Signed .venv-check Python 3.14.10 now works; locked dependencies installed. Actual BrandProof :8001 health/docs and frontend :5174/:4173 proxy verified. Seven HTTP scripts and connected browser journey pass; genuine INR 499 source versus INR 599 caption evidence, corrections, comments, permissions, conflicts, stale receipts and memory-only refresh boundary verified. Real PNG/JPEG upload succeeds; OCR returns unavailable/tool_missing. Provider none, no key/model, external AI disabled; no live Groq success. Backend suite: 310 passed, 21 failed, 1 collection error from missing hardcoded Linux font; Tesseract absent. Ruff lint/format pass. Checklist remains incomplete for configured OCR/Groq, restart/public deployment and human acceptance. Full detail in FINAL_QA_REPORT.md.


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


## Image selection / grey Run review flow fixed - 2026-10-27

User repeatedly reported that adding an image disabled review. Confirmed UI flow: pending image preview set posterPending and disabled the only primary review action, requiring a separate upload step. Updated frontend so selected image offers explicit Upload poster and run review. On click it awaits real revision-checked upload/canonical OCR, refreshes campaign, then reviews the acknowledged saved revision; upload/conflict failure aborts review and preserves the selected image. Caption edits still require save; concurrent writes still return 409 and require explicit reconciliation. No backend changes, auto-approval or silent AI consent.

Files: frontend/src/ContentWorkspace.tsx, LiveCaption.tsx, LivePoster.tsx; frontend/tests/browser-smoke.mjs. Fresh lint/build and 36 unit tests pass. Connected browser 24 groups pass: selected poster plus caption save, combined-action 409 with no created run, explicit reconciliation/retry, real OCR boxes at desktop/mobile, and poster-only PNG then JPEG reviews against confirmed INR 499 with actual INR 599 contradictions. Provider admission count remains 1 (no new Groq calls). Original backend 361-pass result remains from preceding full run; backend was unchanged in this fix. No push/merge/deploy; current frontend :5174 serves the change without full-page refresh.


## Brand-logo comparison feature - 2026-10-27

User explicitly requested this new feature. Added private owner-only reference upload/confirmation, immutable versions/history, revision-bound snapshot provenance, conservative bounded local template comparison, and frontend reference upload/preview plus possible-mismatch findings. Confirmed logo replacement invalidates prior review currency. Pending references are excluded; uncertain matches never approve content. No provider calls or new dependencies. Empty findings/close candidates do not prove a correct logo; tiny changes, backgrounds, rotations and small logos require human inspection. See LOGO_COMPARISON_REVIEW.md for exact supported scope, new routes and focused backend patch for Rushab.

Six focused backend tests pass; first full suite 366 passed before the additional immutable-snapshot test. Frontend lint/build/36 unit tests pass. Connected browser with BRANDPROOF_TEST_BACKEND=1 BRANDPROOF_TEST_OCR=1 BRANDPROOF_TEST_LOGO=1 passes all 25 groups, including actual logo reference upload/owner confirmation and real PNG/JPEG reviews that show possible mismatch and the historical reference image. Matching synthetic example scores 0.9745 and remains partial; altered example scores 0.7329 and warns. These are raw similarities, not calibrated confidence or representative accuracy.

Final combined suite result follows. Runtime :8001 reloaded; UI :5174 contains Brand logo under Brand Information. No reset, existing-data deletion, external notification, extra Groq call, push/merge or deployment. Linux/real-logo quality acceptance and Rushab review remain outstanding.


### Final logo-feature verification - 2026-10-27

Full combined backend suite: **367 passed, 0 failed/errors/skipped**, 167.57s (.cache/backend-logo-combined.log / .cache/qa-logo-combined.xml). Backend Ruff lint/format and frontend lint/build/36 tests pass. Connected browser 25 groups pass with owner logo confirmation, real missing-logo warning, historical image and PNG/JPEG poster journey. Actual HTTP matching-versus-altered sample: matching candidate 0.9745/no warning; altered candidate 0.7329/one needs_clarification warning; both remain partial and persisted. Evidence .cache/logo-live-evidence.json; raw score is not calibrated confidence. Provider admissions remain exactly one from earlier Groq acceptance; no extra provider calls. Frontend :5174 returns 200 and backend health/database ok after feature restart. Focused new backend patch: rushab-logo-review.patch; scope/limits and Rushab review notes: LOGO_COMPARISON_REVIEW.md. No push/merge/deploy. Small alterations, rotations and complex/low-resolution backgrounds remain manual-review scope.


## Local claim-risk acceptance — 28 October

Configured runtime: FastAPI and built UI on 127.0.0.1:8001, isolated manual-qa-oct28 SQLite database, real local Tesseract; external AI disabled/provider none. Fictional “Claim-risk demo” campaign: source revision 0, no approved facts. Browser saved and reviewed “Guaranteed results in 30 days.”: one needs-clarification warning with the actual caption span, contextual unavailable, claim screening partial and readiness not approved. Revised to “The workshop lasts 30 days.”: zero findings, pattern scan complete, readiness still not approved, earlier result historical. Uploaded a generated 1200×220 PNG of the promise: actual OCR completed, one poster risk finding with real word highlights and 91% OCR confidence; source evidence absent as expected. Reload retained the run, image and warning. Final runtime restarted with the same database and updated code/UI.

Fresh automated checks: 497 backend tests/49 frontend tests pass; build, lint, format and diff checks pass. Tests include guarantees, time promises, placement/admission/cure, absolute/quantified claims, selected denials/hedges, overlap/Unicode, scan limits, real OCR, no-source persistence and human approval enforcement. No fresh external model request or public-deployment verification; no representative precision/recall claim.

## Public acceptance — 2026-10-28

- Application source: 639fe5fb8a4b43d9a46f1bec503e2b8031273f78 on integration/round2-backend-pr1.
- Render Docker deployment dep-dbh3fa0473hc7384ju10 is live at https://brandproof-api-slz9.onrender.com. Backend/database health is ok; actual contract exposes DELETE campaign and POST restore.
- Vercel production deployment dpl_Grf42dLLAjyMswKTR5h9RJ4v3fXp is READY with https://brand-proof-tau.vercel.app/ assigned. Public HTML returned 200 and serves index-B4CsNG0r.js / index-N18PP02p.css.
- Actual public dashboard browser check passed Delete, Cancel with no mutation, confirmation, same-review Undo, mobile confirmation, deletion persistence after full refresh and unchanged session. New Review and refresh restoration passed with two simulated failed health GETs; this is a transient-failure regression, not a controlled hosting sleep benchmark.
- Actual production PostgreSQL-backed removal/restore API test passed owner-only access, stale revisions, cross-workspace isolation, hidden reads/writes, identical restored campaign/source/review/receipt and stale deletion-generation rejection. Eight real HTTP suites passed (seven existing plus removal).
- The pre-deployment fictional persistence probe resumed the same workspace after Render replacement and confirmed unchanged campaign, confirmed source, review and identical poster/logo SHA256 bytes. Credentials were held only in process memory.
- Full local regression: 501 backend tests, 53 frontend tests, seven HTTP suites, 26 existing browser groups plus dedicated cold-start/delete journey passed; Ruff check/format, frontend lint/build and whitespace checks passed.

All public checks used fictional isolated workspaces. Existing PostgreSQL and hosting settings were reused. No provider/AI enablement or paid upgrade, no main merge, and no other Round 3 feature release. Original primary-workspace documentation edits remain intact.

## Feature-branch local acceptance — 30 October

Fresh isolated SQLite/Tesseract :8001 runtime on ca6dd8c, external provider disabled: 513 backend tests pass, 3 contrast-rendering tests fail; 54 frontend tests/build/lint pass. All seven genuine frontend HTTP suites and the improvements HTTP smoke pass. Browser confirms PDF evidence/confirmation, background and alt-text flows, explicit draft/save gates, governance evidence links and session/review recovery after restart. Real HTTP contrast reproduction on black Noto TEST over white yields completed OCR but partial contrast/zero measurements because the exact-ink guard rejects antialiasing. No production/PostgreSQL/model acceptance is claimed. Preserved local approval edit fails formatting/whitespace checks. Detailed findings: LOCAL_RETEST_2026-10-30.md.

### 30 October 2026 — visual refresh acceptance

Restarted the existing isolated SQLite retest runtime on 127.0.0.1:8001 with the rebuilt frontend, same database, external AI disabled. Browser session restored its original campaign. The redesigned example entry created campaign `deb456a2-a86b-44f7-92f7-99f63225cb1b`; Run review returned eight actual findings and kept the pending policy excluded, partial coverage visible and readiness not approved. No approvals or provider calls were made. This frontend acceptance does not supersede the earlier backend report's three contrast failures.


## 31 October 2026 — contrast repair local verification

Latest local suite after T00/T01: 542 backend tests pass, 54 frontend tests pass, lint/build/Ruff/whitespace pass. Real Tesseract HTTP uploads measure black and grey text and retain finding source versions/boxes. Mostly antialiased small text and uncertain images still abstain. Browser security policy prevented manual UI acceptance; public/PostgreSQL acceptance remains unverified. See T00_T01_RETEST_2026-10-31.md.


## 31 October — Round 3 current local acceptance

574 backend tests and 56 frontend tests pass; frontend build/lint, Ruff format/lint, whitespace and saved/live OpenAPI parity pass. Seven real-HTTP frontend suites and expanded PDF/contrast/advertising/approval smoke pass on an isolated SQLite/Tesseract runtime with external AI disabled. Actual server restart preserved eight table digests including profiles, documents, decisions and receipts. Wheel contains and imports the frozen legal pack and migration metadata. Manual browser and PostgreSQL/container execution remain unverified. User selected local-only release. Detailed evidence and limits: ROUND3_LOCAL_ACCEPTANCE_2026-10-31.md.

## 31 October 2026 ? integration release preparation, no production update

Existing team-owned resources were reidentified through connectors: Vercel project `prj_GEGiIsaOoEp0mww0FY5LIkOZKyf6` and public alias `brand-proof-tau.vercel.app`, current READY deployment `dpl_Grf42dLLAjyMswKTR5h9RJ4v3fXp`; Render service `srv-dbgtr7nb9u1s73981s70`, live deployment `dep-dbh3fa0473hc7384ju10`, both at source `639fe5f`. Render reports PostgreSQL `dpg-dbgtpn5g1s2s73c9tg60-a` available on Free, expiring 27 November 2026; its empty external IP allowlist prevents connector SQL/export access. No access rule was relaxed and no backup is claimed.

The user explicitly requested production remain unchanged until a restorable backup is available. The latest Round 3 tree is prepared on integration only. Fresh isolated SQLite/Tesseract runtime at 127.0.0.1:8014 passed eight frontend HTTP suites and expanded PDF/OCR/contrast/advertising-risk/approval/readiness/governance smoke, external AI disabled. Arial produced truthful contrast abstention; Noto test-font rerun passed supported measured contrast. Credentials remained in process memory. Local backend: 558 passed, 18 optional font skips; frontend: 56 passed, lint/build passed; Ruff passed. No fresh public Round 3 acceptance or manual browser result is claimed.

Upstream feature CI [41211193409](https://github.com/YogitaKanwar/BrandProof/actions/runs/41211193409) passed Docker build, PostgreSQL health, real workflows, additive migration upgrade/idempotence and feature smoke. The overall run failed its offline evaluation test because tests were copied to `/tmp/backend-tests`, making a repository-relative script resolve to `/scripts/evaluate_live.py`. The prepared CI fix retains `/app/backend/tests` and copies `/app/scripts`; the final integration result follows when available. This test-harness fix does not modify application behavior.

### Final integration CI ? 31 October 2026

[Hosting package run 41213208584](https://github.com/YogitaKanwar/BrandProof/actions/runs/41213208584), exact commit `9d6d227a530ee1aa7fd752579460cab48fdd687b`: **success**, frontend and container-postgres jobs both successful. The actual production Docker image built and started against ephemeral PostgreSQL 16; database health, real caption/parser/OCR/approval/session workflows, additive PostgreSQL legacy upgrade/idempotence and expanded PDF/contrast/advertising/description/readiness/governance smoke all passed. Full offline backend in the image: **558 passed, 18 skipped**, 114 deprecation warnings, 76.36 seconds. The skips are the optional Noto font-family matrix under its Linux-only path. Frontend: 56 tests, lint and build passed. The CI layout fix resolved the prior missing-script failure without backend product changes.

Local installed-wheel checks found valid packaged `legal_pack.json` and `migration_baseline.json`, with no environment/database artifacts. Actual local API OpenAPI equals the saved contract; local `migrations --check` reports no pending steps and no application. These local/ephemeral-CI checks are not production migration or backup evidence.

Vercel READY preview `dpl_C8ux1u81waHyheQzqrg4zvzW6u8R` was built from the same commit. It was not promoted and still targets the older production API. Connector rechecks confirm public alias `brand-proof-tau.vercel.app` remains assigned to `dpl_Grf42dLLAjyMswKTR5h9RJ4v3fXp` and Render remains live at `dep-dbh3fa0473hc7384ju10`, both application source `639fe5f`. User-required hold: no production update until a current restorable PostgreSQL backup/restore procedure is available. No new public Round 3 workflow/manual-browser acceptance is claimed.

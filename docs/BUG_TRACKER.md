# QA bug tracker — 2026-10-27

| ID | Severity | Reproduction / actual | Expected / action | Owner / status |
| --- | --- | --- | --- | --- |
| QA-01 | P0 release blocker | Run any frontend test:* HTTP script; session POST returns 404. GET :8000/openapi.json identifies SpeakEZ API, zero BrandProof /api/v1/ routes. | Start BrandProof on an available port and align proxy/test target; preserve unrelated service. | Runtime configuration; open, not a confirmed backend code defect |
| QA-02 | P0 audit blocker | Run .venv/Scripts/python.exe -m pytest; Windows Application Control blocks executable, including outside sandbox. | Use an approved Python environment to execute backend and suite. | Machine/runtime owner; open |
| QA-03 | P1 audit blocker | npm.cmd run test:browser; localhost:9223 connection refused, including after attempted hidden headless Chrome start. | Provide working dedicated CDP browser, then run responsive/judge tests. | Browser environment; open |
| QA-04 | P1 acceptance gap | Correct BrandProof runtime unavailable; no genuine OCR/Groq/restart/hosted acceptance possible. | Execute configured-backend-tests.md on actual runtime; preserve incomplete status until verified. | Backend/deployment owners; open |

No new frontend code defect confirmed. Previously documented memory-only session refresh limitation remains; no token-storage workaround authorised. Severity denotes release/audit impact, not a claim of application corruption or a newly discovered backend implementation bug.

## Isolation follow-up

- QA-01: configuration fixed in source: Vite and all seven HTTP/browser probes default to :8001; configurable test base and API-identity preflight added. Runtime still blocked; :8000 independently confirmed SpeakEZ unchanged. Existing preview needs restart.
- QA-02: confirmed Code Integrity events 3033/3077, Enterprise signing level rejection, policy {0283ac0f-fff1-49ae-ada1-8a933130cad6}. Actual :8001 Uvicorn startup blocked with `An Application Control policy has blocked this file`. Requires administrator-approved Python or an approved Linux host; do not bypass policy.
- QA-03/QA-04: remain open. Seven reruns stop at unreachable :8001 OpenAPI; no workflow assertions executed. No new backend defect established.
- Regression: lint/build pass and 36 unit tests pass (three new preflight tests). See FINAL_QA_REPORT.md for private Linux-host startup recommendation and exact command.

## Latest requested retest — 2026-10-27

Fresh `npm.cmd run verify`: build PASS, lint PASS, 36 unit tests PASS (zero failed/skipped); test:api BLOCKED by ECONNREFUSED at :8001/openapi.json. Fail-fast verification did not execute the remaining six HTTP scripts or browser suite. Port :8000 still identifies SpeakEZ API and was left unchanged. Retried documented Uvicorn startup on :8001: `Program 'python.exe' failed to run: An Application Control policy has blocked this file`. No policy bypass or backend changes. Runtime-dependent tests remain blocked; next action is an approved Python runtime or private approved Linux test host. Release readiness remains NOT READY.


## Signed runtime retest ? 2026-10-27 (current status)

- QA-01 RESOLVED locally: BrandProof :8001 health/OpenAPI verified, dev :5174 and preview :4173 proxy health verified; seven real HTTP scripts pass. Old occupied :5173 is not a verified working proxy. SpeakEZ :8000 preserved.
- QA-02 RESOLVED: official and new .venv-check Python 3.14.10 signatures Valid; locked dependency installation and runtime successful. Old .venv preserved.
- QA-03 RESOLVED locally: dedicated hidden Chrome CDP launched with escalation; connected browser suite passes all 22 groups.
- QA-04 OPEN: Tesseract missing; Groq disabled/unconfigured. PNG/JPEG uploads pass but OCR is unavailable. Live Groq and configured-runtime acceptance not completed.
- QA-05 OPEN, P1 test prerequisite gap: unchanged backend suite hardcodes Linux Noto font unavailable on Windows; 310 passed, 21 failed, 1 collection error. Provide approved font/OCR runtime; no confirmed backend code defect or unauthorised backend edit.

Frontend lint/build/36 unit tests and backend Ruff lint/format pass. Refresh memory-only session boundary, permissions, stale approvals and real price contradiction are exercised by HTTP and connected browser suites. No release readiness or deployment claim.


## Completion Sprint 1 - current diagnosis (2026-10-27)

| ID | Status / root cause | Evidence / next action |
| --- | --- | --- |
| QA-04 | OCR engine installed and CLI works; application OCR BLOCKED. Groq BLOCKED, unconfigured. | Tesseract 5.5.3, eng/osd available, real PNG/JPEG CLI recognition/boxes. App uploads return unavailable/extraction_failed. No live provider call; configure key locally and model before one consented review. |
| QA-05 | OPEN: test fixture portability/prerequisite issue | Fresh pre-install run: 310 passed, 21 failed, 1 collection error. Precisely 20 failures + collection error from hardcoded missing Linux Noto font; 1 blank-image failure from missing OCR tool. Font is fixture generation, not production dependency. Rushab to review portable fixture configuration or rerun on documented Linux. |
| QA-06 | NEW confirmed P1 Windows backend OCR defect; Rushab review required | OCR runner selects subprocess pipes; Windows selectors support sockets only. Reproduced WinError 10038/10093 and real API extraction_failed despite functioning Tesseract. Implement bounded portable process I/O; no backend edit made. |
| QA-07 | OPEN runtime configuration | Already-running backend retains old PATH and HTTP returns tool_missing. Restart BrandProof with Tesseract directory on process PATH after compatibility fix; do not alter SpeakEZ. |

Genuine poster contradiction and frontend real-box alignment remain unverified, not passed. Installation approved and completed normally; signature validity warning recorded in FINAL_QA_REPORT.md, no Windows security changes. Groq key absent in Process/User/Machine and root .env absent. No secrets exposed, paid calls, push/merge/deployment or backend/test changes.


### Post-install full-suite result - 2026-10-27

With `C:/Program Files/Tesseract-OCR` explicitly on process PATH, the unchanged full suite completed: **310 passed, 21 failed, 1 collection error, 0 skipped**, 119.76s. The 20 font-rendering failures and import-time collection error remain. Blank-image OCR still fails because production Windows pipe selection returns unavailable/extraction_failed despite a working engine; this is now the confirmed runner compatibility defect, not missing Tesseract. Evidence: `.cache/backend-sprint1-ocr-installed.log` and `.cache/qa-sprint1-ocr-installed.xml`. No further reruns can resolve unchanged prerequisites/code; Rushab review is required. Latest local health and frontend HTTP checks remain ok/200. No Groq credentials arrived during this run; genuine provider call remains blocked.


## Completion Sprint 1 fix verification - 2026-10-27 (latest)

- QA-04 RESOLVED for local core acceptance: real PNG/JPEG OCR/price contradictions and browser boxes work; one live consented Groq review completed with validated source v2 evidence, zero rejected findings and persisted results. Broader provider accuracy/edge acceptance remains separate.
- QA-05 RESOLVED on Windows: fixture font fallback/explicit override restores all formerly failing/collection-blocked tests. No font redistribution or assertion removal. Linux execution pending CI.
- QA-06 FIXED locally, RUSHAB REVIEW PENDING: bounded concurrent pipe I/O replaces Windows-incompatible selectors. Real extraction and safety-cap/timeout/cleanup regressions pass. See focused patch.
- QA-07 RESOLVED: backend restarted on 8001 with Tesseract PATH and .env settings; original synthetic QA database retained. SpeakEZ unaffected.

Exactly one provider admission recorded; automated regression server disabled external calls, then restored user .env enablement. No tokens/secrets logged. Initial backend pass 358 plus three new process tests; final combined count follows. Frontend 36 tests, lint/build, seven scripts and connected real-overlay browser suite pass. Refresh recovery and deployment remain open, not backend OCR blockers.


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

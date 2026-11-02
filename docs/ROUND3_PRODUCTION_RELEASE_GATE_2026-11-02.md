# Round 3 production release gate - 2 November 2026

**Recommendation: READY for an explicitly approved frontend-only release. Production is not deployed.**

The deployment candidate is **`5eac37660a7c4f53d17464dea3ced563486aa9bd`**. It is pushed to `YogitaKanwar/BrandProof`, branch `integration/round2-backend-pr1`, in [PR #14 targeting main](https://github.com/YogitaKanwar/BrandProof/pull/14). Later release-evidence documentation commits retain the same application/test/container/contract tree. They do not silently replace the pinned production candidate.

## Exact-commit CI

| Run | Result | Evidence |
| --- | --- | --- |
| Push, head 5eac376 | PASS, both jobs | [41473172383](https://github.com/YogitaKanwar/BrandProof/actions/runs/41473172383) |
| PR #14, head 5eac376 | PASS, both jobs | [41473406560](https://github.com/YogitaKanwar/BrandProof/actions/runs/41473406560) |
| Backend in production Docker image | **576 passed, 18 optional skips**, 94.06s in push CI | Sanitized `evidence/round3-release-preview/ci-test-counts.json` |
| Frontend | **62 passed, zero failures/skips**, lint and production build passed | Same run logs; `ci.json` records individual job/step conclusions |
| PostgreSQL 16 and migrations | PASS | Fresh startup, database-backed health, real caption/parser/OCR/approval/session workflows, six-step legacy upgrade/idempotence, measured-feature smoke |

The skips are the existing optional Linux-path Noto font matrix, not suppressed failures. Full required OCR/contrast cases ran. No assertion, timeout, validation threshold or backend product behavior was weakened. No new implementation was added during publication.

## Six judging requirements

These are the six requirements from the Round 3 brief, not six extra features.

| Requirement | Result and evidence |
| --- | --- |
| Deliver exactly the three promises | PASS within scope: PDF page provenance/pending/confirmation/versioned findings; supported colour/contrast/description checks; data-backed Governance Insights/sample guards |
| Complete loose ends | PASS exercised paths: description revision race fixed, deletion Cancel/Confirm/Undo, retained audit, resume/reset/logout, stale approval and actual conflicts; bounded OCR/logo/AI limitations remain disclosed |
| Invalid input, refresh, duplicates, empty/error states | PASS: unit/API regressions plus preview browser 503 and real 10-second timeout, one actual create after duplicate activation, invalid PDF/retry, draft preservation and refresh recovery |
| First-time judge clarity | PASS automated journey: passwordless demo → fictional campaign → References → Content → Results → Human Review → Insights; existing design preserved; keyboard and 1440/768/390/320px layouts |
| Genuine end-to-end testing | PASS: exact-commit Linux CI and three isolated-preview Chromium suites, both shipped PDFs over HTTP, real Tesseract/source boxes, human decisions, numeric measurements and evidence drilldown |
| Independently reproducible README | PASS exercised Windows clean source-copy install, locked dependencies, lint/62 tests/build, read-only migration check and actual restart; Docker/Linux path exercised by fresh CI; limitations and commands recorded |

No independent usability study, universal compliance, broad OCR accuracy or verified personal identity is inferred from these developer tests.

## Isolated preview acceptance

**[Open full-stack preview](https://brandproof-round3-preview-20261102.onrender.com/#/demo)**

- Render workspace `BrandProof` (`tea-dbgt7ne1egvs73e4jvug`), service `srv-dbkati8ae00c738bl1h0`, deployment `dep-dbkatioae00c738bl2p0`, source **5eac376**, observed LIVE.
- Explicit **Free** web plan, one instance, Singapore, automatic deployment **off**, no new paid database/provider. Preview SQLite is `sqlite:////app/data/round3-preview.db`; no production connection string, provider key or production record was copied. Preview data is disposable and is not a durable production store. Free service usage shares the workspace's free allowance.
- AI disabled; frontend/API served together by the exact candidate Docker image. Health 200/database OK; saved/live OpenAPI equal; JS and CSS SHA-256 match the tested local build.
- Three Chromium suites passed with fresh browser contexts: judge journey, strengthened combined improvements, and fault injection. Both-file PDF HTTP and Python measured-feature smoke also passed.
- Browser cases include demo entry and isolation, actual price contradictions/OCR boxes, PDF quotations/pending/Owner confirmation, supported 21:1 contrast against a 4.5:1 target, description revisions, reasoned human changes/decisions, Insights limits/evidence/history, refresh, reset/revocation/logout, deletion Cancel/Confirm/Undo and responsive layouts.
- Error journey injected 503 and a real transport timeout in that isolated browser, preserving the draft and restoring controls; duplicate activation sent one actual create. Wrong, blank, oversized and corrupt PDFs failed safely, followed by successful pending import.
- The original scripts' explicit host guards were adapted only for this exact preview hostname in ignored local adapters; behavioral assertions were unchanged. Error-result metadata explicitly identifies preview injection. No preview acceptance request targeted production/private data. Credentials/cookies/workspace IDs stayed in memory.

The automatically generated [Vercel frontend preview](https://brand-proof-jh29qzass-yogitakanwars-projects.vercel.app) is READY at 5eac376 (`dpl_5w7agRgTfwuJ4EY5GMTTB1JSWPDc`). Its committed `/api` rewrite points to the current production API, so it was **not** used for data-mutating preview acceptance. Its protection redirected a static request, and the connected protected-fetch tool returned 403. Protection was not weakened. The isolated Render full-stack preview is the accepted review environment.

## Poster-description workaround

The defect was reproduced before the existing fix: replacing a poster could leave the old description revision editable while its reload was pending, causing a 409 on save. Candidate `AltTextEditor` derives loading from the resolved campaign revision, disables edits during the read and refuses stale saves while retaining dirty text.

The isolated-preview combined journey explicitly replaces the poster, immediately edits and saves its description, and verifies success **without** `BRANDPROOF_MANUAL_DESCRIPTION_RELOAD`. Numeric contrast is measured on a genuine supported Noto72 black/white fixture; the antialiased Workshop image is still truthfully partial. No outstanding candidate description-reload defect was observed. The older current public UI still needs the documented explicit reload until this frontend is approved/released.

## Production compatibility, migration and recovery review

Current production: https://brand-proof-tau.vercel.app/ → existing Render `srv-dbgtr7nb9u1s73981s70` → PostgreSQL `dpg-dbgtpn5g1s2s73c9tg60-a`. Vercel production `dpl_C15g8rCKBDCfFtwHfmuasXycyb3P` READY and Render `dep-dbjn8b7f3r2c73cjfti0` LIVE both report **e01f52b6ee02b6c85c480619cfc82cc486a56123**.

`git diff e01f52b 5eac376 -- backend/brandproof pyproject.toml uv.lock Dockerfile` is empty. There is **no backend, schema, migration, dependency or Docker runtime delta**. The six migration definitions remain 0001 through 0006. The API contract is compatible/unchanged; frontend fixes use the existing endpoints and exact revision guards. No new production migration is needed.

Production migration state was checked without mutation: successful live startup was read from existing logs, definition identity was verified, and the read-only schema-history query was attempted. Direct SQL is **blocked by the empty external IP allowlist**, so a fresh row-by-row production migration inventory is not claimed. No allowlist/security setting was changed. Fresh PostgreSQL CI proves the isolated upgrade path, not an independent production audit.

Provider metadata confirms PostgreSQL 16 available on Free, expiry **27 November 2026 at 11:30:36 UTC**. Render production remains one Free instance with automatic deployment off and `/api/v1/health` configured. No full production backup or tested restore is verified. No paid upgrade, database cleanup or production mutation was performed.

**Recommended approved action:** release only the exact candidate frontend on the existing Vercel project/production alias; keep Render/API/database at e01f52b. All required user-facing fixes are frontend changes and the isolated-preview API equals production code. This avoids a backend restart/schema change and makes the lack of a full database backup an explicitly reviewed operational risk rather than an implicit migration assumption.

**Rollback:** retain production deployment `dpl_C15g8rCKBDCfFtwHfmuasXycyb3P`; if the approved frontend release fails the public synthetic smoke, restore that existing deployment/alias. It uses the same unchanged backend contract. This is a frontend rollback, not a database restore/downgrade. Do not reverse migration history or promise recovery of production data from an unverified backup. A backend redeploy or any new migration requires a separate reviewed recovery plan and approval.

## Approval gate / remaining limitations

- **READY for approval:** CI green; all three promises accepted within scope; isolated preview passes; description workaround fixed in candidate; no new migrations; frontend rollback and unchanged-data path reviewed.
- **HELD:** no production deployment, production migration or merge into main until the user explicitly approves the exact frontend release candidate. PR remains reviewable; merge permission is separate from preview permission.
- Known limits: cold starts/temporary proxy failures, free-database expiry, no verified full backup, external AI unavailable, text-layer PDFs only, bounded OCR/logo/visual/legal scope and synthetic actors. No unresolved new candidate defect affecting the exercised judge journey was observed.
- Vercel's protected preview cannot be fetched through the current connector scope; do not weaken protection. If production promotion later encounters a permission error, resolve the account/project authorization before any alternate release action.

Final PDF: `output/pdf/BrandProof_Round_3_Final_Submission.pdf`; editable source: `docs/ROUND3_SUBMISSION_CONTENT.md`. README and final QA/matrix were synchronized with this release review. Historical evidence stays separate under `round3-final/`; new CI/preview evidence is under `round3-release-preview/`. The leader still owns official submission and actual member declarations.

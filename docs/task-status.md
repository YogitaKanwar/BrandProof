# BrandProof task status

Updated: 2026-10-26. Branch: `integration/round2-backend-pr1`.

Six task flows are implemented and verified against the local API; four tasks remain partial. This is a local integration milestone, not final hosted acceptance.

| Task | Status | Implemented / remaining |
| --- | --- | --- |
| Y01 | Partial | App shell, navigation, real demo sessions and campaign create/list/get work. Server data persists; refresh loses memory-only demo access. Session resume and deployment remain. |
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
- Backend implementation is unchanged from PR #1. Latest frontend fixes/docs are included in this local checkpoint; no integration push, deployment or main merge performed.

## Verification observed

- Latest run: production build and lint passed; **33 frontend tests**, **all 7 genuine HTTP scripts**, and **19 browser check groups** passed on both dev `:5173` and production preview `:4173`.
- Real API coverage: campaigns/session/auth/errors, INR 499 pending v1 → approved v2, source/caption revisions, evidence, poster upload/private retrieval, corrections/comments, reviewer permissions, manual-note guards, receipts, stale approvals and explicit AI consent.
- Browser checks include the reported `/#/new` URL, visible owner confirmation, Run Review spinner/result focus, failed-request error focus, local deletion, mobile widths 390/320 and no uncaught JavaScript errors. Test data/notes are fictional scripted actions, not human feedback.
- Backend latest full run: **310 passed, 21 failed, 1 collection error**. Twenty failures plus collection are missing Linux Noto fonts; the other failure expects OCR partial but missing Tesseract produces unavailable. Backend Ruff lint/format passed. This suite is not fully green.

## Remaining blockers and acceptance

- **Session refresh:** no documented resume route. Rushab must provide a same-workspace resume/refresh contract that can restore authorised actor access without persisting bearer tokens in browser storage. No undocumented localStorage/sessionStorage workaround is used.
- **OCR / contextual AI:** local OCR returns `unavailable/tool_missing`; consented contextual checking returns unavailable because Groq is unconfigured. Real extraction, INR 499 vs poster INR 599, responsive real boxes and contextual claim/citation quality require configured-runtime testing.
- **Release:** public HTTPS API/frontend, CORS/private images, durable storage/restart, security/retention, accessibility/usability acceptance and submission evidence remain. No confidential-data or production-identity claims.
- **Deletion:** only browser-local drafts can be deleted. Backend campaign/poster deletion requires an actual API contract.
- See [configured-backend-tests.md](configured-backend-tests.md), [regression-report.md](regression-report.md) and [release-checklist.md](release-checklist.md).

## Manual review before push

1. Open `http://127.0.0.1:5173/#/new`, start connected review and create a campaign.
2. Add a price fact, save it, then explicitly confirm as owner. Enter a conflicting caption and save it.
3. Run review: check visible progress, actual results/evidence and unavailable coverage. For poster-only review, upload the file to the server first.
4. Exercise explicit corrections/comments and creator/reviewer controls. Source confirmation is not content approval; refreshing still loses demo access.

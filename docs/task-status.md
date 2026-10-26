# BrandProof task status

Updated: 2026-10-26. Current branch: integration/round2-backend-pr1.

## Repository safety

- Existing frontend is protected by pushed checkpoint a93f782 on frontend/connected-review-milestone.
- Fetched PR #1 and verified exact cdda60fd48371662a1380f82029836960271aa76. Merged cleanly into a new integration branch; main/checkpoint unchanged. No reset, force push or deployment.
- Read updated FRONTEND_HANDOFF.md, OpenAPI, STATUS, RUSHAB_TASKS, BACKEND_DEPLOYMENT and plan. Backend files equal PR #1; no backend fixes or test modifications made.

## Implemented slices

| Task | Current observation |
| --- | --- |
| Y01 | Campaign/session create-list-get reverified. Server persistence works; memory-only demo access still cannot survive reload. Deployment pending. |
| Y02 | Real typed sources, explicit owner confirmation, versions/history/validity/conflicts reverified. Guidelines stay unparsed local context. |
| Y03 | Real caption revisions, conflict reconciliation and review/history reverified; running/partial/completed/failed statuses supported. External AI consent is per request, default false and reset after a run. |
| Y04 | Raw PNG/JPEG upload, byte/pixel checks, canonical private retrieval, replacement and historical access connected. Real 401/409/413/415/422 verified. Server poster deletion has no contract. |
| Y08 | Frontend poster findings bind their historical poster_id and real boxes. Canonical percentage geometry scales responsively and rejects invalid bounds. Genuine extracted-box acceptance pending a working OCR runtime. No fake boxes. |
| Y06 | Persisted comments, explicit suggestion confirmation/application, caption revision history, before/current comparison, reviewer decisions/history and conflict preservation connected. |
| Y07 | Creator requests, separate demo reviewer approve/request-changes, required manual-check notes, receipts/history and stale readiness connected. Source confirmation remains separate. No prefilled notes or automatic approval. |
| Y05 | Existing evidence/coverage/stale display preserved; poster locations, OCR confidence, finding groups, running status and expanded server readiness supported. |
| Y09 | Local build/lint, 32 service tests and 15 browser groups pass. Seven genuine HTTP scripts pass. Backend full suite has environment failures below; hosted/manual usability acceptance remains. |
| Y10 | Current setup, integration/release handoff and separate configured-backend test checklist prepared. Public deployment/final submission remain pending. |

## Actual verification

- Frontend: production build/lint, 32 tests, 15 real browser journey groups; dev and production preview exercised during integration.
- HTTP: Y01 campaigns, Y02 sources, Y03 runs, private poster upload/retrieval/replacement, collaboration, approval and consent scripts pass. Fixtures are fictional; scripted reviewer notes are test actions, not real user feedback.
- Approval tests: creator denied; missing manual checks rejected; reviewer receipt recorded; caption/poster/source edits stale it; request-changes persists. Blocking findings still require explicit decisions before approval.
- Poster HTTP: actual OCR unavailable/tool_missing on this Windows host. Groq consent true returns unavailable because local provider configuration is absent. Neither is reported as successful inference.
- Backend pytest with continue-on-collection-errors: 310 passed, 21 failed, 1 collection error in 102.82s. Twenty failures plus the collection error are missing Linux Noto font resources; the other failure expects blank-image OCR partial but the absent Tesseract returns unavailable. Backend Ruff check/format pass (68 files). No environment-specific backend patches made.

## Remaining acceptance / deployment

- Continue independently per Yogita's instruction; do not install unrelated infrastructure or modify backend code. Configured runtime acceptance is listed separately in configured-backend-tests.md.
- OCR/Tesseract and live Groq/citation quality must be exercised on a configured backend; geometry tests and unavailable-state tests do not prove extraction/model success.
- Refresh/session-resume needs a backend contract change. No tokens in localStorage/sessionStorage/logs/URLs.
- Public HTTPS API/frontend, CORS, durable storage/restart, security/retention and human usability tests remain deployment gates. No hosted success or final task completion is fabricated.
- Use frontend/.env.example to configure a later public API location (never provider keys). Production requires actual API/reverse-proxy hosting, not Vite's dev proxy.
- See integration-sprint.md and configured-backend-tests.md for route mapping, local commands and final acceptance.

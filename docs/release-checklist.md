# BrandProof review / GitHub handoff

The connected local milestone is ready for team testing, not public deployment or final submission.

## Try the real flow

1. Start the backend from repository root: `.\.venv\Scripts\python.exe -m uvicorn brandproof.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log`.
2. In `frontend/`, run `npm.cmd run dev`; open http://127.0.0.1:5173/.
3. Preview mode -> Connect backend demo -> New Review; enter publication date -> Continue.
4. Add Price 499 INR -> Save pending fact -> Confirm as owner. Observe approved v2.
5. Save caption `Book for INR 599.` -> Run Review. Inspect contradiction, source evidence, coverage and partial/not-approved status.
6. Manually correct caption to `Book for INR 499.` and save. Old run becomes stale; new run may have zero findings but remains partial/not approved.
7. Inspect source versions and run history. Pasted guidelines are not automatically approved. Poster preview is temporary and not checked.

## Verified / outstanding

- Real API: demo sessions, campaigns, typed owner-confirmed sources, version conflicts, server caption revisions, synchronous exact-text reviews, persisted run history and evidence rendering.
- Frontend regression: service tests, real HTTP smoke scripts, browser keyboard/focus, stale edits, image validation and responsive widths.
- Backend foundation regression suite unchanged and exercised locally.
- Y01 refresh access needs an authenticated server-managed session-resume contract. Tokens remain memory-only.
- Y04 upload persistence, Y06 comments/decisions/full caption revision history, Y07 approval receipts/permissions workflow and Y08 OCR need backend contracts. No corresponding success is fabricated.
- Contextual AI is unavailable. Unsupported placement guarantees cannot be represented as proven false; unavailable semantic checking must remain visible. Poster price contradictions cannot be detected without OCR.
- Y09 needs team/manual usability feedback; Y10 needs hosted release verification and final submission materials.

## GitHub and deployment

Yogita authorised a checkpoint on branch frontend/connected-review-milestone. Scope: frontend source/config/lockfile/tests, task/release docs and AGENTS.md. Shared main and Rushab's backend remain unchanged. Runtime dependencies, databases, .env files and tokens are excluded by existing ignore rules. Later design changes can be committed on the same branch before deployment.

Deploy only after Yogita approves the connected journey, Rushab supplies a safe hosted API/session contract, and frontend/API integration is tested together at the actual URLs. A production Vite build alone does not establish deployment or connectivity.

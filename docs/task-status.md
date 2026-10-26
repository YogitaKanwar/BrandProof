# Task status

Updated: 2026-10-26

Yogita authorised continued planned frontend work. Yogita authorised a GitHub checkpoint on frontend/connected-review-milestone. No deployment or backend implementation changes.

| Task | Observed status |
| --- | --- |
| Y01 | API integration complete; overall partial: refresh access needs server session-resume, deployment withheld. Campaigns persist; tokens remain memory-only. |
| Y02 | Complete for current demo backend: typed rules, owner confirmation, pending/approved versions, editing, validity, history, conflicts and source revision refresh. |
| Y03 | Complete for synchronous exact-text milestone: real server caption saves/expected revisions, conflict comparison/reconciliation, review initiation with current revisions, statuses and persisted run history. No queued AI job claimed. |
| Y04 | Frontend picker/drop/validation/preview/replace/remove complete and tested. Persistent upload blocked by absent API; temporary previews explicitly disclosed. |
| Y05 | Complete for implemented exact-text scope: severity, evidence status, exact quotes/source versions, Unicode offsets, optional suggestions (never applied), coverage/excluded sources, partial/failed/current/stale runs and immutable snapshots. Contextual AI/posters unavailable. |
| Y06 | Partial: explicit caption corrections, reviewed/current server caption comparison and run history work. Comments, finding decisions and full caption revision history have no API. |
| Y07 | Blocked: no human content-approval/receipt API. Source confirmation is never portrayed as content approval. Stale review detection is not approval invalidation. |
| Y08 | Blocked: no poster upload/OCR/coordinate contract. No fabricated overlay or image result. |
| Y09 | Automated local regression/responsiveness/keyboard and focus checks implemented; manual team usability and hosted regression remain. |
| Y10 | Local handoff/release checklist prepared; hosted release verification and final submission materials pending. |

## Verification

- Production build and lint pass; 30 service tests, real Y01/Y02/Y03 HTTP scripts, and 13 browser check groups pass against the connected workflow.
- Backend unchanged: 100 pytest tests passed; Ruff check and formatting passed (31 files).
- Actual price case: owner-confirmed INR 499 v2 vs caption INR 599 -> supported contradiction with source/version evidence. Corrected caption -> zero findings, still partial/not_approved. Pending sources excluded; edits invalidate run currency while retaining history.
- Browser verifies owner confirmation/history, caption/source 409 conflict preservation, explicit reconciliation, no automatic correction, responsive widths, actual source links, and no tokens stored. Failed review requests must report failure without creating a fake run.
- Existing local fixtures preserved separately. Local-only draft deletion has confirmation/cleanup; server deletion disabled because no DELETE contract exists.

## Remaining release gates

- Y01: memory-only demo access cannot survive reload; Rushab must supply authenticated resume or explicitly change token policy. No localStorage token workaround.
- No contextual AI, poster/OCR, comments or human approval backend contracts. Unsupported guarantee claims must not be called proven false. A poster price contradiction cannot be evaluated without OCR.
- Safe hosted API, session/security work, actual hosted end-to-end verification and Yogita's design/release approval required before deployment.
- GitHub checkpoint branch: frontend/connected-review-milestone. Commit scope is frontend/docs/AGENTS.md; shared main and Rushab's backend history are preserved. Git author verified as YogitaKanwar. Runtime databases, tokens, node_modules, dist and .venv are excluded by existing ignore rules.
- Manual flow: :5173 -> Preview mode -> Connect backend demo -> campaign/publication date -> confirm price source -> Save caption -> Run Review -> evidence/history. See release-checklist.md.

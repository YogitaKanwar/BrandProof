# Local regression report — 2026-10-26

Tested frontend: http://127.0.0.1:5173/ and the exact /#/new entry; production preview: :4173; genuine API: :8000. Existing user records were not cleared: browser tests use a dedicated Chrome profile and fictional data.

## Fixes and coverage

- New Review starts a connected demo, and direct /#/new requires an explicit connection instead of silently creating a local-only draft. Local creation has its own /#/local-new route.
- Removed stale local-form wording implying Y02 was unimplemented. Saving a pending server fact scrolls/focuses the real owner-confirmation button.
- Late campaign reads cannot restore backend data after switching to local drafts.
- Visible mouse/input tests cover the exact direct URL, real INR 499 pending v1 -> approved v2, outage/retry without fake local success, and local deletion cancel/confirm/reload.
- Caption/source conflicts, explicit corrections, comments, reviewer finding decisions, empty manual-note fields, receipt persistence, stale approvals, image validation/upload/private retrieval, responsive layouts, token privacy and failed review requests are exercised.
- Browser errors are monitored: no uncaught JavaScript exceptions during the journey.
- Run Review now exposes a spinner/busy state, focuses and scrolls to returned results, and brings request errors into view. Genuine browser assertions cover busy feedback with network latency, visible result focus and failed-request error focus on dev and production preview. Results also explain when no approved reference facts were used.
- User-walkthrough regressions: cancel navigation/Back/reload with unsaved caption, explicitly discard without changing server text, block review with an unuploaded image, save caption after image selection, preserve a real concurrent-upload conflict until explicit reconciliation, and show actual approval/request-changes receipts on the dashboard. Added focused date validation, honest session-loss recovery text, sticky stage links and a direct Human Review shortcut.

## Results

- Build and lint: passed.
- Frontend tests: 33 passed, including expired-session handling without silently rotating the workspace.
- Real HTTP scripts: all 7 passed (campaigns, sources, reviews, posters, collaboration, approval, consent).
- Browser: 22 check groups passed at both dev :5173 and production preview :4173.
- Backend latest rerun: 310 passed, 21 failed, 1 collection error in 113.89s. Failures are missing Linux font/Tesseract prerequisites; backend lint/format passed. See task-status.md. This is not a fully green backend suite.

## Repeat

From frontend/, with the local API running: npm.cmd run verify. This stops on the first failing command; it does not turn a later success into an all-passed report.

For the full browser pass, also start dedicated Chrome CDP :9223 and preview :4173; set BRANDPROOF_RUN_BROWSER=1 and BRANDPROOF_TEST_BACKEND=1 before npm.cmd run verify. BRANDPROOF_TEST_URL can target :5173.

## Known incomplete behaviour

Refreshing loses memory-only demo credentials; the backend has no resume contract. Real local OCR reports tool_missing, and consented Groq checks report unconfigured/unavailable. Server campaign/poster deletion has no API. These are not claimed fixed or successful; configured-backend-tests.md remains open. Backend source was not modified and nothing was deployed.

# Editable-example caption initialization — 10 November 2026

Fixed and verified locally on `integration/round2-backend-pr1`. No commit, push, deployment, hosted-service request or hosted workspace reset was performed. Backend product code, API contract, dependencies and deployment configuration are unchanged. Existing unrelated working-tree changes are preserved.

**Root cause and request trace.** `startExample()` first creates a campaign with an empty caption at content revision 1 and publishes that provisional result into the workspace. `prepareExampleCampaign()` then creates/confirms the example sources, saves the caption at revision 2, uploads the poster (advancing the shared content revision to 3), and reads the completed campaign. The original page allowed its newly created Recent Reviews card to be opened before preparation completed. Opening any cached campaign also mounted the editor immediately while its opening GET was still outstanding.

`LiveCaption` initializes three independent React states from the first campaign props: `text`, `saved`, and `revision`. Those `useState` initializers do not run again when the same campaign's props change. A form mounted from the provisional record therefore kept empty text/saved state and revision 1 even after the parent held the actual saved caption at revision 3. The poster made Run review available. Preflight fetched revision 3, compared it with the stale form baseline, and correctly blocked the request. Explicit Use saved version repaired those local states, explaining the reported workaround. This was a form-initialization defect; no caption deletion request was needed to cause it.

The failure was reproduced locally using the committed `ReviewWorkspace.tsx` from `c99183645b31245230cbefc38161603cd58767b1`, with the remaining current frontend candidate files unchanged. A real source-creation request was held to expose the partly prepared card, the card was opened, and the actual request resumed. The editor remained empty despite saved revision 3; the first review was blocked and explicit Use saved version then returned HTTP 201. This controlled baseline establishes the timing-dependent defect; it does not claim to reconstruct the exact network timing of the user's hosted session or test the complete deployed bundle. Evidence: [baseline results](evidence/example-caption-init-20261110/before-fix/results.json), [empty editor](evidence/example-caption-init-20261110/before-fix/empty-editor-before-review.png), [blocked review](evidence/example-caption-init-20261110/before-fix/empty-editor-saved-revision-3-conflict.png).

**Fix.** The existing local preparation gate is retained and verified: the example editor cannot mount until setup finishes. Every connected campaign opening now waits for its saved-content GET before mounting the form, showing `Loading saved content…`. The caption and baseline revision initialize together from that acknowledged snapshot. A failed read exposes Retry loading content; it never exposes a misleading empty editable form. Route/request and retry identity prevent a previous visit's ready state being reused for a new opening; canceled route effects ignore their eventual responses. Query-only navigation keeps the current editor mounted.

The frontend API client's campaign GET cache now rejects responses whose content or source revision is older than the acknowledged cached snapshot. This prevents an older opening read rolling back a newer save or upload. The form still does not blindly copy later props into its editable text: unsaved edits, including an explicitly emptied draft, remain intact. No automatic caption-clear request is introduced. Existing explicit Save/Remove caption/reconciliation actions and both preflight and server 409 protection remain active. The prior local conflict-recovery improvement is retained.

**Files.**

- `frontend/src/ReviewWorkspace.tsx`: preparation/opening gates, saved-content initialization, route request identity and retry feedback.
- `frontend/src/api/backend.ts`: monotonic campaign GET cache updates for both revision counters.
- `frontend/src/LiveCaption.tsx`: documents the initialization boundary; retains the earlier local conflict-recovery changes.
- `frontend/tests/backend.test.mjs`: two regression tests covering late reads after a caption save and source-only revision advancement.
- `frontend/tests/first-review-browser.mjs`: real Chromium/API initialization, normal-first-example, slow setup, delayed response, empty edit, refresh, error/retry, poster-only and concurrent-conflict regressions, plus controlled baseline reproduction.
- `frontend/package.json`: exposes `npm run test:first-review`.
- This report, `docs/task-status.md`, `docs/configured-backend-tests.md` and sanitized evidence under `docs/evidence/example-caption-init-20261110/`.

**Fresh-browser demonstration.** Separate new Incognito contexts at 1440px desktop and 390px mobile launched an empty workspace and opened the example as their first campaign, with no artificial setup delay. The full caption appeared automatically with content revision 3/source revision 9. The first Run review returned HTTP 201 and eight real findings, without refresh or Use saved version. Both contexts also refreshed into the same saved campaign and successfully reviewed again. Zero caption-clear requests occurred during initialization. Screenshots were inspected.

- Desktop: [caption populated](evidence/example-caption-init-20261110/desktop-incognito/example-caption-hydrated.png), [first review results](evidence/example-caption-init-20261110/desktop-incognito/first-review-results.png), [sanitized result record](evidence/example-caption-init-20261110/desktop-incognito/results.json).
- Mobile: [caption populated](evidence/example-caption-init-20261110/mobile-incognito/example-caption-hydrated.png), [first review results](evidence/example-caption-init-20261110/mobile-incognito/first-review-results.png), [loading feedback](evidence/example-caption-init-20261110/mobile-incognito/saved-content-loading.png), [sanitized result record](evidence/example-caption-init-20261110/mobile-incognito/results.json).
- Timing regression: separate fresh contexts exercised slow setup and attempted early navigation. The form stayed unmounted until the real saved snapshot arrived; the first review succeeded. A held old opening response released after a new visit and unsaved edit did not replace that edit. An unsaved empty field survived comparison without a deletion request. Both explicit conflict-recovery choices and an actual review POST 409 caused by a concurrent write after preflight passed.

**Validation.** All 64 frontend unit tests, lint, production build and whitespace check pass. All 40 selected backend tests pass across `test_reviews.py`, `test_concurrency.py` and `test_posters.py`. Real local `test:reviews` and `test:posters` HTTP suites pass. The normal desktop/mobile initialization suites, full timing/poster-only browser regression and existing judge browser suite pass. The judge suite additionally covers actual OCR/source evidence, PDF, human request-changes, roles/isolation, desktop/390/320px layouts, refresh and local synthetic-session lifecycle. No independent human approval is claimed. Browser credentials remained in memory; result records contain no tokens or workspace IDs.

The initial backend test run had 35 passes and five OCR failures because Tesseract was absent from the process PATH. The existing Tesseract installation was verified and added to the local test-process PATH; no installation or product change was made. The rerun passed all 40 tests, and the browser demonstration was repeated with real OCR. HTTP poster fixture extraction remained honestly partial/low-confidence where applicable. External AI stayed disabled; successful review submission is not complete coverage or human approval.

Reproduce against a local backend serving the current build at port 8021 and isolated headless Chrome CDP at 9223:

```powershell
cd frontend
npm.cmd test
npm.cmd run lint
npm.cmd run build
npm.cmd run test:first-review
$env:BRANDPROOF_EXAMPLE_FIRST = '1'
$env:BRANDPROOF_TEST_SLOW_SETUP = '0'
npm.cmd run test:first-review
$env:BRANDPROOF_TEST_MOBILE = '1'
npm.cmd run test:first-review
```

Timing regressions remain loopback-only. A separate explicit preview opt-in permits only normal example-first/refresh smoke checks against the exact approved judge-preview host. `BRANDPROOF_EXPECT_INIT_BUG=1` is only for the isolated local baseline described above; it is expected to fail against the corrected frontend. Configured-runtime details remain separate in `configured-backend-tests.md`. The subsequently approved judge-preview release is tracked in `CAPTION_INITIALIZATION_RELEASE_2026-11-10.md`.

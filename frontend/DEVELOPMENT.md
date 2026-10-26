# Local frontend

From frontend/: npm.cmd run dev, npm.cmd run build, npm.cmd run lint, npm.cmd test.

Open http://127.0.0.1:5173/. Preview mode -> Connect backend demo explicitly creates an isolated fictional-data workspace. New Review takes an optional name plus a required publication date and creates a real backend campaign. Selecting it fetches its current caption/content_revision/source_revision. Campaigns persist on the server; the UI draft is a view of a campaign, not a persisted review run.

Demo workspace ID and all actor tokens live only in memory, never browser storage or logs. Creator credentials are used for Y01. Refresh ends access; starting another demo creates a different workspace. There is no resume endpoint. See docs/integration-checklist.md for the required backend contract change. The returned synthetic-demo notice appears in the connection disclosure. This is not production authentication.

Local drafts remain available in Preview mode and are not automatically uploaded. Connected mode uses real Y02 source APIs: Add Fact -> choose a typed rule -> Save pending fact -> Confirm as owner. Owner credentials come from the current in-memory demo session; no new workspace is created for source actions. Status, generated versions, validity and history come from the server. Edits require the actual expected_version and become pending again. Reload sources refreshes both sources and campaign source_revision. Conflict errors preserve unsaved entries; cancel and reopen the latest source to reconcile rather than overwriting it.

Pasted Brand Guidelines remain explicitly local context only. No PDF or free-text extraction is performed. Tone/claim_policy facts are stored guidance but not working contextual AI checks. Local guideline saving is separate from adding/confirming a typed source. Connected caption saves now use expected content revisions on the server. Save -> Run Review performs real synchronous exact-text checks using fetched content/source revisions; no queued AI job is claimed. Results display findings, evidence, source snapshots, coverage, exclusions and persisted history. Stale runs remain historical. Corrections require explicit editing/saving; suggested replacements are never applied automatically. Conflict comparison preserves your text and requires explicit reconciliation.

PNG/JPEG previews (5 MB maximum) remain memory-only and disappear on exit/reload; backend upload/OCR is unavailable. Source confirmation is not human content approval. Comments, finding decisions and approval receipts have no working APIs. See `docs/release-checklist.md` for team-testing instructions and outstanding task/deployment gates.

Start backend from repository root:

    .\.venv\Scripts\python.exe -m uvicorn brandproof.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log

Dev and preview proxy /api to localhost:8000. Production hosting needs an explicitly configured equivalent reverse proxy; building dist does not establish connectivity. Deployment is not authorised yet.

Checks:

- npm.cmd test: stubbed service/transport tests, no backend required.
- npm.cmd run test:api: real running localhost:8000, fictional isolated workspaces; no tokens logged.
- npm.cmd run test:sources: real Y02 source create/confirm/edit/history, rule kinds, revision/conflict/permission checks and a test-only HTTP review verifying pending exclusion.
- npm.cmd run test:reviews: real server caption revisions, review initiation, persisted results/history, stale runs and conflict handling. Zero findings remains partial/not approved.
- npm.cmd run test:browser: production preview :4173 plus a dedicated headless Chrome CDP session :9223 with a separate user-data-dir. Test clears only its browser profile's origin storage.
- Set BRANDPROOF_TEST_BACKEND=1 to include real API browser checks; set BRANDPROOF_TEST_URL=http://127.0.0.1:5173/ to target dev instead. Start preview after proxy config changes. Set BRANDPROOF_SCREENSHOTS=1 for screenshots under node_modules/.cache/brandproof-screenshots.

Original starter assets and the previous campaign-first workspace remain preserved. Backend source files are unchanged.

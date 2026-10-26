# Final integration: local handoff

Integration branch: integration/round2-backend-pr1. Preserved frontend checkpoint: a93f782. Backend PR #1: cdda60fd48371662a1380f82029836960271aa76. Backend implementation is unchanged.

## Local start

From repository root, install locked backend dependencies using uv sync --extra dev --locked. Run:

    .\.venv\Scripts\python.exe -m uvicorn brandproof.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log

From frontend/: npm.cmd run dev. Open http://127.0.0.1:5173/. Start an explicit demo session through Preview mode. Use fictional data only. Tokens/workspace stay in memory; reload loses access. New demo creates another workspace, not recovery.

The normal single-workspace flow is Sources -> Caption/poster -> Run Review -> Findings/corrections -> Comments -> Creator request -> Demo reviewer decision -> Receipt. Source confirmation is not content approval. Reviewer notes must describe checks actually performed, and automated coverage is never relabelled as passed.

## Contract connections

- Y01/Y02/Y03/Y05 retain the previous documented campaign/source/caption/review contracts, with current response additions.
- PUT posters?expected_revision uses raw File bytes and matching MIME; GET posters metadata and authenticated /posters/{id}/content create/revoke object URLs. No multipart/base64 upload. No DELETE route invented.
- Poster finding boxes are positioned as canonical pixel/dimension percentages. Findings fetch their own historical poster_id, never assume latest poster.
- GET revisions/comments; POST comments with both expected revisions. POST findings/{id}/apply requires a separate explicit UI confirmation and creates a caption revision.
- GET/POST findings/{id}/decisions uses expected_decision_version plus both snapshot revisions. Mutations use the documented creator/owner/reviewer tokens. Stale entries are retained for reconciliation, never blindly replayed.
- POST reviews/{id}/requests acts as creator. POST reviews/{id}/approvals acts as reviewer. Readiness comes from GET receipt and includes stale/manual-supplement states.
- Manual notes name exactly incomplete exact_text/contextual and, when attached, poster checks. Notes begin empty. Request-changes sends an empty manual_checks object. Server remains authoritative for role/self-approval/snapshot guards.
- external_ai_consent defaults false. Explicit checked consent sends caption and selected approved reference text to the server-configured provider. Credentials are never browser configuration. Each run clears the checkbox.

## Run checks

From frontend/: npm.cmd run build; npm.cmd run lint; npm.cmd test.

With backend running: npm.cmd run test:api, test:sources, test:reviews, test:posters, test:collaboration, test:approval and test:consent.

Browser: start production preview on :4173 and a dedicated headless Chrome CDP session on :9223. Set BRANDPROOF_TEST_BACKEND=1, then npm.cmd run test:browser. BRANDPROOF_TEST_URL can target :5173. Only the dedicated profile's fictional data is cleared. No real tokens are logged. Synthetic reviewer notes in tests are not human evaluation.

Actual results and runtime limitations are in task-status.md. Final configured-server checks are in configured-backend-tests.md. Build output alone is not deployment. Use VITE_API_BASE_URL or an actual production reverse proxy; BRANDPROOF_API_TARGET is only Vite dev/preview configuration. Never put Groq keys in VITE_ variables.

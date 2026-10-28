# Recent Reviews deletion release

This is a narrow backport onto production frontend `298c776` and backend `36cb8ae`, requested by the user. It does not deploy the broader improvements branch.

The dashboard exposes Delete on each saved review. Cancel performs no mutation. Confirm delete calls the owner-only, revision-checked API, hides that campaign from normal listing/access and offers Undo in the current page session. Undo restores the same campaign and retained evidence/history. Reload loses the in-memory Undo handle, but a confirmed deletion remains hidden. Local drafts retain their existing browser-only deletion behavior.

## Database and deployment

The existing startup `Base.metadata.create_all` adds only `campaign_removals`: campaign ID, unique deletion generation, actor ID and timestamp. No existing table/column is altered and no campaign, source, review, image, finding, comment, decision or approval is deleted. This is compatible with the future feature-branch migration `0005_review_removal`, which recognizes and validates this table. Do not deploy the broader migration stack for this release.

Startup upgrade/idempotence tests compare every legacy table schema and saved row before/after adding the table. A PostgreSQL-dialect compilation test checks the exact additive DDL and foreign keys; it is not a live PostgreSQL migration test. Local PostgreSQL/Docker executables and direct production SQL access are unavailable; database access restrictions were not relaxed and no production backup/export is claimed. Production remains on the existing persistent Render PostgreSQL 16 instance. A fictional session/campaign/source/review/poster/logo probe was seeded before deployment, retaining credentials only in process memory, for post-deployment persistence comparison.

Release order: validated integration commit → existing Render Docker deployment → backend health and contract → persistence probe → existing Vercel production deployment of that same source → public browser Delete/Cancel/Undo/reload checks. No main merge, new hosting, new service or provider change.

Rollback retains the additive table and all saved rows. Reverting to a backend without the removal filter makes previously hidden reviews visible again; avoid that application rollback after use unless this behavior is explicitly accepted. A frontend-only rollback can retain the updated backend filtering.

## Validation

Pre-release: 53 frontend unit tests, frontend lint/build, seven real HTTP suites and 26 existing local connected browser groups passed, including actual Tesseract, poster and logo-reference flows. The dedicated deletion browser check passed Cancel without a write, confirmation, same-review Undo, mobile confirmation, deletion persistence after refresh and unchanged workspace. Full backend suite and public acceptance results are recorded in the task/runtime acceptance logs after completion.

External contextual AI remains disabled/unconfigured in these checks. Render Free startup delays, bounded logo checking and the existing Free PostgreSQL retention deadline are unchanged.

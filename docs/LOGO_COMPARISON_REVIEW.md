# Reference-logo comparison - implementation and Rushab review

User requested this new feature on 2026-10-27. Changes stay local for Rushab review; no push, merge or deployment. No new dependencies or provider calls.

## User flow

In a connected workspace, Brand Information now includes Brand logo. Choose a tightly cropped PNG/JPEG reference with a plain background, upload it, then explicitly confirm as demo owner. Upload the campaign poster and run review. Logo comparison appears with real stored reference version and, when no close match is found, a Possible logo mismatch warning. Findings show the historical reference image beside the poster. This is in-app notification; no email or external message is sent.

## Scope and limitations

A bounded local RGB template search downsamples the poster to at most 160x160 and compares 16x16 samples at a finite set of scales/positions. It stops after two seconds. Raw similarity is an implementation metric, not a probability. It supports a constrained plain-background/template comparison; it is not semantic logo recognition or forgery detection. Similar candidates remain partial and require manual fine-detail verification. Missing/changed/obscured/tiny logos can all produce a possible-mismatch warning. Rotations, complex backgrounds, compression and very subtle alterations are not reliably resolved. A timeout or blank/tiny reference is not_assessed, not pass. No detected location is invented: uncertain findings have empty boxes and require whole-poster inspection. Use the existing manual poster notes/owner review; automated logo comparison never approves content.

## Persistence, roles and contract

Additive brand_logos table stores private canonical PNGs and append-only immutable versions. Owner upload creates pending v1; explicit confirmation appends approved v2. Replacement creates a new pending head and suspends old authority. Every mutation increments campaign source_revision, making old runs/receipts stale. Only owners upload/confirm; reads require authenticated same-workspace access. Image/byte limits reuse existing poster validation (5 MiB input, 16M pixels). Canonicalisation flattens transparency onto white; use a clear tightly cropped reference.

- GET /api/v1/campaigns/{id}/brand-logo: latest metadata
- GET /brand-logo/history: immutable metadata history
- GET /brand-logo/{logo_id}/content: authenticated historical canonical PNG, no-store
- PUT /brand-logo?expected_source_revision=N: raw PNG/JPEG, owner only
- POST /brand-logo/{logo_id}/confirm: expected_version and expected_source_revision, owner only

Review snapshots add approved logo metadata to sources_used; pending reference is explicitly excluded. Result is checks.poster.details.logo; uncertain mismatch adds category=logo, needs_clarification, actual reference-version/hash provenance and poster identity. Logo image bytes are never sent to Groq. Existing text-source/provider APIs unchanged. Existing poster incomplete/manual-note guard covers visual/logo checks.

## Validation and review

Focused comparison/API tests cover matching, changed, missing, blank/tiny/timeout, owner/creator/workspace permissions, size/type validation, confirmation conflicts, version history, source-revision staleness, persisted findings and immutable ORM snapshots. Connected browser exercises real reference upload/owner confirmation, PNG/JPEG poster reviews, warning and historical reference image. Full regression count is in FINAL_QA_REPORT.md. Synthetic samples are local ignored .cache/sample-brand-logo.png and sample-poster-logo-reference.png / sample-poster-logo-changed.png.

Rushab should review additive schema lifecycle, locking/snapshot identity, matching thresholds, CPU limits and false positives/negatives. Linux CI and representative real-logo evaluation remain open. Fine differences require manual review; do not advertise reliable detection of every altered logo. New table is bootstrapped with existing create_all; no existing data or table was deleted or reset.


### Final logo-feature verification - 2026-10-27

Full combined backend suite: **367 passed, 0 failed/errors/skipped**, 167.57s (.cache/backend-logo-combined.log / .cache/qa-logo-combined.xml). Backend Ruff lint/format and frontend lint/build/36 tests pass. Connected browser 25 groups pass with owner logo confirmation, real missing-logo warning, historical image and PNG/JPEG poster journey. Actual HTTP matching-versus-altered sample: matching candidate 0.9745/no warning; altered candidate 0.7329/one needs_clarification warning; both remain partial and persisted. Evidence .cache/logo-live-evidence.json; raw score is not calibrated confidence. Provider admissions remain exactly one from earlier Groq acceptance; no extra provider calls. Frontend :5174 returns 200 and backend health/database ok after feature restart. Focused new backend patch: rushab-logo-review.patch; scope/limits and Rushab review notes: LOGO_COMPARISON_REVIEW.md. No push/merge/deploy. Small alterations, rotations and complex/low-resolution backgrounds remain manual-review scope.


## Full-poster logo reference false reassurance fixed - 2026-10-27

User reported a visible logo mismatch despite similar-candidate result. Inspected latest saved reference/poster locally: reference was an entire 800x400 workshop poster (logo plus separated caption), and comparison reduced the whole foreground layout to 16x16. Changed small logo was overwhelmed by matching layout; score 0.9757 wrongly suppressed mismatch warning. Confirmed defect, not user approval or absence of an alteration.

Added conservative reference-suitability guard: widely separated artwork/text blocks produce not_assessed with an explicit logo-reference-needs-cropping finding, including on persisted real API review. Such references are no longer presented as similar candidates. This heuristic may also abstain on legitimate separated brand lockups; owner must provide a tightly cropped logo and inspect fine details. It does not solve all subtle-logo detection limits or silently approve/replace the user's reference. Existing user review remains historical.

Fresh verification: seven focused logo tests pass (new full-reference regression), backend Ruff pass, frontend lint/build pass, connected browser 25 groups pass, and genuine API reference/poster reproduction persists the new clarification finding. No additional Groq call; full 367-test result above predates this guard and is not claimed as a fresh full-suite rerun. Local server reloaded. User next step: upload logo-only reference, explicitly confirm and run a new review. No push/merge/deploy.


Publication note: .patch exports mentioned in historical evidence are local-only and excluded from GitHub. Review the committed backend files and tests directly in the GitHub commit diff.

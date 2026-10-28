# Implementation report — 28 October 2026

Follow-up: connected Recent Reviews deletion and Undo were implemented on this review branch and then released as a narrow production backport `639fe5f`. The public release passed 501 backend tests, 53 frontend tests, eight live HTTP suites, public delete/cancel/Undo/mobile/reload and cross-deploy persistence acceptance. The broader feature-branch checks remain the previously recorded 516 backend / 51 frontend tests plus 54 frontend tests after the startup fix. Original source/image/review history is retained; this is reversible removal rather than permanent erasure. See [release acceptance](REVIEW_DELETION_RELEASE.md) and [judging answers](judges-submission-2026-10-28.md).

The authorized improvements are implemented on `feat/brandproof-improvements-20261028`, originally based on deployed `36cb8ae95adf42a252808e08f8dcdf972627c360`. Only the startup fix and separate dashboard deletion backport are now public; the remaining feature code and migrations have not been released. The user requested preparation of the branch and PR text rather than connecting GitHub for automatic PR creation. Reconcile this branch with current integration before merging. See [PR text](improvements-pr.md).

## Implementation coverage

| Area / Prompt.txt recommendation | Result | Boundaries / remaining gate |
| --- | --- | --- |
| A: preconfigured demo | Implemented | Explicit action creates a separate fictional campaign, four confirmed sources, one pending policy, flawed caption and a generated real PNG; no seeded findings/approvals or edits to other campaigns |
| A: blank alternative/readiness/role guidance | Implemented | Persistent server-backed blocker checklist, actual finding IDs/source validity/request/author eligibility and required manual-note keys; synthetic role guidance, not production auth |
| B: contextual caption + OCR | Implemented | One bounded consented request, separate asset fields/offsets, high-confidence masking, exact quote/citation validation and real poster boxes. Positive live provider acceptance awaits private configuration |
| C: non-authoritative draft corrections | Implemented | Claim templates and contextual tone/policy candidates labelled unverified; explicit code-point-safe copy into an unsaved caption or poster wording scratchpad; explicit save/reupload and fresh review required. Semantic intent preservation is human-assessed |
| D: PDF/document ingestion | Implemented for PDF | Isolated bounded text-layer extraction, finite supported directives, immutable pages/digest/page quotes; pending candidates and explicit confirmation. Scans/unsupported/encrypted/resource-limited files do not produce invented rules. DOCX/general semantic extraction is outside this PDF scope |
| D: page evidence/source confirmation | Implemented | Exact page substring/offset verified, copied through confirmation to immutable source-version evidence; edits drop unsupported old quote attribution and require new confirmation |
| E: brand palette | Implemented within supported scope | Owner-confirmed flat-background hex/CIE76 tolerance; only dominant uniform border/background region measured. Gradients/photos/other regions abstain |
| E: contrast | Implemented within supported scope | High-confidence OCR boxes, uniform exterior background and dominant ink; relative-luminance ratio versus explicit source target. Bounded generated text/gradient/noise fixtures tested. No raster font/large-text inference or full WCAG/accuracy claim |
| E: accessibility descriptions | Implemented | Poster-specific immutable alt text, shared content revision/author locks and stale receipts; confirmed requirements check presence/literal reliable OCR price/date inclusion. Human semantic adequacy remains required |
| F: recurring issues/governance view | Implemented | Actual workspace records, distinct snapshot counting, source/version/finding links and latest disposition reasons. Observations are not all confirmed violations |
| F: ambiguity detector | Implemented as triage | Five reviewed distinct content revisions required before rates; >50% latest dismissal/exception rate can prompt owner inspection. Synthetic reviews are not independent human evidence |
| G: migrations | Implemented | Explicit numbered additive steps; legacy column/type/nullability baseline, SQLite/PostgreSQL transaction locks, drift/newer-version refusal, idempotent adoption. Fresh PostgreSQL upgrade/container CI must pass before release |
| G: automatic interrupted-run recovery | Implemented | 180-second worker leases, ten-second heartbeats, 30-second reaper plus startup/read recovery, ownership/expiry fencing. Existing unleased legacy runs retain the stopped-worker CLI; no unsafe fixed 45-second reaper |
| H: Free-compute logo behavior | Verified, limit retained | Real production search exceeded its bound and returned not-assessed/manual inspection; not converted into success or a larger CPU purchase |
| H: production upload/latency | Measured single sample | 5,155,064-byte PNG (98.33% of 5 MiB), HTTP 200, 10.32s including normalization/OCR. Random-noise OCR correctly partial/unreadable. No p95/load claim |
| H: provider quotas | Reviewed; unchanged | Application defaults remain 6/workspace/hour, 24/global/hour, concurrency 1/2. Production inference unavailable; effective account token/rate budget is not independently known. No assumed 100–150/hour increase |
| H: database persistence/expiry | Verified existing config | Render Free PostgreSQL 16 available, expiry 27 November 2026; existing actual redeploy persistence acceptance retained. No feature migration, new backup claim or retention purchase |
| Public deployment recommendation | Already satisfied before feature work | Existing Render + Vercel + Render PostgreSQL retained; Neon switch/Vercel-blocked assumptions are obsolete |
| Legacy demo component cleanup | Implemented | Removed unused CampaignWorkspace component from App.tsx; active local-draft services/types retained |
| Real SSO/team login | Deferred as recommended | Synthetic roles stay explicit; production identity is not claimed |
| Final metrics/epistemic boundaries | Updated in this report | Test counts are software regression evidence; manual audit and provider-quality evaluations remain separately scoped. Submission PDF not automatically rewritten/published |

## Changes and contracts

New backend modules: `migrations`, `review_leases`, `document_models`, `documents`, `pdf_extract`, `accessibility`, `visual_checks`, `readiness`, `insights`; integrated with existing `main`, `reviews`, `contextual`, `claim_screening`, `sources` and schemas. The legacy model tables were not altered.

Migrations: `0001_legacy`, `0002_review_leases`, `0003_guideline_documents`, `0004_alt_text`. New data tables: `schema_migrations`, `review_leases`, `guideline_documents`, `document_evidence`, `alt_text_versions`. No destructive downgrade is provided.

New routes:

- GET/POST `/api/v1/campaigns/{id}/guideline-documents`; raw application/pdf, `expected_source_revision`, encoded `X-BrandProof-Filename`, owner-only import, existing 5-MiB bound.
- GET/PUT `/api/v1/campaigns/{id}/alt-text`; creator/owner revision-checked save.
- GET `/api/v1/campaigns/{id}/readiness`; actual actor/scoped saved-state guidance.
- GET `/api/v1/governance-insights`; authenticated workspace scope and bounded history.

Additive source kinds: `brand_color`, `contrast`, `alt_text`. Sources may contain `document_evidence`; findings may contain `unverified_draft_suggestion`. Original verified apply semantics remain unchanged. Poster measured checks and alt-text snapshots are retained in immutable review JSON. The contextual consent description now includes extracted high-confidence poster text. `docs/openapi.json` equals the running feature API.

New UI: DocumentImport, AltTextEditor, WorkflowReadiness, GovernanceInsights and draft-copy handling; existing minimal design/review workspace retained. Insights deep links select the exact historical run/finding/source snapshot. Only pypdf was added as an application dependency, locked at 6.21.3. Docker's existing uv version is retained and accepts the frozen lock. No new secret or production environment setting was introduced.

## Fresh acceptance

| Check | Result |
| --- | --- |
| Full backend | 514 passed; 0 failures/errors/skips; 110.58s |
| Full frontend | 50 passed; lint/build passed |
| Backend lint/format | Passed |
| Seven genuine HTTP suites | Passed against isolated feature runtime |
| Existing browser regression | All 26 groups passed, actual Tesseract and local logo flow enabled |
| New HTTP acceptance | Passed PDF/quotes/pending/confirm, actual poster claim boxes, unverified drafts, measured background, alt-text revision, readiness/governance and scripted human approval/staleness |
| New browser acceptance | Passed expanded demo/poster, pending confirmation, readiness, explicit copy/save/review, actual PDF import/citations/confirmation, alt-text save, measured results, governance sample guard, exact historical links, 390/320px and cookie recovery |
| Visual QA | Desktop demo/checklist and governance, mobile workspace screenshots inspected; narrow layout did not overflow. Corrected new separator encoding and kept detailed metric methodology in a disclosure |
| Package | Backend wheel built, inspected for baseline/data inclusion and absence of cache/environment files; independent installed-wheel startup/migrations/health passed |
| Dependency/contract | pip check passed; pinned uv lock check passed; running/saved OpenAPI equal |
| New PostgreSQL/container CI | Configured for this feature branch and integration PR; completion must be verified in GitHub before release. Local Docker/PostgreSQL binaries unavailable; no local PostgreSQL pass invented |

The first full suite found an obsolete concurrency-test hook that assumed the run was still unflushed at commit. The updated hook observes both pending/flushed running runs and retains the same actual post-commit edit/currentness assertions. A browser race exposed incorrect “historical result” wording for merely unsaved drafts; saved-state staleness is now distinguished while draft actions/approval remain guarded. Final regressions pass. A QA navigation retry handles browser context changes; it does not fake product responses.

Evidence is local/ignored in `.cache/improvements-20261028/` and `frontend/node_modules/.cache/improvements/`. The PDF fixture and reusable HTTP/browser/CI probes are committed. Four Pillow deprecation warnings concern the still-supported `getdata` API; assertions pass. No OCR/LLM accuracy benchmark or independent real-user acceptance is claimed.

## Production observations and release gates

Public https://brand-proof-tau.vercel.app/ and Render API remain on deployed `36cb8ae`. Web is Free Docker, Singapore, one instance, automatic deploys off. No new service/provider, paid capacity, quota change, credential copy or public feature deployment occurred. Direct SQL inspection remains blocked by the existing empty external IP allowlist; it was not opened.

During the single resource probe, the first proxied health request returned 502 in 0.268s; after direct backend warming, proxied health returned 200 in 0.306s. Near-limit synthetic PNG upload succeeded in 10.32s. Review with the confirmed logo completed HTTP 201 in 3.994s with a truthful partial result and logo timeout/manual-inspection reason. This is not a controlled 15-minute sleep test or a load percentile. Existing redeploy/image/session durability evidence belongs to the prior release, not an unperformed migration of this branch.

Before release: review the prepared PR, pass Docker/PostgreSQL CI, approve a real production backup/restore plan, stop old workers, run migration check/apply in the intended database, then deploy the reviewed integration commit through the existing workflow and repeat public/redeploy acceptance. No force-push, main merge or deployment is authorized by this handoff alone.

Live contextual-provider acceptance is blocked by production configuration/credentials. Configure provider/model/key/enablement privately on the existing Render service if wanted; verify the actual account budget before changing quotas, and test with per-review consent. Do not paste keys into chat or frontend settings. The expiring database, cold-start availability expectation, manual logo verification and real-user/representative visual evaluation remain explicit operational/quality limits.

Original uncommitted documentation and the earlier assessment were backed up and preserved. Understandable stage commits are listed in the feature branch log. The final PR text is prepared for the user's requested manual opening; no PR creation is claimed.

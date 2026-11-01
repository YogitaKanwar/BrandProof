# Round 3 submission content — local candidate

Use after the final deployed workflow is verified. The current release is local only; public acceptance is pending. Do not paste “completed publicly” until the deployed build is checked.

## Project and links

BrandProof — evidence-first brand and advertising review. Team: YOGI2KANWAR.

Repository: https://github.com/YogitaKanwar/BrandProof

Repository homepage: https://brand-proof-tau.vercel.app (requires current release acceptance; API health returned 429 during this session).

Updated PDF: `output/pdf/BrandProof_Round_3_Release_Candidate.pdf`.

## Three improvements completed in the local candidate

1. **PDF guideline import with traceable evidence:** supported PDF text directives produce pending rule candidates with exact page quotations, validated offsets and document digests. Owners explicitly confirm versions. Modified rules retain history without falsely inheriting old quotation support. Unsupported/scanned pages and extraction limits remain visible.
2. **Measured visual consistency and accessibility:** flat background colour distance, reliable OCR-word contrast with measured colours/ratios/targets, poster-description requirements and literal price/date coverage. Ordinary antialiased text is supported; uncertain/complex images return partial coverage. Relevant edits invalidate earlier reviews and receipts.
3. **Governance Insights:** recurring categories across campaigns, exact guideline-version groups, latest dispositions/reasons and finding drilldown. Minimum sample and truncation notices prevent unsupported rates; the denominator and rerun policy are explicit. Regulation dispositions cannot recommend weakening law.

## Additional differentiator

A saved advertising profile selects jurisdiction, sector and language. Supported English claim signals for India receive frozen official CCPA 2022 clause 12(a) evidence on the existing claim finding. Reviewers inspect supporting material and record reasons. Each run pins its profile, publication date and pack; changes stale approvals. Dedicated notes handle incomplete coverage. This is bounded evidence review, not general legal advice or legal certification. The unverified coaching pack remains disabled.

## Technology and implementation

React 19, TypeScript and Vite frontend. Python/FastAPI/Pydantic/SQLAlchemy backend. Pillow normalizes images; real Tesseract returns OCR text/confidence/coordinates. pypdf runs in a bounded subprocess. Deterministic structured parsers, measured image samples and versioned English patterns perform the core checks. SQLite is used for isolated local acceptance; PostgreSQL models and an additive migration/CI path are prepared, with six schema steps. Optional external contextual AI requires server configuration and explicit per-review consent; live-provider quality is not claimed here.

The difficult work is evidence/currentness integrity: immutable source and content snapshots, exact quotations, real image coordinates, concurrent revision guards, author/requester approval restrictions, persisted human decisions, historical receipts and safe recovery. Advertising profile changes share source revision guards, while installed pack digests additionally protect approval currentness.

## Changes since the submitted plan

The three promised improvements were completed through bounded extraction, measurements and descriptive governance summaries. We repaired ordinary antialiasing sampling and made partial coverage explicit. We added a small cited India advertising-risk check rather than claiming broad legal understanding. Coaching-specific clauses remain disabled until the final official document can be verified. Existing manual review and immutable evidence remain authoritative.

## Unit Testing

BrandProof uses automated tests for brand fact validation, price contradiction detection, source versioning, content validation, permissions, invalid inputs and edge cases. Backend API tests and end-to-end browser checks exercise content submission, evidence-backed findings and human decisions, including stale reviews, self-approval restrictions, session recovery and workspace isolation.

**Verified results, 1 November 2026:** the final local backend regression suite passed **571 tests**, with **18 optional Noto-font cases skipped** and zero failures. All **59 frontend unit tests** passed. Frontend build/lint and backend Ruff/format checks passed. The earlier isolated acceptance also passed eight real HTTP suites and two genuine browser suites; current public release acceptance is recorded separately. The backend count includes API/regression tests and is not presented as a unit-only count. No line/branch coverage percentage was measured. The feature coverage above describes tested behavior, not universal correctness or OCR/model accuracy.

## User Handling

BrandProof provides one structured workflow for brand references, marketing content, findings and human decisions. It validates inputs and uploads, prevents duplicate submissions, preserves edits on failures, and shows loading, permission and recovery messages. Backend workspace and role checks protect access; versioned sources, immutable review snapshots and decision history preserve traceability. Changes invalidate earlier readiness instead of silently retaining an approval.

Guest access uses server-issued, hashed bearer credentials held only in browser memory and a protected 24-hour HttpOnly recovery cookie. Logout and reset revoke all guest roles server-side. These are synthetic demo roles, not verified personal or team identities. Production team sign-in is outside this guest model.

## Demo Account for Judges

Judges enter through the **Try Interactive Demo** button without creating a personal account or entering a password. The visible **Demo Credentials** section explains passwordless access and provides copyable Creator/Reviewer access instructions; it does not expose administrator, owner or database secrets. The direct `/#/demo` link shows the simple entry screen even when a browser has a saved session. **Continue Demo** preserves that session's workspace.

Each guest receives an isolated workspace. Judges can create their own reviews or choose the optional fictional workshop campaign inside the workspace, including a real uploaded poster, INR 899 approved reference versus INR 599 content, actual contradiction checking and a human-review workflow. Findings and approvals are not precomputed. Backend scope checks prevent access to another workspace; judges should use fictional, non-confidential material. Reset starts a separate workspace and revokes old access. AI requires server enablement and explicit consent and remains unavailable when unconfigured.

Scripted reviewer notes are QA, not independent feedback. Optional fonts, representative OCR/model quality and full accessibility certification are outside the verified results. See `JUDGE_DEMO_2026-11-01.md` and the dated configured-runtime acceptance for evidence and deployment status.

## Member contributions

Team-supplied ownership: Rushab Ramhari Patil — backend, OCR, AI/database and evidence integrity; Yogita Kanwar — frontend and integration. This slice was implemented with coding-assistant support. Final member declarations should describe their actual work and match team records/commits; no unverified hours or percentages are supplied.

## Before the leader submits

Finish team-owned deployment and fresh anonymous desktop/mobile acceptance. Replace local candidate status with verified deployed commits/results; ensure the working app, repository and PDF links open without sign-in. Confirm the exact final form format and deadline in the official instructions. No form submission is authorised or performed by this document.

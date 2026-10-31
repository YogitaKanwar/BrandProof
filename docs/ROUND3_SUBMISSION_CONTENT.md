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

## Testing notes

31 October 2026: 574 backend tests and 56 frontend tests passed; frontend build/lint, backend Ruff and whitespace checks passed. All seven frontend real-HTTP suites and the expanded improvements smoke passed against an isolated SQLite/Tesseract runtime with external AI disabled. Wheel packaging/import, API-contract parity and actual process restart persistence were verified. Evidence: `ROUND3_LOCAL_ACCEPTANCE_2026-10-31.md`.

Manual UI, current PostgreSQL/container execution and public release remain unverified due browser/Docker access restrictions and the user's local-release decision. Scripted reviewer notes are QA, not independent feedback. OCR and English patterns have explicit limitations; sampled contrast is not full accessibility certification.

## Member contributions

Team-supplied ownership: Rushab Ramhari Patil — backend, OCR, AI/database and evidence integrity; Yogita Kanwar — frontend and integration. This slice was implemented with coding-assistant support. Final member declarations should describe their actual work and match team records/commits; no unverified hours or percentages are supplied.

## Before the leader submits

Finish team-owned deployment and fresh anonymous desktop/mobile acceptance. Replace local candidate status with verified deployed commits/results; ensure the working app, repository and PDF links open without sign-in. Confirm the exact final form format and deadline in the official instructions. No form submission is authorised or performed by this document.

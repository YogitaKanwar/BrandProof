# BrandProof - Codex 48 Round 2

Implementation guide from Yogita's supplied requirements. Original reference: `plan.pdf`.

## Ownership and workflow

Yogita: React frontend, product workflow, UI integration, usability, deployment verification and submission.
Rushab: FastAPI backend, database, RAG, AI checks, OCR, permissions and approval logic. Do not modify backend files without approval.

Use React + TypeScript + Vite, primarily in `frontend/`, and existing dependencies. Complete one task at a time, run relevant checks, fix errors, and update `task-status.md`. Stop after Y01 for review before starting Y02.

## Tasks

| Task | Scope |
| --- | --- |
| Y01 | App shell, navigation, API client, campaign creation and frontend deployment |
| Y02 | Approved sources, pending/approved states, validity and versions |
| Y03 | Caption editor, revision saving and review job statuses |
| Y04 | PNG/JPEG upload, preview, replacement and errors |
| Y05 | Findings with severity, evidence, source references and suggested actions |
| Y06 | Corrections, comments, before/after comparison and revision history |
| Y07 | Human review, authorised decisions, approval receipts and stale status |
| Y08 | OCR-based poster highlighting with correctly scaled coordinates |
| Y09 | Accessibility, usability and regression testing |
| Y10 | Documentation, release verification and submission materials |

## Product requirements

- Approved workshop price INR 499 versus poster price INR 599: show a supported price contradiction.
- Unsupported placement guarantee: show missing substantiation, not a proven false claim.
- Changes after approval invalidate readiness while preserving history.
- Failed checks must never appear as successful reviews.
- Never fabricate AI findings, successful backend calls or approvals.

## Y01 implementation boundary

Build the shell, navigation, campaign form, API client, loading and error states. Preserve existing code. If backend is unavailable, use clearly labelled development fixtures and record real integration as blocked. Run the frontend build. Verify deployment only against an actual hosting target; do not claim a local build is deployed.


## User-requested extension: reference logo (2026-10-27)

Add owner-confirmed private logo reference, revision/history protection and conservative local poster comparison. Flag possible mismatch when a close match cannot be established; preserve uncertainty and manual visual review. Fine-detail/semantic logo verification is outside this initial template-comparison scope. See LOGO_COMPARISON_REVIEW.md and current QA reports for actual capabilities and evidence.

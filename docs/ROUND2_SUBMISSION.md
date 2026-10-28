# Round 2 submission handoff

Team: **YOGI2KANWAR**. The team leader submits once. No cloud project has been deployed; public access is not yet complete.

## Links and files

- Working project: **pending your own Render/Neon account setup and hosted acceptance**. Do not substitute a localhost link.
- Source: https://github.com/YogitaKanwar/BrandProof - currently **private**. Team owner must explicitly arrange public source access for judges.
- Updated PDF: [BrandProof Round 2 Build Update](submission/BrandProof_Round_2_Build_Update.pdf). Page 1 has editable URL fields. It is an accurate build update, not proof of a deployed product.
- Draft code PR: https://github.com/YogitaKanwar/BrandProof/pull/6
- Verified container/PostgreSQL run: https://github.com/YogitaKanwar/BrandProof/actions/runs/40671322353 (private repository access required).

## Completed features

Owner-confirmed typed references and version history; caption checks; real PNG/JPEG Tesseract OCR and extracted boxes; conservative reference-logo comparison; explained source/version-backed findings and partial coverage; explicit corrections/comments; human review requests, notes and receipts; stale readiness after edits; same-browser session recovery; an editable fictional example; and the complete-app container/free-hosting configuration. Optional contextual provider review requires configuration and per-review consent; default hosting does not enable it.

Validation: 445 backend tests, 47 frontend tests, build/lint/format, seven real HTTP scripts and three actual backend smoke scripts passed. The packaged browser app produced four findings and retained the exact campaign/review after reload. Container build, built UI, PostgreSQL 16 and real caption/parser/OCR/human workflows passed in CI. No new external model call or full dedicated Chrome/CDP rerun is claimed here.

## Technology and changes from plan

React/TypeScript/Vite; Python/FastAPI/Pydantic; SQLAlchemy/SQLite and CI-exercised psycopg 3/PostgreSQL; Pillow/Tesseract; optional consented Groq/OpenRouter with bounded approved-text retrieval and citation/span validation. Multi-stage Docker serves the frontend and API under one HTTPS origin. Proposed free hosting: Render Free + Neon Free, documented in FREE_HOSTING.md.

Scope reductions: typed owner-confirmed rules instead of automatic guideline extraction, keyword retrieval instead of vector search, bounded synchronous runs instead of a durable queue, and simulated roles instead of production membership. Added during the build: logo reference comparison, combined upload/review, browser recovery, editable example and one-origin hosting package. Missing/uncertain checks remain incomplete.

## Three Round 3 product additions

1. PDF/document guideline import with page-level candidate evidence, owner review and confirmed structured rules.
2. Measured visual brand checks for supported logo placement/clear space, colours and typography/contrast, evaluated on a frozen heldout poster set with abstentions.
3. Real authenticated team membership and review queue, plus recurring confirmed-issue analytics linked to actual runs and human decisions.

## Remaining handoff

Follow FREE_HOSTING.md, then verify the actual public app in a private window, exercise review-to-human-decision, and test persisted campaign/images after sleep/redeploy. Fill the verified project URL in the PDF, confirm team/leader details and make all submitted links public. The supplied email's hard deadline is 28 October 10:00 AM IST; this file does not establish an extension or on-time submission.

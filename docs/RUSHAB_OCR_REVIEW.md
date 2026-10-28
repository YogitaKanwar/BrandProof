# Rushab review: Windows OCR and portable image fixtures

User authorised these focused backend fixes on 2026-10-27. Changes remain local and uncommitted. No push, merge or deployment. Backend working tree had no existing edits before this fix.

Review the backend files and process regression tests in the GitHub commit diff. Local .patch exports are not published.

## Problem and change

Windows selectors cannot monitor subprocess pipes, causing extraction_failed even with functioning Tesseract. The runner now uses three concurrent workers: input writer, bounded stdout reader and bounded stderr reader. It preserves the overall timeout, output/diagnostic caps, nonzero-exit handling, shell=False, memory-only image transfer and existing TSV parsing/coordinates. Failure kills and reaps the child before joining workers.

Fixture generation now tries installed Noto, DejaVu, Windows Arial or macOS Arial, with BRANDPROOF_TEST_FONT for an explicit path. Missing fonts still fail meaningfully. No fonts redistributed; no assertions deleted or skipped.

Focused files:

- backend/brandproof/ocr.py
- backend/tests/test_ocr.py
- backend/tests/test_ocr_process.py: real subprocess output/stderr cap and blocked-input timeout/cleanup tests
- scripts/workflow_smoke.py

The frontend browser suite also adds opt-in BRANDPROOF_TEST_OCR checks comparing actual API boxes with rendered image coordinates at 1440/390/320px. No UI redesign.

## Evidence and review scope

41 targeted OCR/poster tests and three new process tests passed. Real PNG/JPEG INR 599 posters produced contradictions against approved INR 499 source v2, real boxes and persisted findings. Browser geometry passed within 1.5 CSS pixels; the mobile screenshot was inspected. Frontend lint/build/36 tests and seven API scripts passed. Final combined backend count is recorded in FINAL_QA_REPORT.md.

One consented Groq request with the existing model completed contextual checking, yielded one validated claim finding with zero rejections, and persisted unchanged on retrieval. Overall review remained partial. Automated regressions temporarily disabled external AI to avoid additional model calls. No provider implementation changes or secrets in this diff.

Windows is exercised. Linux execution remains for CI. Review worker cancellation, bounds and cleanup, then run Linux tests with English Tesseract. API/schema/auth/database behaviour is unchanged. Session recovery, public deployment and human usability acceptance remain separate.


### Final combined verification - 2026-10-27

**Backend: 361 passed, 0 failed, 0 errors, 0 skipped in 132.09s.** Full suite includes the three new real-pipe regressions. Evidence: .cache/backend-completion-final.log and .cache/qa-completion-final.xml. Ruff lint/format pass. Frontend lint/build/36 tests, all seven real HTTP scripts and connected browser 23 groups pass. Actual PNG/JPEG INR 499-versus-599 poster contradictions and desktop/mobile genuine-box alignment verified. Exactly one Groq provider admission, successful validated/persisted result, no retry. Backend is restored with .env Groq enabled and Tesseract PATH on 127.0.0.1:8001; health/database ok, docs 200, frontend :5174 returns 200. SpeakEZ still identifies on :8000 unchanged.

No immediate user setup action is needed. Rushab review and Linux CI remain required before merging the focused backend diff; same-workspace refresh recovery, deployment, broader model evaluation and human usability acceptance remain separate. Nothing pushed, merged or deployed.

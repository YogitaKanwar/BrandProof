# Authorized improvements implementation

Feature branch: `feat/brandproof-improvements-20261028`, based on production `36cb8ae`.
Original local documentation additions and assessment are preserved and remain uncommitted. Production deployment requires review; this feature branch must not auto-deploy.

## Stage G1 — migrations and interrupted-review safety

- Added explicit numbered additive schema steps, an inspected legacy baseline, schema drift/newer-version refusal, SQLite writer locking and PostgreSQL transaction advisory locking. No drop/alter/destructive downgrade. `python -m brandproof.migrations --check` reports pending steps; `--apply` applies them. Back up and stop old workers before production migration. An older application may run with additive tables retained; do not delete them to roll back.
- Added worker-owned 180-second leases, ten-second heartbeats and finalization fencing. Expired leased runs recover to partial/unavailable on startup or review reads, preserving findings/inputs. Healthy slow workers renew; legacy unleased jobs retain the stopped-worker recovery CLI.
- Focused migration/lease/contextual/manual-recovery suites: 122 passed. Existing frontend production build/lint passed. Full PostgreSQL/container acceptance remains a separate final stage; no production migration was run.

## Stages B/C — contextual OCR and unverified draft candidates

- One bounded provider request can include separately labelled caption and high-confidence poster OCR, with independent offsets and original asset identity. Low-confidence words are masked without shifting Unicode offsets; invented/uncertain spans are rejected and accepted poster findings receive actual OCR boxes. Consent disclosure now includes extracted poster text, never image bytes. Missing configuration/outages still produce incomplete coverage. Quota defaults are unchanged.
- Findings can contain `unverified_draft_suggestion`; `suggested_replacement` remains reserved for the existing verified path. Local claim signals receive a conservative draft template. Contextual tone/policy candidates remain explicitly unverified. Caption copy validates the current code-point span and preserves surrounding copy, changes only the unsaved editor, blocks approval while dirty, and requires explicit save/new review. Poster wording uses a separate scratchpad and requires image revision/reupload.
- Focused contextual/assets/review/claim tests: 149 passed with actual Tesseract on PATH. An initial missing-PATH OCR case was corrected as QA setup, not hidden as a pass. Frontend 50 tests, production build/lint and backend lint/format passed. OpenAPI updated. Live provider quality is not claimed by offline transport tests.

## Stage D — bounded PDF guideline import

- Added locked pypdf dependency and migration `0003_guideline_documents`, retaining legacy tables. PDF parsing runs in an isolated worker with a 15-second timeout, 5-MiB input, 30-page, decompression/page/total-text and output bounds, and a 256-MiB address-space cap on Linux. Windows has the same timeout/byte/text bounds but no equivalent OS memory cap in this implementation. Encrypted/invalid/resource-limited input is rejected without creating sources.
- Owner-only raw-PDF import supports explicit price/date, quoted terminology, required-text, tone and claim-policy directives. It is intentionally not general document understanding. Exact extracted page quotes and offsets are verified before creating pending sources; original PDF digest, filename and immutable extracted pages are retained. Confirmation copies provenance to the approved version; editing a rule requires new confirmation and does not falsely carry the old supporting quote.
- UI supports import, extraction status/page inspection, pending source cards, exact citations and normal explicit confirmation. Blank/scanned/unsupported pages return no invented rules. The original plan.pdf was not extracted or changed.
- Six focused PDF/source/migration tests passed, including generated real text/blank/encrypted PDFs, conflicts, role restrictions, provenance preservation and upload limits. Frontend build/lint/50 tests passed. A Windows temporary-directory permission issue was avoided using workspace-owned QA directories; a cache-write warning did not affect assertions.

# Latest-branch local restart and retest — 30 October 2026

Result: local app starts and the exercised core/PDF/background/alt-text/governance flows work. Contrast measurement has a reproducible supported-image failure. This is not an all-green acceptance or a public-deployment test.

## Runtime and provenance

- Branch: `feat/brandproof-improvements-20261028`, commit `ca6dd8c20c0338656b523a1689693bded6413d7a`.
- Existing uncommitted `backend/brandproof/approval.py` edit and `docs/ROUND3_SCOPE.md` were retained. No application/test code was changed during this retest.
- Installed the frozen project environment with `uv sync --frozen --extra dev`; this added the branch's declared `pypdf==6.21.3` dependency. No dependency manifest or lockfile changed.
- Built React and served it with FastAPI at `http://127.0.0.1:8001/`.
- Isolated SQLite database: `/home/KARMA/Documents/Codex/2026-10-24/i/work/round3-retest-20261030/brandproof.db`. Existing databases were not migrated or reset. All five additive migrations applied on this fresh database.
- Real local Tesseract 5.5.3, English data, Noto Sans fixture font; two CPU threads. External AI explicitly disabled/provider `none`.

## Automated evidence

| Check | Observed result |
| --- | --- |
| Full backend suite | **513 passed, 3 failed**, 47.99 seconds, four Pillow deprecation warnings |
| Frontend unit tests | **54 passed**, zero failures/skips |
| Frontend production build and lint | Passed |
| Backend/scripts Ruff lint | Passed |
| Backend/scripts formatting | Failed only on the pre-existing uncommitted approval edit |
| Diff whitespace | Failed on that edit's extra blank line at EOF |
| Saved/live OpenAPI | Equal; PDF, alt-text, readiness and governance routes present |
| Feature real-HTTP smoke | Passed pending PDF evidence/confirmation, actual OCR claim boxes, unverified drafts, background measurement, alt-text revision, readiness/governance, scripted human approval and staleness |
| Seven frontend real-HTTP suites | Passed session/campaign, sources, reviews, posters, collaboration, approval and consent suites |

The poster HTTP suite truthfully reported partial/low-confidence OCR for its small fixture. Consented contextual requests remained unavailable because the provider was disabled; no live model acceptance is claimed. Scripted reviewer attestations/exceptions are test actions, not real user feedback.

Full-suite XML: `/home/KARMA/Documents/Codex/2026-10-24/i/work/round3-retest-20261030/backend-tests.xml`.

## Manual browser evidence

1. Created the separate editable fictional example through the UI. Real saved caption, poster and reference cards appeared; the pending claim policy and readiness blockers were visible.
2. Explicitly confirmed the example policy, then generated eight actual findings across caption/poster. Source evidence, real OCR highlights, unverified draft labels and incomplete coverage were visible. Readiness remained not approved.
3. Imported the committed fictional `guidelines.pdf`: three pending candidates appeared. Expanded document evidence showed page 1, exact quotation `Alt text: required` and offsets 51–69. Confirmed candidates explicitly.
4. Reran review: measured background was `#FFFFFF`, colour distance 0 against tolerance 10. Missing description produced an alt-text finding and partial accessibility coverage.
5. Saved a poster description. The content revision changed and the earlier result became historical. A fresh review removed the alt-text finding and reported completed coverage for the documented presence/literal-text scope only.
6. Explicitly copied an unverified claim suggestion to the caption editor. Copy remained unsaved, Run review was disabled, and the UI required save/review. Saved and reran successfully.
7. Opened Governance Insights: real category counts, source-version groups and the insufficient-sample guard appeared. Expanded underlying evidence and followed its exact run/finding/source-version link; the correct finding received focus.
8. Restarted the actual server and reloaded the browser. The same demo identity/campaign and selected saved review returned. All 17 existing review snapshots had identical IDs/caption/findings/checks before and after restart, confirmed by a credential-free digest. This precedes the additional contrast reproduction campaign.

Screenshot: `/home/KARMA/Documents/Codex/2026-10-24/i/outputs/round3-retest-20261030/measured-checks.png`.

## Confirmed issues

### Contrast sampling abstains on simple antialiased text

Three existing `test_real_rendered_text_contrast_samples` cases fail: black on white, white on black and grey on white. They render Noto Sans 72px text and expect a contrast measurement; `word_colours` returns `None`.

The same issue reproduces outside the fixture bounds: a real PNG containing black `TEST` on white is uploaded through HTTP, Tesseract completes with `TEST` at approximately 91% confidence, and a confirmed minimum-ratio rule is used. Review returns contrast `partial`, zero measurements and one unmeasured word. Readiness stays `not_approved`; no fabricated passing ratio is shown.

Cause: `visual_checks.py` requires one exact RGB foreground colour to cover at least 80% of non-background ink pixels. The Noto black-text sample has 76.61% because edge antialiasing produces other shades. This is an implementation limitation in ordinary supported text, not a missing OCR engine/font. The same algorithm also refuses the real OCR box.

Suggested repair for a separate authorised fix: evaluate conservative colour clustering/antialiased-edge handling while preserving uncertainty on gradients, noise, multicolour text and unreliable backgrounds. Add real-OCR and multiple-font coverage for high/low contrast; do not simply relax every abstention to make the three assertions pass.

Reproduction metadata: `/home/KARMA/Documents/Codex/2026-10-24/i/work/round3-retest-20261030/contrast-failure.json` (no credentials).

### Existing local approval edit fails formatting

The pre-existing edit adds three statements after the function's return and a trailing empty line. Those statements are unreachable. Ruff format and whitespace checks fail on that file; lint and exercised approval workflows pass. The edit was preserved exactly, not silently removed or included in a commit.

## Boundaries

No production database, hosted deployment, paid service or live model was changed. No push/merge/deploy occurred. Fresh PostgreSQL/container acceptance and representative visual/LLM accuracy were not run here. Existing browser CDP scripts were not executed; the manual browser cases above used the available in-app browser. This retest does not establish all-input coverage, independent user testing, legal compliance or full accessibility.

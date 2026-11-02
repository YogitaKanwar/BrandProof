# Round 3 requirements matrix - 2 November 2026

Classification: **VERIFIED** = the stated bounded behavior was exercised; **PARTIAL** = verified subset with an explicit gap; **FAILED** = observed failing acceptance; **NOT TESTED** = no fresh execution evidence. A completed extraction or merged PR is not production acceptance. Exact commands/results are in `ROUND3_FINAL_QA.md`.

## Current status matrix

| Requirement | Implemented? | Tested? | Deployed? | Evidence | Remaining gap |
| --- | --- | --- | --- | --- | --- |
| PDF import/provenance/confirmation | VERIFIED | VERIFIED local; public judge/PDF suites | VERIFIED e01f52b | test_documents, test_demo_guidelines, test_round3_acceptance; final local/public artifacts | Bounded text-layer/directive scope |
| Measured colour/contrast/description | VERIFIED | VERIFIED local automated/combined browser | e01f52b; current public combined result in QA | test_visual_accessibility; improvements_smoke; browser screenshots | Complex-image uncertainty remains explicit |
| Governance Insights | VERIFIED | VERIFIED API boundaries and local browser | e01f52b; current public combined result in QA | test_insights, test_round3_acceptance; browser evidence links | Minimum sample and truncation limits retained |
| Error-message hardening | VERIFIED candidate | 62 frontend tests and local fault-injection browser | NOT DEPLOYED | client.ts; y01.test; errors/results.json | Specific production release approval |
| Poster-description revision race | VERIFIED candidate fix | Real replacement → immediate edit/save Chromium regression | Older public UI needs explicit saved-description reload | AltTextEditor; strengthened improvements-browser | Remaining gates/approval |
| Current README/report | VERIFIED candidate | Clean setup/render results in QA | Repository patch; no publication claimed | README; Markdown source; generated final PDF | Official submission remains team action |
| Docker/PostgreSQL/legacy upgrade | VERIFIED | Exact 5eac376 push and PR CI passed | Deployed schema unchanged | Runs 41473172383 / 41473406560; release-preview/ci.json | Final production approval |

## PDF cases

| Cases | Status | Actual evidence / scope |
| --- | --- | --- |
| Compact/extended shipped PDF; full campaign import → quote → pending → confirm → conflicting/corrected review | VERIFIED | test_demo_guidelines; pdf-guidelines-live; judge/combined browser; no automatic approval |
| Two supported pages and mixed supported/blank pages | VERIFIED | test_round3_acceptance; test_documents; exact page offsets/readback |
| Blank and actual image-only PDF | VERIFIED | test_documents; final Pillow-created raster-only PDF; no invented candidates |
| Encrypted, corrupt, invalid, wrong MIME, >5 MiB, >30 pages | VERIFIED | test_documents; genuine browser wrong/empty/oversized/corrupt/retry |
| Worker timeout, text/candidate cap, narrative with zero rules | VERIFIED | test_documents; no imports on timeout |
| Reimport, duplicates/conflicting confirmed rules | VERIFIED | Reimports remain pending; test_documents/test_reviews clarify conflicts |
| Wrong role, stale import/confirmation version | VERIFIED | test_documents/test_sources, sources-live |
| Unconfirmed rules excluded; confirmed quotes immutable | VERIFIED | sources/reviews/document API tests; shipped-file HTTP |
| Edited rule loses unsupported citation; immutable old version retained | VERIFIED | test_documents |
| Publication validity, version updates, history and refresh recovery | VERIFIED | test_source_coverage, source-api tests, judge/combined browsers |

## Measured visual/accessibility cases

| Cases | Status | Actual evidence / scope |
| --- | --- | --- |
| White/black and low-contrast grey; exact threshold comparisons | VERIFIED | test_visual_accessibility uses real rendered text and real OCR HTTP |
| Approved/mismatched flat background, actual target/delta/tolerance | VERIFIED | Palette unit/API tests; improvements_smoke |
| Missing, whitespace, present/updated description; revision conflict/stale approval | VERIFIED | Visual/accessibility and workflow API tests, approval HTTP |
| Default installed font and ordinary antialiasing | VERIFIED | Real Noto fixture; no threshold change |
| Noto Sans/Serif/Mono × size × colour matrix at Linux paths | NOT TESTED here | 18 optional cases skipped; historical Linux evidence is separate |
| Noise, gradients, mixed ink, small/thin text, partial OCR, 100-word cap | VERIFIED | Conservative unit/API uncertainty fixtures; partial/unassessed scope |
| Broad real photographs, arbitrary rotated text/fonts/layouts | PARTIAL | Bounded abstention is implemented; no representative field benchmark or universal abstention guarantee claimed |
| Full WCAG, typography, complete visual conformity | NOT TESTED | Explicitly outside product scope; no certification |

## Governance cases

| Cases | Status | Actual evidence / scope |
| --- | --- | --- |
| Zero, one, four, exactly five, six distinct reviewed snapshots | VERIFIED | test_round3_acceptance asserts every boundary, actual persisted API decisions |
| Counts/categories across campaigns; exact source-version separation | VERIFIED | test_insights |
| Identical reruns, no inherited decisions, latest reopen/reason | VERIFIED | test_insights |
| Missing/whitespace reason rejected | VERIFIED | Final test asserts 422 before valid disposition |
| Deleted campaign exclusion, workspace isolation/401 | VERIFIED | test_insights, removal HTTP, judge isolation |
| Run/decision truncation and evidence links | VERIFIED | MAX_RUNS and MAX_DECISIONS regression tests; combined UI deep links |
| Refresh/readback | VERIFIED | Repeat API readback; browser reload/history recovery |
| Regulation dismissal never recommends weakening regulation | VERIFIED | test_insights regulatory grouping |
| Representative organizational trends/customer outcomes | NOT TESTED | Only fictional synthetic data; descriptive triage, not a benchmark |

## Robustness, usability and release

| Cases | Status | Actual evidence / scope |
| --- | --- | --- |
| Delete Cancel/Confirm/Undo, owner permission, audit retention, stale Undo | VERIFIED | Removal API and combined Chromium |
| Refresh, expired/revoked session, reset/logout, independent judges | VERIFIED | judge-demo-browser and session API/unit tests |
| 503, real 10-second timeout, retry, preserved draft and duplicate activation | VERIFIED local | round3-errors-browser; one actual create request after two activations |
| Cold public startup | PARTIAL | Initial 502/45s harness failure retained; direct health recovered in ~22s and warmed public judge/PDF passed; not an idle-latency guarantee |
| Source/content conflicts and stale approvals | VERIFIED | Sources/reviews/approval HTTP and backend guards |
| OCR/logo timeout handling and interrupted review recovery | VERIFIED bounded behavior | Existing process/recovery/uncertainty suites; live logo quality remains limited |
| Desktop/tablet/mobile/keyboard | VERIFIED automated | 1440/768/390/320px; keyboard entry/finding focus; no independent usability study |
| Current candidate container/PostgreSQL CI | VERIFIED remotely | Exact 5eac376 CI: 576 backend passes, 18 optional skips; frontend 62 passes; fresh/legacy PostgreSQL upgrade and actual workflows passed |
| New production migration/deployment | NOT TESTED / NOT REQUESTED | No schema/product-backend changes; production remains e01f52b |
| Backup/restore, prolonged idle and near-limit production latency | NOT TESTED | Release/operational gaps retained explicitly |

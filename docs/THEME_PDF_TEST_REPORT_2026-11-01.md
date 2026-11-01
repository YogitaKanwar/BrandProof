# Navy/sunshine restoration and PDF verification - 1 November 2026

## Changes

- Restored the established dark blue `#1E2640`, sunshine/Desert Sun `#DC9750` and warm background `#F8F5EF`. Removed the Emerald workspace override and recolored the demo entry, role cards and demo controls to the same original palette. Layout and existing workflows are preserved.
- The three-rule Workshop PDF already used INR 899. The separate seven-rule extended PDF still used INR 499, which disagreed with the current Workshop reference. Corrected the extended file to INR 899 and updated its generation source. Recolored the smaller PDF to navy/sunshine and visually checked both actual PDF renders.
- Kept `docs/plan.pdf` and the historical Round 3 report unchanged. No backend application, database model, migration, approval rule, OCR threshold or provider setting changed.
- Added a collapsed explanation of the PDF import/confirmation/review sequence and labelled the extended download as seven rule types.

## What actually matches

The PDFs agree with the Workshop's declared reference values. The demonstration marketing content deliberately conflicts with those values.

| Rule | Workshop PDF | Extended PDF | Existing Workshop reference | Demonstration content |
| --- | --- | --- | --- | --- |
| Main price | INR 899 | INR 899 | Owner-confirmed INR 899, v2 | Caption and poster show INR 599: supported contradiction |
| Campaign date | 2026-11-12 | 2026-11-12 | Owner-confirmed 2026-11-12, v2 | Caption says 2026-11-13: contradiction; the poster has no supported date expression |
| Required wording | Terms apply | Terms apply | Owner-confirmed Terms apply, v2 | Missing from the sample caption/poster: finding |
| Preferred terminology | Not included | affordable instead of cheap | Owner-confirmed affordable instead of cheap, v2 | Caption uses cheap: contradiction |
| Flat background | Not included | White, #FFFFFF | Available through explicit PDF confirmation | Only reliably supported poster backgrounds are measured |
| Minimum text contrast | Not included | 4.5 | Available through explicit PDF confirmation | Requires reliable OCR-word/background measurement |
| Poster description | Not included | Required | Available through explicit PDF confirmation | Add an actual description; it is not generated or attested automatically |

The compact PDF is a **three-rule subset**, not a complete duplicate of the extended guidelines. The extended PDF has seven supported rule types and shares all four existing confirmed Workshop facts. The additional pending claim policy is not declared in either PDF.

## Verified PDF workflow

1. Import the actual PDF bytes through the API. The compact file produces three candidates; the extended file produces seven.
2. Each candidate starts **pending v1**, with its exact page quotation and offsets. Successful extraction does not activate a rule.
3. Inspect the source document, then explicitly confirm as the sandbox Owner. Confirmation produces **approved v2** and retains the document citation/history.
4. Run the real engine on `A cheap workshop on 2026-11-13. Book for INR 599.`. Confirmed PDF rules produce actual price/date/required-wording conflicts, and the extended PDF also produces the terminology conflict. The price finding cites the real approved v2 rule containing INR 899.
5. Save `An affordable workshop on 2026-11-12. Book for INR 899. Terms apply.` as another content revision and re-review. The supported caption price/date/wording/terminology checks match, but the receipt remains **not_approved**, with no approval records.

The isolated matching-caption test has no poster attached. In the interactive sample, the attached INR 599 poster must also be corrected and reuploaded; fixing the caption alone does not resolve poster findings. No findings, boxes, decisions or approvals are precomputed.

### How a judge can use it

Open a campaign, then **References > Import PDF guidelines > Load fictional workshop guidelines > Import as pending candidates**. Inspect the extracted page text and quotes; confirm the rules explicitly. In **Content**, save the caption/poster and choose **Run review**. Inspect source versions and actual findings under **Results**, then use **Human Review** for a real decision. The direct demo entry stays simple; this import UI is inside the workspace.

Previously imported PDFs and confirmed source versions are not rewritten when a public sample file changes. An old INR 499 import remains historical evidence. Import the corrected file as pending and explicitly reconcile differing confirmed prices before relying on a new review.

## Scope and limits

PDF parsing supports the **text layer and explicit supported directives**, up to 5 MiB / 30 pages, with bounded text/candidate extraction. Scanned or image-only guideline PDFs require manual transcription in this importer. Poster PNG/JPEG OCR is a separate feature.

A rule/value match does **not** verify the PDF's authenticity, prove who owns the brand, establish that an arbitrary document is the same as the official guidelines, or certify complete visual/legal/brand compliance. The checker compares saved content against confirmed supported rules. Unsupported narrative guidance, typography, logo placement, ambiguous expressions and incomplete checks require the existing manual/consented review paths. Source confirmation is separate from content approval. Optional external AI remains unavailable when unconfigured.

## Tests and evidence

| Check | Current result |
| --- | --- |
| Full backend API/regression suite | **573 passed, 18 optional Noto-font cases skipped, zero failures/errors**; 591 collected, 114.51 seconds |
| New real-PDF API tests | **2 passed**, included in the full count; both actual shipped PDFs, including Docker asset location |
| Frontend unit suite | **59 passed**, zero failures |
| Frontend production build and lint | Passed |
| Backend/scripts Ruff lint and formatting | Passed |
| Eight existing real HTTP suites | Passed on the fresh isolated runtime |
| New `npm run test:pdf` real HTTP suite | Passed for both distributed files: pending/confirmation, exact quotations, conflicting and matching captions, no automatic approval |
| Judge Chromium suite | Passed; actual navy/gold computed styles, mobile/keyboard, same-session entry/reload, real OCR/review, PDF/reference consistency, roles/isolation/reset/logout |
| Expanded improvements Chromium suite | Passed; explicit drafts, PDF confirmation, descriptions/measured checks, Insights/history and removal/Undo |
| PDF visual QA | Both actual browser PDF renders inspected; INR 899 is legible and no layout defects observed |

The reused local runtime initially reached its intentional hourly demo quota. The remaining suites passed after restarting the isolated local process with the same normal 20-session / 300-operation limits. Production quotas and logic were not weakened. The small poster HTTP fixture truthfully returned low-confidence OCR; the Workshop sample separately completed OCR and produced real price boxes. Scripted QA notes are fictional test actions, not independent human feedback.

Feature coverage is described above; **no code line/branch coverage percentage was measured**. Optional font cases, representative OCR/model quality, full accessibility certification and real brand-owner verification are not claimed.

Evidence: `evidence/navy-pdf/` contains sanitized results and screenshots. Source checks: `backend/tests/test_demo_guidelines.py`, `frontend/tests/pdf-guidelines-live.mjs`, `frontend/tests/judge-demo-browser.mjs`. Pytest XML: ignored `.cache/navy-pdf-tests.xml`.

## Release status

Local candidate verified. Production deployment of the requested theme/PDF correction and public acceptance will be recorded here separately from these local results. No production migration is required.

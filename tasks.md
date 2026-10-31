# BrandProof — Round 3 implementation handoff to Sol

Prepared by Astra, 31 October 2026. This is an implementation plan, not a report of completed work. Check off tasks only with recorded evidence.

Implementation update, 31 October: local implementation and automated acceptance for T00–T06 are complete. **574 backend tests, 56 frontend tests, seven real-HTTP suites and the expanded improvements smoke pass.** The PDF report, fictional sample, legal scope, submission copy and release handoff are prepared. Evidence: `docs/ROUND3_LOCAL_ACCEPTANCE_2026-10-31.md`. Checkboxes below record local implementation/evidence; they do not assert public or manual UI acceptance. Browser acceptance and PostgreSQL/container execution remain unverified due tool access restrictions. The user explicitly requested a local-only release; deployment/integration/public gates are deferred to the team-owned hosting account. Final personal contribution declarations remain the team's responsibility.

## Goal and product decision

Finish the three improvements actually promised in Round 2, then add a small, credible India advertising-risk feature. The judge should independently complete this path:

**Import guidelines → inspect quotations → confirm rules → submit caption/poster → see measured, explained findings → inspect evidence → record a human decision → receive a current approval receipt.**

Governance Insights should then show where review friction recurs and let an owner inspect the underlying decisions. Legal-risk findings join this workflow; they are not a separate chatbot or a claim that the product certifies compliance.

Priority order: reliability → promised features → bounded legal checks → public acceptance and submission evidence. Complete the three promises even if the legal extension has to remain smaller. No design overhaul, production authentication rebuild, vector database or new queue is required.

The supplied final-round window is 31 October 2026, 23:59 IST through 3 November 2026, 23:59 IST. Preserve honest commit/build provenance and check the final event rules before submission. Do not submit the form on the user's behalf.

## Read before editing

- `AGENTS.md`, dependency manifests and lockfiles.
- `docs/ROUND3_SCOPE.md`: actual submitted commitments; overrides older proposal drafts.
- `docs/LOCAL_RETEST_2026-10-30.md`: latest recorded acceptance evidence and failures.
- `docs/improvements-implementation.md`, `docs/task-status.md`, and current API contracts. Older passing counts do not supersede the latest failing run.

Baseline inspected: branch `feat/brandproof-improvements-20261028`, commit `ca6dd8c20c0338656b523a1689693bded6413d7a`. Recheck before work; do not assume this is current `main` or the public release. PDF, visual checks and Insights already exist here: extend and repair them rather than building duplicate systems.

Existing dirty files at handoff:

```text
backend/brandproof/approval.py
docs/configured-backend-tests.md
docs/task-status.md
frontend/src/App.css
frontend/src/ReviewWorkspace.tsx
docs/LOCAL_RETEST_2026-10-30.md (untracked)
docs/ROUND3_SCOPE.md (untracked)
```

Preserve these changes. The approval edit predates this plan; inspect its intent before removing unreachable statements. Preserve the user-selected Dark Blue `#1E2640` / Desert Sun `#DC9750` styling, cream workspace, compact navigation and mobile layout. Do not restore the older teal palette from stale instructions. Coordinate with Yogita before concurrent frontend editing; use separate worktrees for simultaneous editing sessions.

## Baseline and release blockers

| Area | Existing implementation/evidence | Required next step |
| --- | --- | --- |
| PDF import | Bounded text extraction, exact page/offset evidence, pending candidates and confirmation | Verify failure cases, edited-rule provenance and public usability |
| Visual checks | Flat-background measurement, contrast sampler, alt-text checks | Repair ordinary antialiased-text sampling; retain conservative abstention |
| Insights | Workspace-scoped persisted summaries, version groups, evidence links, minimum sample | Verify denominator, rerun/decision semantics and cross-campaign examples |
| Core workflow | Revision guards, immutable runs, decisions, stale receipts and session recovery | Regression-test changes through approval and restart |
| Legal extension | Existing bounded English claim screening; no accepted legal pack | Implement curated applicability, provenance and review integration |
| Latest recorded tests | Backend 513 passed / 3 failed; frontend 54 passed; build/lint passed | Obtain a fresh all-green result after repairs; PostgreSQL/container and public checks remain |

All three failures are contrast tests in `backend/tests/test_visual_accessibility.py`. Formatting also fails on the pre-existing approval edit. Historical local passes are not proof of public deployment or general accuracy.

## T00 — Establish a safe, reproducible baseline

- [x] Inspect branch, diff, relevant instructions, running processes and environment; preserve unrelated edits. Fetch remote state if integrating, but do not automatically switch branches, reset, merge or force-push.
- [x] Use the project virtual environment and frozen dependencies. Use `agent-env` for generic tooling; limit CPU/OCR work to two threads and run one heavy task at a time.
- [x] Use a separate test database and fictional data. Do not migrate/reset a live database during development.
- [x] Inspect the unreachable statements after `return` in `backend/brandproof/approval.py`; resolve deliberately, preserving intended behaviour and verifying approval guards.
- [x] Record baseline and subsequent test commands/results in a dated report. Do not add credentials, session tokens or private documents to reports.

Done: reproducible environment, cleanly understood diff, agreed branch and isolated test data. Keep commits focused; this handoff does not request pushing, merging or deployment.

## T01 — Repair and finish measured visual checks (release blocker)

Primary files: `backend/brandproof/visual_checks.py`, `backend/tests/test_visual_accessibility.py`, review/readiness integration and corresponding UI.

The confirmed defect: `word_colours` requires one exact foreground RGB to account for at least 80% of ink. Ordinary antialiased Noto Sans text yields about 76.61%, so black-on-white, white-on-black and grey-on-white examples all abstain. Real Tesseract boxes reproduce it; it is not merely a synthetic-box test issue.

- [x] Implement conservative core-ink/colour-cluster handling for antialiased edges. Do not simply lower all confidence thresholds or force a measurement from every box.
- [x] Preserve abstention for mixed foregrounds, uncertain backgrounds, gradients, shadows, noisy/compressed inputs, unreliable OCR and truncated sampling. Bound runtime and pixel work.
- [x] Show measured foreground/background, contrast ratio, configured threshold and measurement scope. Clearly separate measured failure from inability to measure. (Implemented and built; manual UI acceptance pending.)
- [x] Preserve flat-background colour comparison and display the observed colour, target, distance and tolerance. Do not describe this as a whole-brand visual audit.
- [x] Verify missing/present/empty alt text, description edits and affected revision/receipt staleness. Presence checks do not establish semantic adequacy.
- [x] Do not infer WCAG large-text status from raster pixel size alone; explain the configured threshold and limited sample coverage. Never label an entire poster WCAG compliant from sampled words.

Acceptance: existing three regressions pass; test multiple available fonts/sizes, high and low contrast, real OCR boxes, threshold boundaries and unsupported inputs. For ideal black/white inputs the measured ratio should be approximately 21:1 within documented tolerance. Low contrast produces a measured finding; uncertainty remains partial rather than passing. One real upload must reproduce this through the UI, including word evidence and approval handling.

## T02 — Complete PDF import acceptance

Primary files: `backend/brandproof/documents.py`, `pdf_extract.py`, `document_models.py`, `backend/tests/test_documents.py`, `frontend/src/api/documents.ts`, relevant workspace panels.

Keep the existing bounded text-PDF pipeline and limits. Do not add external extraction or scanned-PDF OCR for this release.

- [x] Distinguish document imported, pages extracted, supported candidates found, and candidates confirmed. Successful extraction is not complete guideline coverage.
- [x] Each candidate exposes original filename/digest, exact page quotation and validated offsets. Confirmation is explicit and owner-only, with expected-revision protection.
- [x] Show page-specific unsupported/scanned/blank outcomes; mixed documents may have useful candidates and incomplete coverage simultaneously.
- [x] Preserve original document evidence and immutable source versions. A materially edited rule must not falsely present an old quote as support for the new rule; show its manual provenance and history.
- [x] Explain duplicate/conflicting candidates without silently activating them or inventing precedence. Inspect existing behaviour before adding a duplicate-resolution mechanism.

Acceptance cases: valid supported PDF; scanned-only; mixed text/scanned; text with no supported rules; malformed/encrypted; oversized/page-limit/timeout; quotation offset integrity; non-owner confirmation; stale revision; repeat upload; edited candidate; subsequent source edit and historical run readback. Verify the current configured limits rather than hardcoding different ones in UI copy.

Done: a judge can import a committed fictional fixture, inspect evidence, confirm a candidate, run a check against it and return to the exact historical source version without help.

## T03 — Make Governance Insights trustworthy and useful

Primary files: `backend/brandproof/insights.py`, `backend/tests/test_insights.py`, Insights UI and API types.

Current implementation retains the latest run per campaign/content/source revision, uses latest finding decisions, groups by category/source version, requires at least five distinct reviewed campaign/content snapshots for its signal, and bounds loaded runs/decisions. Verify these details against current code before changing them.

- [x] Label category recurrence separately from reviewer disagreement. Show observation counts, reviewed counts, distinct-snapshot count and the denominator beside rates.
- [x] Explicitly define handling of dismissal, exception, reopen, changed decisions and identical reruns. Current latest-run selection can exclude decisions on an older identical snapshot: document and test that policy, or deliberately implement stable deduplication. Never silently multiply repeated runs or decisions to reach the threshold.
- [x] Keep guideline-version signals tied to the exact immutable version. Aggregate categories across campaigns without pretending unrelated source IDs are one shared guideline.
- [x] Keep insufficient-sample and truncation notices visible. Present signals as reasons to inspect a guideline, not proof it is wrong or a model-accuracy score.
- [x] Evidence drilldown includes campaign, run, finding, source version, latest decision/reason and a working deep link. Deleted/inaccessible campaigns must follow the product's existing visibility policy without leaking other workspaces.
- [x] Include new legal findings as their own category/provenance where applicable; do not let Insights recommend weakening a regulation because reviewers dismissed it.

Acceptance: zero data; below threshold; exactly threshold; repeated runs; changed/reopened decisions; multiple campaigns; multiple source versions; deleted campaign; truncation; cross-workspace isolation. Use clearly labelled fictional fixtures for a meaningful demo, never present seeded decisions as real customer analytics.

## T04 — Curate the legal scope before coding its detector

Product name in UI: **Advertising-risk checks**. Initial scope: selected English advertising claims for India. Start with the 2022 general advertising guidelines; add coaching-specific checks only after the final 2024 instrument and applicability are verified. Other jurisdictions/sectors remain explicitly outside coverage. Do not present ASCI self-regulatory codes as statutes.

Official research starting points, checked 31 October 2026:

- [CCPA 2022 Gazette notification](https://consumeraffairs.gov.in/public/upload/files/CCPA_Notification_1732707665.pdf): conditions for non-misleading advertising and disclaimer requirements support bounded claim/substantiation review. A slogan match alone does not establish a breach.
- [CCPA official guidelines index](https://www.ccpa.doca.gov.in/guidelines): retrieve the final instruments and check for amendments/supersession before freezing a pack.
- [PIB announcement of final coaching guidelines, 13 November 2024](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2073013&lang=2&reg=48): describes restrictions on misleading success, selection and outcome claims. This is a discovery/summary source; obtain the final instrument for exact clause citations. Do not use the February 2024 draft as the final law.
- [Department of Consumer Affairs Acts index](https://consumeraffairs.gov.in/pages/consumer-protection-acts): authoritative starting point for the Consumer Protection Act framework. Do not claim to implement the entire Act.

- [x] Create a small curated pack with stable rule IDs, jurisdiction, instrument type/title, final official URL, exact verified clause/page, brief supporting quotation, source checksum, source retrieval date, effective dates where verified, pack version, supported signals and limitations.
- [x] Separate legal text from the product's interpretation/detection heuristic. Every heuristic needs a reviewed rationale and explicit limits; do not assign a clause from memory or fabricate it with a model.
- [x] Check current amendments. Retrieval date is not enactment/effective date. If final text or applicability cannot be verified, keep that rule disabled and document the gap.
- [x] Require a campaign review profile: target jurisdiction, sector and publication date. Explain what is required for the selected pack; leave unknown facts unknown. Do not infer legal applicability solely from currency, address or a brand name.
- [x] Curated packs are application-maintained references. Owners select an applicable profile; confirming a brand guideline cannot edit, waive or override a legal instrument. Arbitrary uploaded PDFs must not become trusted law.

Done: a small auditable rule manifest and applicability matrix, not a broad legal knowledge base. A general pack is the minimum; a coaching pack is conditional on verified final-source evidence. Record exactly which clauses are supported, not just the instrument title.

## T05 — Implement legal-risk evaluation and immutable provenance

Suggested new module/data fixture names are proposals; follow existing architecture after inspection. Reuse bounded claim screening and the existing review pipeline rather than adding a second review engine.

- [x] Add explicit coverage results: completed for the stated bounded scope, partial, not assessed, and not applicable. Missing profile or unsupported language/sector must not yield a clean legal pass.
- [x] Start with a few reviewed signals: absolute outcome promises, time-bound results, and coaching selection/placement guarantees when applicable. A signal requests substantiation/context; it does not declare the claim false. Test negation, quotations and ordinary warranty/refund language to reduce false positives.
- [x] Produce findings with exact content span, caption/OCR origin and OCR coordinates when available, matched signal, why it needs review, selected jurisdiction/sector, immutable rule/pack version, official evidence and a concrete reviewer action.
- [x] Pin legal profile and pack content/version in each review snapshot. Extend review currentness/deduplication to include legal configuration; old runs remain readable after profile/pack updates. Switching profile or changing relevant evidence must stale affected approval receipts.
- [ ] Use additive migrations and backwards-compatible defaults. Existing runs without legal metadata show not assessed, not silently passed. (Implemented; fresh/legacy SQLite tests pass. PostgreSQL/container execution remains unverified because Docker access was denied.)
- [x] Preserve content length limits, OCR confidence/partial coverage and execution budgets. Do not send private material externally by default. Optional LLM calls remain consented, bounded and unnecessary for the core demo; model output cannot invent sources or legal conclusions.
- [x] Link overlapping brand claim-risk and legal findings clearly. Avoid two indistinguishable alerts for the same span; keep each supporting reason and provenance accessible.

Example behaviour:

| Input/context | Expected product behaviour |
| --- | --- |
| “Guaranteed results in 30 days” | Flag a supported outcome/time-bound signal for substantiation; explain scope and source, without claiming the promise is necessarily unlawful |
| “No results are guaranteed” | Negation control: do not flag as a positive guarantee |
| Coaching advertisement: “100% selection guaranteed” | Apply verified coaching rule when profile matches; request relevant evidence and human review |
| “30-day money-back guarantee” | Do not misclassify as guaranteed performance; unsupported refund conditions may need manual review |
| “Red Bull gives you wings” | Do not claim literal falsehood or brand disapproval from this phrase alone; metaphor/general truth analysis is outside the bounded detector |
| Missing profile, unsupported language or unreliable OCR | Explicit not-assessed/partial coverage; no invented legal verdict |
| Risky claim plus “T&Cs apply” | Disclaimer presence must not automatically resolve the claim finding |

## T06 — Integrate human review, readiness and UI

Primary integration points: review orchestration, `backend/brandproof/readiness.py`, `approval.py`, frontend readiness types, review cards, historical snapshots, receipts and Insights.

- [x] Add a compact profile control and collapsible risk section within the existing workspace. Keep brand-source evidence distinct from regulation evidence; no new crowded dashboard or legal chatbot.
- [x] Finding card answers: what was found, why it matters, what source supports the concern, what is uncertain, and what the reviewer should check next. Prefer “Evidence needed” / “Needs review” over “Illegal” / “Legally approved.”
- [x] Reuse reasoned human decisions. Reviewers can record supporting evidence/reference and rationale; explicitly distinguish “evidence supplied” from independently verified truth. Preserve reopening and decision history.
- [x] Unresolved findings and incomplete coverage participate in readiness according to the existing workflow. If manual attestation is allowed, store it explicitly in the receipt; it must not silently convert unmeasured/unassessed checks into machine passes.
- [x] Extend every hardcoded coverage/manual-review key and API/UI contract. A new check must not be accidentally omitted from the approval gate.
- [x] Preserve self-approval restrictions, stale-revision conflicts, workspace isolation and immutable history. A reviewer exception is a recorded human decision, not a waiver of law.
- [x] Receipt identifies profile/pack version, remaining scope limitations and human decisions. State briefly that advertising-risk screening is not a legal certification.

Done: run → legal evidence → reasoned decision → approval → profile/content change → stale receipt → rerun works through real HTTP and UI. All old campaigns and receipts remain accessible.

## T07 — Verification and judge-ready release gate

Run focused tests while implementing; once stable, run the full relevant suites once, then repeat only when changes/failures justify it. Inspect each live/browser script's configuration before invoking it. Never point destructive tests at production.

- [x] Full backend suite and Ruff lint/format; frontend unit tests, lint and production build; whitespace check and OpenAPI parity.
- [x] Real-HTTP core suites plus PDF/visual/Insights/legal tests. Use actual local Tesseract for representative poster cases, not mocks alone.
- [ ] Fresh and existing-database migrations on SQLite and PostgreSQL; restart preserves documents, profiles, historical packs, runs, decisions and receipts.
- [x] Legal evaluation fixtures include positives, negatives, ambiguous cases and unsupported cases, with expected findings AND coverage. Report false positives/misses and fixture count honestly; fixture success is not real-world legal accuracy.
- [ ] Manually exercise desktop and narrow mobile: new session, editable example, PDF evidence/confirmation, poster upload/contrast/alt text, claim-risk evidence, correction/save/rerun, reviewer decision, approval/staleness, Insights evidence links and recovery.
- [x] Verify malformed uploads, oversized input, unavailable provider, OCR uncertainty, API errors/cold starts, concurrent edits, role restrictions and cross-workspace requests. Errors must leave an understandable recovery path.
- [ ] Integrate intended changes against current remote main through a reviewed diff; preserve the existing startup/delete fixes. Use the user's authorized hosting accounts only. The previously connected `adarshnarwankar` Vercel account was explicitly not theirs.
- [ ] Coordinate release with Yogita. Only mark a feature publicly delivered after testing the actual deployed URL in a fresh/private session with no account sign-in. Verify frontend/API compatibility, persistence after restart, reachable evidence and usable cold-start recovery.
- [ ] Confirm the deployed database expiry/availability plan with the hosting owner; the reported expiry was 27 November 2026. Do not change hosting or incur costs silently.

Suggested judge scenario: fictional campaign with a supported PDF guideline, one ordinary text poster that can be measured, one measured visual failure, and one outcome claim requiring evidence. Show exact quotations, measurements and a reasoned human decision. A separate clearly labelled multi-campaign fixture demonstrates Insights with sufficient sample size. Do not pre-resolve all findings or conceal partial coverage to make the demo look perfect.

## T08 — Finish the submission evidence

- [ ] Updated project PDF: three promised improvements mapped to working flows; legal addition labelled with its actual scope; architecture, changes since Round 2, limitations and screenshots.
- [ ] Completed-improvements list and implementation details match deployed behaviour, including deterministic screening versus optional external AI.
- [x] Testing notes contain date, commit, environment, commands/results and manual cases. Distinguish local, branch and public acceptance.
- [ ] Contribution record reflects actual Rushab/Yogita work; no invented percentages or claims.
- [ ] Working project/repository/document links open without sign-in. Team leader handles official submission; this plan does not authorize form completion.

## Execution order and cut line

1. T00, then T01: eliminate the known reliability blocker.
2. T02 and T03: finish acceptance of the remaining promises.
3. T04 before T05/T06: freeze a verified small legal scope, then integrate it end to end.
4. T07 throughout, with a final deployment acceptance window; T08 follows verified results.

Reserve the final 12 hours before the supplied deadline for integration, deployed verification and submission materials. If time tightens, cut additional sectors, model integration and new detectors first. Do not cut provenance, partial-coverage honesty, approval guards or the three promised deliverables. Leave incomplete legal rules disabled and disclosed rather than shipping guessed citations.

Deferred: all-jurisdiction/all-law advice, healthcare/finance-specific regulation, automatic truth verification, legal-compliance scores, scanned guideline OCR, automatic policy weakening, full logo/typography validation and production team identity.

## Sol's completion report

For each task, report: implemented change, relevant files, evidence/tests, remaining limitations and whether it is local or deployed. Update this checklist as work completes. Start by inspecting the current diff and reproducing the contrast failure; preserve existing visual changes. Do not describe the project as winning, legally compliant, fully accessible or fully tested. The deliverable is a reliable, evidence-backed product whose supported workflow a judge can use independently.


## Delivered files and explicit remaining gates

- Local report: `output/pdf/BrandProof_Round_3_Release_Candidate.pdf` (six pages, visually checked).
- Fictional import fixture: `frontend/public/fictional-guidelines.pdf` (seven supported candidate types, linked in UI).
- Evidence: `docs/ROUND3_LOCAL_ACCEPTANCE_2026-10-31.md`, `docs/evidence/round3-backend-tests.xml`, `docs/evidence/round3-restart-digests.json`.
- Legal scope/source maintenance: `docs/ADVERTISING_RISK.md`; coaching-specific pack disabled because final official text was unavailable.
- Release and submission handoffs: `docs/ROUND3_RELEASE_HANDOFF.md`, `docs/ROUND3_SUBMISSION_CONTENT.md`.
- Still open: manual desktop/mobile acceptance and screenshots of the new UI; current-commit PostgreSQL/container CI; reviewed release integration; deployment and fresh public acceptance; actual hosting retention; final member contribution declarations and leader submission. Public release was explicitly deferred by the user. Do not mark those gates complete based on local tests.

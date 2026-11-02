# Round 3 final QA - 2 November 2026

**Outcome:** the three promised improvements are implemented and accepted within their documented scope. Final local backend: **576 passed, 18 optional skips, 0 failures** (594 collected). Frontend: **62 passed, 0 failures/skips**. Nine local HTTP suites, four Python workflow smokes, three local Chromium suites, two public Chromium journeys, public both-file PDF HTTP acceptance and an actual isolated process restart passed. This is not universal correctness, full accessibility certification or representative model/OCR accuracy.

**Release boundary:** production remains `e01f52b6ee02b6c85c480619cfc82cc486a56123`; the frontend error-message patch, additional tests and final documentation are a separate local candidate. No deployment, provider enablement, production migration, destructive cleanup, main merge or official submission was performed. Fresh candidate Docker/PostgreSQL CI and explicit production approval remain release gates.

## State established before changes

- Read AGENTS.md, product plan/contracts, README, Round 3 scope/handoff/local acceptance/submission, 1 November theme/release reports, configured-runtime evidence, workflow, Docker/Vercel/Render configuration and six-step migration history. Original `docs/plan.pdf` was not extracted or modified.
- Primary checkout started on `feat/judge-demo-login-20261101` at `5a5fa39`, with pre-existing edits to `docs/task-status.md`, `docs/configured-backend-tests.md` and untracked user test-kit artifacts. They were preserved.
- Fetched GitHub: main advanced from `1cf0ddc` to **`d251daa`**, including PR #12/#13 and previously merged Round 3 PR #9. `git diff HEAD origin/main` was empty in the primary checkout: these merges contained no missing application files.
- Clean existing isolated checkout `.cache/delete-release` on **integration/round2-backend-pr1** was fast-forwarded from `bf4e938` to fetched main `d251daa`. No reset, force-push or change to local main or `a93f782` was used.
- Provider readback: Vercel production `dpl_C15g8rCKBDCfFtwHfmuasXycyb3P` READY, Render `dep-dbjn8b7f3r2c73cjfti0` live; both source **e01f52b6ee02b6c85c480619cfc82cc486a56123**. Render automatic deployment is off. Later merge/docs SHAs differ, while the pre-hardening application tree matches. Current candidate JS intentionally differs; CSS and both sample PDFs match production bytes.
- No backend product/model/migration changes were made. Added backend files are acceptance tests only. Schema versions remain 0001 through 0006.

## Status matrix

| Promise | Implemented | Local acceptance | Public acceptance | Gap |
| --- | --- | --- | --- | --- |
| PDF import / traceable evidence | VERIFIED | API invalid-input/provenance tests; both shipped PDFs; combined browser | Judge + PDF HTTP + combined browser passed | Supported text layer/directives only; no scan extraction |
| Measured visual/accessibility | VERIFIED within scope | Real OCR/rendered threshold tests, feature smoke, controlled-image browser measurement | Combined browser verifies flat-background/description; supported-poster numeric contrast evidence recorded separately | Workshop antialiasing can abstain; complex images remain partial |
| Governance Insights | VERIFIED | Zero through six reviewed snapshots, exact versions/reasons, truncation/isolation, browser links | Combined browser passed persisted sample warning/history/evidence links | Fictional descriptive evidence; no customer trend claim |

See [requirements matrix](ROUND3_REQUIREMENTS_MATRIX.md) for individual cases and explicit PARTIAL/NOT TESTED classifications.

## Small fixes and regression coverage

1. **PDF errors prescribed image-only remedies.** Shared 413/415 guidance now refers to the action's file limit/type and preserves server detail, including the PDF limit. Added regression coverage.
2. **Uncertain write recovery was unclear.** Network failures and actual transport timeouts advise checking saved state before resubmitting; timeout has a distinct error code. Writes are not replayed; intentional AbortError cancellation stays distinct. Three additional frontend tests cover these changes (59 → 62).
3. **Browser acceptance isolation.** Combined improvements suite now uses a fresh incognito context, disposes it and saves evidence to an explicit directory instead of clearing shared-profile cookies. Dedicated personal browser tabs/profiles were not used.
4. **Cold-start harness mismatch.** Judge initial wait was 45 seconds while product health readiness is documented/bounded at 90. Only initial entry allows 100 seconds; other action deadlines/assertions remain unchanged. No product timeout, measurement threshold or backend validation was relaxed.
5. **Combined measurement gap.** The older three-rule test fixture did not include contrast. The combined suite now imports the actual seven-rule INR 899 PDF and explicitly uploads a supported real Noto 72px black/white image before requiring numeric contrast/target UI evidence. The original Workshop image legitimately yields partial contrast; that limitation is retained.
6. **Acceptance boundaries.** Added three backend acceptance tests: actual image-only/two-supported-page PDFs; zero-to-six reviewed snapshots and whitespace reason rejection; decision-cap truncation. No backend production behavior changed.
7. **Stale documentation/report.** Rewrote README with current hosting, setup, migrations, exact three promises and limits. Replaced historical report-generation content with the current Markdown submission and genuine screenshot source. Report generation no longer rewrites public sample guideline assets.
8. **Description revision race after replacing a poster.** The strengthened browser flow reproduced a stale-revision 409: the old description remained editable while its new-poster read was pending. The editor now derives loading from the last resolved campaign revision, disables edits during that read and blocks stale-revision saves without overwriting dirty text. The real replacement → immediate description edit → save browser path is the regression. The older public build can use **Load saved description (discard draft)** before typing; public evidence explicitly uses that recovery action. The automatic loading fix is candidate-only.

## Environment and commands actually executed

Windows / PowerShell, Python **3.12.15**, Node **24.22.1**, Tesseract **5.5.3.20260724** with eng/osd, real Noto Sans fixture at `.cache/release-fonts/NotoSans-Regular.ttf`. Full pytest and API data use fictional isolated SQLite databases. Local packaged frontend/API served on loopback **8019**; Chrome CDP **9223** uses a dedicated headless profile and fresh contexts. External AI explicitly disabled; bearer/session values remain in memory, never in evidence artifacts or browser storage.

Commands below are relative to the isolated integration root; frontend commands run in `frontend`. Windows uses `npm.cmd`. Set `PYTHONPATH=backend`, add Tesseract to PATH and set the real `BRANDPROOF_TEST_FONT` for image smokes.

| Command | Observed final result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest backend/tests -q --tb=short --junitxml=docs/evidence/round3-final/backend-tests.xml` | **576 passed, 18 skipped**, 137.13s; 114 dependency deprecation warnings |
| `npm.cmd run verify` | **10 commands passed**: build, lint, 62 tests and seven live HTTP suites |
| `node tests/removals-live.mjs` | Passed owner/versions/isolation, retained history, restoration generation/stale Undo |
| `npm.cmd run test:pdf` | Passed compact three-rule and extended seven-rule files, exact quotes, pending/confirmation, conflicting/corrected captions and no automatic approval |
| `.venv/Scripts/python.exe -m ruff check backend scripts` | Passed |
| `.venv/Scripts/python.exe -m ruff format --check backend scripts` | Passed |
| `git diff --check` | Passed; ordinary LF/CRLF notices are not whitespace failures |
| `scripts/smoke.py --base-url http://127.0.0.1:8019 --output .cache/round3-final/review.json` | Passed: four flawed findings, zero exact clean findings, partial coverage and historical staleness |
| `scripts/parser_smoke.py --base-url http://127.0.0.1:8019 --output .cache/round3-final/parser.json` | Passed: **10 readback cases**, oversize revision 422 |
| `scripts/workflow_smoke.py --base-url http://127.0.0.1:8019 --output .cache/round3-final/workflow.json` | Passed real completed OCR, explicit suggestion/decisions, manual-note approval and stale after poster edit |
| `scripts/improvements_smoke.py --base-url http://127.0.0.1:8019` | Passed PDF provenance, real measured background/contrast, description revisions, cited risk, readiness and governance |
| `npm.cmd run test:demo` with local URL | Passed fresh/restored entry, actual OCR findings/boxes, reasoned human decision, PDF, roles, independent judges, reset/revocation/logout, keyboard and 390/320px |
| `npm.cmd run test:improvements` with local URL | Passed actual seven-rule import/confirmation, supported-poster numeric contrast, description, Insights limits/deep links, refresh, mobile, delete Cancel/Confirm/Undo |
| `npm.cmd run test:errors` with local URL | Passed injected 503, actual **10s timeout**, draft preservation, controls restored, one real POST after duplicate activation, wrong/blank/oversize/corrupt PDFs and valid retry; **768px** tablet |
| `.venv/Scripts/python.exe scripts/round3_restart_probe.py` | Passed actual child-process replacement: **10 resources** unchanged, same cookie workspace/credentials and all roles valid |
| `node scripts/public_acceptance_probe.mjs` | Read-only public health, contract and asset digests; evidence preserves initial cold-start results |
| `npm.cmd run test:demo` with authorized public opt-in | Passed complete synthetic public judge journey after recovery |
| `npm.cmd run test:pdf` against Vercel API | Passed both shipped PDFs through actual proxy |
| `npm.cmd run test:improvements` against Vercel | Passed combined PDF/measurement/description/Insights/history/removal workflow in a new fictional workspace |
| `scripts/build_round3_report.py` + PyMuPDF renders | Six-page report; every final page visually inspected after regeneration; no guideline asset mutation |

HTTP suites are script-level pass results, not invented assertion/test counts. Chromium scripts contain multiple assertions and journeys; **3 distinct local suites and 2 distinct public suites** are counted once regardless of reruns. Reviewer choices/approvals/manual notes are labelled scripted QA, not independent feedback or real substantiation.

## Failures/retries retained

- Initial full backend attempt: **571 passed, 18 skipped, 2 recovery CLI subprocess timeouts** in 619.21s. Focused unchanged recovery suite passed **21 tests**; full unchanged baseline passed **573/18** in 135.89s; adding the three acceptance tests yielded final **576/18** in 137.13s. No test timeout/threshold was increased and no failing backend behavior was patched.
- Initial local HTTP approval request encountered a connection timeout while the first full suite was running. Approval rerun passed; later `npm run verify` passed all seven HTTP suites together. The small poster HTTP fixture truthfully reports partial low-confidence OCR; Workshop and controlled-image tests separately demonstrate completed OCR.
- Local runtime reached normal **20-session** admission limit after accumulated QA. Restarted only the isolated API, retaining its SQLite database and unchanged normal 20/300 limits, then remaining/full HTTP smokes passed. No production quota or database was reset.
- First public judge attempt stopped at 45s during a proxy 502/cold start. Read-only direct Render health returned 200 after **22,397ms**; deployed contract equals saved contract. Corrected harness initial wait as above; warmed public judge, PDF and combined journeys passed. The initial failure screenshot/read-only result remains evidence. Vercel `/openapi.json` is 404 because only `/api/*` is proxied; direct Render `/openapi.json` is the contract endpoint.
- Strengthening the browser measurement assertion initially exposed **partial contrast with 19 unmeasured Workshop words**. This is legitimate abstention, not a product failure. Use a real controlled supported fixture for the numeric-measurement assertion; preserve partial coverage for the original sample.
- The new replacement journey reproduced the description race above. Candidate browser acceptance passes without manual reload. Public strengthened measurement acceptance opts into `BRANDPROOF_MANUAL_DESCRIPTION_RELOAD=1`, exercising the existing recovery action; it is not evidence the candidate fix is deployed. Accumulated local operation quota required another isolated-process restart with its database preserved; quotas were unchanged.
- PowerShell npm.ps1 was blocked by normal execution policy; used `npm.cmd`. Offline clean npm install lacked a cached Vite tarball; ordinary locked network install succeeded. An ignored-parent lint scan found no files in the isolated copy; initializing that copy's own Git root made the normal lint command pass. No security policy was changed.

## Clean setup and reproducibility

Copied only tracked/current candidate source into `.cache/round3-clean`, without ignored environments, data, `.env` credentials or node_modules; copied `.env.example` to that copy's `.env`. `uv sync --locked --extra dev --offline` created a fresh **Python 3.14.10** environment with 40 locked packages from cache. `npm ci --no-audit --no-fund` installed 27 locked packages. Normal lint, **62 tests** and production build passed there; asset names match the candidate. Read-only migration check reported six pending, **applied=false/destructive=false** on the empty database. The actual process-restart probe also passed in that clean environment. Tesseract eng/osd verified. This tests an isolated clean source copy, not a second network Git clone or a Linux installation.

No local Docker/psql executable is installed. The deployed source's successful GitHub workflows were freshly read from GitHub: **41332634711, 41330615411, 41330615524**, all success at **e01f52b**. Those workflows exercise Docker/PostgreSQL 16 fresh/legacy upgrades, real workflows and regressions. They are **historical deployed-source CI, not a fresh run of this final patch**. No test is counted as passed merely because its script exists. No destructive migration/probe targeted production.

## Evidence and deliverables

`docs/evidence/round3-final/` contains final pytest XML, local/public judge screenshots and sanitized browser summaries, combined PDF/measurement/governance screenshots, local network-fault results, public both-file PDF results, deployed-source CI readback and read-only live digests. `restart.json` records booleans/resource count only. Raw credentials, cookie jars and workspace identifiers are not serialized. Local logs/runtime DBs remain ignored under `.cache`.

- [Requirements matrix](ROUND3_REQUIREMENTS_MATRIX.md)
- [Judge walkthrough](JUDGE_FINAL_WALKTHROUGH.md)
- [Known limitations](ROUND3_KNOWN_LIMITATIONS.md)
- [Current submission source](ROUND3_SUBMISSION_CONTENT.md)
- Final document: **output/pdf/BrandProof_Round_3_Final_Submission.pdf** (six pages). Historical release-candidate/plan PDFs are preserved.
- README now covers requirements, Windows/Linux setup, Tesseract, env template, backend/frontend, migration/database, Docker (no Compose claim), tests, judge flow, production architecture, troubleshooting and privacy.

## Release blockers and next action

1. Run the existing container/PostgreSQL/legacy-upgrade CI on the exact candidate commit; this host cannot execute it. Do not substitute the successful e01f52b run.
2. Review the final patch and explicit partial limits, then obtain explicit production approval for that exact commit if a release is wanted. The current public baseline already delivers the three promises; this patch does not require a schema migration.
3. Confirm current hosting retention and a recovery/backup plan before relying on continued availability. No full backup is verified; no new production migration is requested.
4. Team leader reviews actual contribution declarations and submits the official form/PDF. No form submission has been performed.

Final candidate/application provenance is pinned in the accompanying manifest/commit record. Production is still e01f52b; the final local commit and live commit **do not match**.

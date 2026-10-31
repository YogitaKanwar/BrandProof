# Round 3 local release handoff

## 31 October integration update

The latest upstream feature and main heads are now included in pushed integration commit `9d6d227a530ee1aa7fd752579460cab48fdd687b`. Application source matches upstream main `1cf0ddc`; integration retains its extra removal HTTP suite and fixes the container regression-test layout. The primary checkout's uncommitted documentation and local main are preserved.

The earlier backup hold was explicitly superseded: the user authorized deployment without a verified database backup and accepted that recovery is not guaranteed. Production is now live at `7cb8fb3169b0dcd1f171a2765232089cbd4e2578` on the existing Render/Vercel services, with the selected committed navy/Desert Sun design. The six ordered additive startup steps completed without an observed schema error; no data deletion/reset/destructive migration occurred. See the production release entry in `configured-backend-tests.md` for exact evidence and limits.

Fresh local evidence: 558 backend tests passed with 18 optional font skips; 56 frontend tests, lint/build, Ruff, eight HTTP suites, expanded feature smoke, live/saved OpenAPI parity, packaged legal/migration JSON and local migration preflight passed. The intended Noto font passed real OCR/contrast; Arial conservatively abstained. No application behavior was modified to force a measurement. Final integration CI: [run 41213208584](https://github.com/YogitaKanwar/BrandProof/actions/runs/41213208584); **both jobs passed**, including Docker/PostgreSQL upgrade and actual workflows, 558 backend tests (18 optional font skips), and 56 frontend tests/lint/build. Full evidence is recorded in `configured-backend-tests.md`.

The former preview has now been superseded by READY production `dpl_Gc7pQV4JdNBpLGdscYM3Dy9mB2Bu` with the actual public alias, alongside live Render `dep-dbj0dklg1s2s73eeh3vg`. Public asset bytes/contract, seven API suites, expanded feature smoke, staged browser acceptance and actual pre/post-upgrade retention passed. External AI stays unavailable; verified backup and broad quality acceptance remain incomplete. The historical local-only account uncertainty below has been resolved for the existing team-owned resources; its local test limitations remain historical evidence.

31 October 2026. User explicitly requested a local release after the discovered Render workspace could not be identified as theirs. Do not deploy into that workspace or the previously rejected Vercel account `adarshnarwankar`. No push, merge, deployment or submission was performed.

## Candidate

- Repository: https://github.com/YogitaKanwar/BrandProof
- Inspected feature branch: `feat/brandproof-improvements-20261028`
- Base commit: `ca6dd8c20c0338656b523a1689693bded6413d7a` plus the local working changes. This is not a committed release SHA.
- Latest fetched `origin/main`: `43fc4a5`, the startup-fix merge. A fetch completed without new remote changes. Review integration against main before release; do not blindly merge the working directory or overwrite Yogita's work.
- Current local app: http://127.0.0.1:8001/ (local-only, not a submission URL).
- Repository homepage: https://brand-proof-tau.vercel.app
- Local report: `output/pdf/BrandProof_Round_3_Release_Candidate.pdf`
- Implementation/testing: `ADVERTISING_RISK.md`, `ROUND3_LOCAL_ACCEPTANCE_2026-10-31.md`, `tasks.md`.

## Completed locally

1. PDF directive import: bounded extraction, exact page quotations/digests, pending candidates and explicit confirmation, source-version history and unsupported-page reporting. The import panel offers a fictional sample PDF with seven supported rule types.
2. Measured flat-background colour, contrast and description requirements: ordinary antialiasing repaired, measurement colours/target shown, partial coverage retained, description changes stale receipts.
3. Governance Insights: category/campaign counts, exact source-version groups, latest decisions/reasons, explicit rerun denominator, reviewed-snapshot sample count, truncation/insufficient-sample notices, evidence links and regulation-aware grouping.
4. Additional advertising-risk profile: curated India reference, same-finding regulatory evidence, immutable pack/profile snapshot and approval staleness, dedicated incomplete-coverage notes and historical receipts.

## Before deploying from the team-owned accounts

- Review the tracked/untracked diff, preserve prior design edits, inspect repository instructions and agree the exact feature commit. Keep unrelated changes out of the release commit. Do not publish temporary test databases or sessions.
- Run the checks documented in the dated acceptance report. Confirm the wheel contains `legal_pack.json`; it is read at application import.
- Run the existing container/PostgreSQL CI on the final reviewed commit. This local machine could not access Docker, and PostgreSQL binaries were unavailable. `.github/workflows/hosting-check.yml` already exercises fresh PostgreSQL, a legacy upgrade, real OCR/approval and improvements smoke. The migration probe now expects `legal_profile_versions`.
- Back up the actual database and follow migration preflight. Keep a compatible executable available: schema version 0006 is additive, but old executables reject unknown versions. Do not promise that selecting an old deployment automatically reverses the database change.
- Build and release the frontend and API together. The API's required manual-check vocabulary now includes `advertising_risk`; an old frontend can fail approval with the new API. The new frontend makes additional profile requests that older backends lack.
- Verify server keys remain server-side; external contextual AI stays disabled unless intentionally configured and consented. Use the authorised Render/Vercel projects only.
- Confirm database expiry, backup and availability in the actual hosting dashboard. The previously supplied expiry was 27 November 2026; GitHub does not establish its current value. No paid plan is selected by this handoff.

## Public acceptance still required

Open the deployed link in a fresh private window without signing in. Verify current API health, new session, editable fictional example, profile selection, sample PDF import/quote/confirmation, poster measurement/description, cited claim finding, reasoned decision, approval, staleness after edit/profile change, Insights deep links and session/persistence recovery. Exercise desktop and narrow mobile, failed API recovery and cold starts. Record actual results and deployed SHAs. Do not substitute local tests or a screenshot of the homepage for this path.

The public homepage returned 200 during read-only inspection; `/api/v1/health` returned 429. No deployment history was exposed by GitHub's deployments endpoint. This establishes neither deployment identity nor a healthy backend. Investigate through the team-owned hosting account when authorised; do not spam retries or bypass protections.

The browser tool rejected local-tab access under its security policy. No alternate browser automation path was used. Manual UI acceptance and fresh screenshots of the new legal controls remain unverified. Older UI screenshots are not evidence of this feature.

## Submission materials

The six-page PDF is a local release candidate with the actual scope and gaps disclosed. After public acceptance, update its release status and evidence rather than submitting claims that are no longer current. Its reproducible source is `scripts/build_round3_report.py` (ReportLab and Noto font dependency; use the bundled document runtime, not system Python). The same script generates `frontend/public/fictional-guidelines.pdf`.

Use the completed-features and implementation descriptions in `ROUND3_SUBMISSION_CONTENT.md`. Member-role mapping comes from team instructions, not inferred time percentages; confirm final wording against the team record. The team leader submits the official form. The supplied cutoff is 3 November 2026, 23:59 IST. The event page and final instructions govern submission; no form was filled here.

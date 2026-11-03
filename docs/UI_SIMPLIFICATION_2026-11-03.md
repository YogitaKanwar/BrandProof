# Focused UI simplification - 3 November 2026

**Complete locally; deployment preflight BLOCKED.** Review at http://127.0.0.1:8021/#/demo while the local test server is running. The existing working Render fallback and public production deployment were not changed. Pre-existing documentation/submission/test-kit edits were preserved.

## Changes

- Landing: removed the Demo Credentials card, Creator/Reviewer labels, Copy actions and repeated identity/privacy explanations. Kept branding, the product description, Try Interactive Demo/Continue Demo, actual loading/error/retry messages and existing sample-entry behavior. Open local drafts now sits inside the collapsed Session & recovery disclosure.
- Header: removed the full-width DEMO MODE banner. The existing top-right menu reads Demo workspace and contains Reset Demo, Exit Demo, reload/local-draft recovery and one concise fictional-data/synthetic-role disclosure. Reset confirmation, expiration recovery and their existing actions remain. Opening the menu no longer changes header height.
- Overview: kept Overview/New review/Governance Insights navigation, the amber New Review primary action and Try an editable example. Removed the repeated introductory workflow strip, duplicate blank-campaign action and repeated example copy. The review workspace's actual stages, role controls and human-decision flow remain.
- Retained the navy `#1e2640`, cream `#f8f5ef` and amber `#dc9750` identity. Native disclosure controls and focus indicators remain; tested narrow menus stay inside the viewport. No full accessibility audit is claimed.

## Exact changed source/test files

| File | Change |
| --- | --- |
| `frontend/src/DemoEntry.tsx` | Landing copy/card removal and local-draft recovery disclosure |
| `frontend/src/DemoEntry.css` | Recovery disclosure styling; removed obsolete credential/banner styles |
| `frontend/src/ReviewWorkspace.tsx` | Session actions in status menu; Overview simplification |
| `frontend/src/App.css` | Menu spacing/buttons and stable header height |
| `frontend/tests/judge-demo-browser.mjs` | Browser assertions for removed UI, relocated controls, draft recovery, responsive menu and one primary Overview action; preserved session/permission/human-review assertions |
| `frontend/tests/new-review-browser.mjs` | Two status-label expectations updated to Demo workspace; this legacy suite was not run in this slice |

Documentation changes for this slice: this file and an appended `docs/task-status.md` entry. New sanitized evidence/screenshots are under `docs/evidence/ui-simplification-20261103/`. No backend, API-client, authentication/session implementation, permission, schema, dependency, API-contract or deployment-configuration file changed.

## Verification

- **62 frontend tests passed**, zero failed/skipped.
- **Lint passed.** TypeScript/Vite **production build passed**.
- **Local genuine Chromium judge suite passed** on the final built frontend: Try/Continue Demo, no credential card/banner, recovery-menu local drafts, one primary Overview action, menu visibility/unchanged header height, same-workspace refresh, actual custom/sample campaigns, completed Tesseract OCR/findings, PDF pending import, reasoned human request-changes, 401/404/403 isolation/role guards, Reset cancellation/confirmation/revocation, stale-tab recovery and Exit/logout.
- **Local Chromium error smoke passed**: injected 503, actual ten-second transport timeout, preserved drafts/re-enabled controls, one real campaign create after duplicate activation, invalid PDF recovery and valid retry.
- Desktop 1440px, tablet 768px and 390/320px widths exercised; landing and open menu had no horizontal overflow. Desktop/menu/mobile screenshots visually inspected.
- `git diff --check` passed. Backend/API-contract/API-client diffs are empty.

The two browser suites ran against the unchanged backend with a separate local fictional SQLite database, AI disabled, on loopback port 8021. Scripted QA decisions are not independent human approvals. Tokens/cookies stayed in memory. These are local candidate results, not new public/fallback acceptance.

## Screenshots and evidence

- Landing: `evidence/ui-simplification-20261103/login-desktop.png`
- Overview: `evidence/ui-simplification-20261103/workspace-overview.png`
- Open workspace menu: `evidence/ui-simplification-20261103/workspace-menu.png`
- Mobile landing/menu: `login-mobile.png`, `workspace-menu-mobile.png` in the same directory
- Judge results and other workflow screenshots: `browser-results.json`, `direct-demo-entry.png`, `workshop-references-content.png`, `workshop-poster-ocr.png`, `real-contradiction-results.png`, `poster-price-evidence.png`, `human-review-changes-requested.png`, `fictional-guidelines.png`, `extended-guidelines.png`
- Error smoke: `errors/results.json`, `errors/timeout-recovery-tablet.png`, `errors/invalid-pdf-recovery.png`

At the end of local implementation, no push, merge, deployment, production-data access, security change or migration command had been performed. The user subsequently approved the specific existing Render judge-preview release; the deployment preflight below supersedes the earlier local-only publication status.

## Approved judge-preview release: blocked preflight

The user explicitly approved committing/pushing these UI changes and deploying only to `brandproof-round3-preview-20261102`, while preserving the existing backend/database, running no migrations and leaving original production services untouched. The user also directed the agent to stop if that existing service could not safely receive a frontend-only update.

Fresh provider readback confirms the judge service `srv-dbkati8ae00c738bl1h0` uses repo `YogitaKanwar/BrandProof`, branch `integration/round2-backend-pr1`, Docker runtime, repository-root Docker context and `./Dockerfile`; no custom Docker command. Automatic deployment is off. The existing deployment remains `dep-dbkatioae00c738bl2p0`, LIVE at `5eac37660a7c4f53d17464dea3ced563486aa9bd`. Read-only metadata also confirms original production Render automatic deployment is off; no production change was made.

The approved frontend source/test files contain no backend, contract, schema, dependency or Docker delta. However, this service has no separate frontend deployment unit: `Dockerfile` builds React and copies its `dist` into the same image as FastAPI. Updating the bundled UI replaces the complete application container.

Its recorded database configuration is SQLite at `/app/data/round3-preview.db` on the Free service's ephemeral filesystem; a fresh environment-variable read is unavailable through this connector. [Render documents that redeploys discard local SQLite/filesystem changes and that Free services cannot attach persistent disks](https://render.com/docs/free#local-files-lost-on-redeploy). Database retention therefore cannot be guaranteed under this release. Additionally, the unchanged `backend/brandproof/main.py` lifespan unconditionally calls `migrate(engine)` on every backend startup. No supported frontend-only rollout preserving this process/data and bypassing that startup routine was verified.

**Decision: do not trigger a Render deployment or modify hosting/storage/security configuration.** Preserve the old working judge image. Commit/push the approved frontend and its review evidence only; preserve unrelated local work. The source commit is a release candidate, not the deployed SHA. Post-deployment public acceptance is not run because no deployment is attempted. Existing fallback public acceptance remains the separate, dated record; the local UI tests above are not a new live pass.

Proceeding at this same URL would require a separately reviewed storage/retention and full-container-release arrangement consistent with the user's no-reset/no-migration constraints. No such change or paid resource is authorized or performed by this UI release approval.

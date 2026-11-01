# Judge demo implementation and audit — 1 November 2026

Implemented on `feat/judge-demo-login-20261101`. Testable local preview: **http://127.0.0.1:8017/**. This is a local URL, not a public deployment. No production migration, deployment, main merge, reset, force-push or provider call was performed.

## Repository and authentication audit

- Verified remote: `https://github.com/YogitaKanwar/BrandProof.git`, matching the requested repository. Starting checkout was the improvements feature branch at `ca6dd8c`, with pre-existing changes in two QA/status documents and an untracked deployment assessment.
- Read the plan, current frontend handoff, saved API contract, SQLAlchemy models, permissions, routes, navigation, deployment files and tests. The remote audit found newer feature commit `b8acc3cdf288c948f8bc207a2c8c628991d02c0f`. Fast-forwarded only the dedicated new branch to that commit, preserving its advertising-risk, measured visual, PDF and governance work. Conflicting UI edits were combined. A retained safety stash contains all earlier working changes. Existing main and the `a93f782` / `cdda60f` checkpoints remain intact.
- The authentication model contains `Workspace`, synthetic `Actor` roles and `DemoBrowserSession`; it has no email/password account directory, sign-in endpoint, identity verification, SSO or password reset. Existing Creator/Reviewer/Owner labels are **synthetic sandbox roles**, not genuine verified human accounts. No production account was created, migrated or replaced.
- Each session creates a random workspace and three separate synthetic actors. High-entropy recovery secrets and role bearers are hashed server-side; browser role bearers stay in memory. Recovery uses a 24-hour HttpOnly, SameSite=Strict cookie, Secure by default. No password database is needed for passwordless guest access. Public copy buttons copy role access instructions, never credentials or tokens.
- A browser profile shares its recovery cookie across tabs; separate judges use separate browser sessions/profiles, and Exit/Reset revokes the previous guest. The backend already enforces workspace scope, role permissions, revisions, author restrictions, source versions and historical receipts. Creator edits/requests; Reviewer reads/decides; sandbox Owner configures references. This guest can exercise all three synthetic roles; switching them is not independent human sign-off. There is no administrative role or access to another workspace.
- Confirmed defects: no server-side logout/revocation, no session-creation admission limit, no dedicated judge entry, and an old INR 499 sample. The task's explicit authorization for secure backend demo/user handling covers these targeted fixes. Existing review/OCR/AI decision logic was preserved.

## Delivered behavior

1. Responsive Emerald entry screen, prominent **Try Interactive Demo**, **Explore Sample Review**, visible **Demo Credentials**, copy feedback, keyboard access, recovery/loading/errors, and access to existing local drafts. No fake account-login form is shown.
2. Server-issued Demo Creator and Demo Reviewer identities, plus the existing workspace-scoped synthetic Owner for references. One-click access starts a fresh isolated workspace. Refresh resumes valid work; failed recovery never silently creates a workspace.
3. **Demo Mode**, explicit reset confirmation, **Exit Demo**, expiry/revocation notices and restore action. Logout revokes every role plus recovery credentials server-side. Reset revokes the old workspace and creates a separate empty one atomically. Saved history is retained until an operator applies retention cleanup.
4. Fictional **Workshop Campaign**: real typed INR 899 reference created pending v1 and confirmed by its synthetic Owner as v2; INR 599 caption; generated INR 599 PNG uploaded through real OCR; additional versioned date/wording/disclosure references and one pending policy. Findings and approvals are never seeded. Judges explicitly run review and perform human decisions.
5. Four workspace stages: References → Content → Results → Human Review. Existing editing, uploads, explicit corrections, comments, revisions, source history, legal scope, measured checks, Insights and stale/self-approval safeguards remain.
6. A small fictional workshop PDF can be inspected, selected and imported through the existing bounded parser. Its three extracted rules remain pending with exact page quotations; confirmation is explicit. The existing full sample PDF remains downloadable. PDF input rejects empty/oversized/non-PDF selections; server validation remains authoritative.
7. No-store on private API/session responses; acknowledged logout before clearing browser memory; no write replay on failures; existing file validation and permission/error recovery retained.

The poster originally returned a truthful scope clarification because the footer included “before”. The fixture now uses explicit supported sentences. No parser, confidence threshold or finding was changed to force a result. Genuine OCR and the existing engine produce the price contradiction, with real boxes and approved-source v2 evidence.

## Admission, costs and cleanup

- Default per server-recognized peer: **20 session creations/resets/hour**, **300 campaign mutations/hour**, plus ten-times global caps. Admission precedes backend work, includes OCR/PDF/review requests and ignores caller-supplied forwarded headers. Buckets are bounded to 4,096 and peer keys are salted hashes held only in process memory. Recovery/logout remain available when quotas are exhausted. HTTP 429 carries Retry-After.
- This is deliberately the existing **single-worker** architecture, with no new infrastructure or database tables. Restart resets these local admission counters. Multiple workers/replicas or stronger abuse resistance require shared gateway admission before public release; NAT/proxy peers can share a quota. Configure trusted proxy handling explicitly rather than trusting arbitrary X-Forwarded-For. The current production ingress behavior is not accepted by local tests.
- Expensive external AI retains its existing persistent workspace/global hourly and concurrency quotas, server enablement and explicit per-review consent. Local preview forces the provider off. It reports **unavailable**, never a fabricated AI success. OCR completion does not establish complete poster review.
- Operator command: `python -m brandproof.demo_cleanup --retention-days 7` is a **dry run** and prints only aggregate counts. It targets only explicitly marked synthetic browser workspaces whose session and all actors expired more than seven days ago. Active and unmarked workspaces are excluded.
- Permanent cleanup additionally requires `--apply --isolated-demo-database`. Back up and verify the database privately first. The command removes dependent data in foreign-key order in one transaction; it is not a guest API and is not scheduled automatically. Tested only against disposable SQLite here. Do not run it against production without separate authorization. Normal reset/logout never erase audit history. Retention scheduling and PostgreSQL execution remain operator acceptance items.

## Verification

| Check | Result |
| --- | --- |
| Full backend suite, including upstream features and 13 new demo tests | **569 passed, 18 skipped**, 136.13 s; skips require optional Noto families unavailable on this Windows host |
| Final targeted session/security/approval/hosting suite after response-schema change | **101 passed** |
| Frontend unit tests | **59 passed** |
| Frontend build and lint; backend/scripts Ruff and formatting | Passed |
| Seven existing real HTTP suites | Passed: session/campaign, sources, reviews, posters, collaboration, approval, consent |
| New genuine Chromium acceptance | Passed: entry, keyboard/mobile, required fields, own campaign, refresh, real sample findings, human decision, PDF, two isolated browser contexts, 401/403/404, reset/cancel/revocation, revoked-tab recovery, logout/reload and direct sample entry |
| Sample OCR | Completed; real INR 599 boxes and source-v2 INR 899 contradiction; overall review remains partial |
| Existing expanded Chromium regression | Passed: explicit drafts, PDF confirmation, descriptions/measured checks, Insights/history links, mobile/refresh and deletion/Undo |
| Running helper preview contract | Matches saved OpenAPI, including new response schemas |
| External AI | Disabled; real unavailable coverage shown; no external call |
| PDF visual QA | Inspected actual Chromium PDF rendering and extracted text; no invented extraction/confirmation |

The real HTTP poster-limit fixture truthfully produced partial/low-confidence OCR; the larger workshop sample separately produced completed extraction. Neither establishes representative OCR accuracy. Wrong bearer credentials and forged recovery cookies are rejected. Wrong-password testing is inapplicable because account/password login is not implemented.

Screenshots and sanitized browser results are in [`evidence/judge-demo/`](evidence/judge-demo/). They show the desktop/mobile entry, confirmed references, actual poster, caption contradiction, poster evidence boxes, human request-changes receipt and rendered PDF. Notes/decisions in these automated tests are explicitly fictional test actions, not claims of independent human review. Screenshots contain no session tokens or workspace credentials.

## Reproduce the isolated preview

Use the repository's installed locked Python environment and frontend dependencies. On this host:

```powershell
.venv-check/Scripts/python.exe scripts/judge_demo_preview.py --port 8017
```

The helper builds the UI, binds loopback only, creates `.cache/judge-demo-preview.db`, disables external AI, uses the normal demo quotas and adds the existing Windows Tesseract directory when present. It never reads or writes production data. Missing OCR remains unavailable rather than a clean pass. Stop the server with Ctrl+C. The earlier acceptance database `.cache/judge-demo-20261101.db` is separate and ignored.

Run `npm.cmd --prefix frontend run test:demo` against the isolated server with the existing dedicated Chromium CDP profile on port 9223. The test refuses public URLs. It creates only fictional sessions and stores only screenshots/sanitized evidence. The 7-suite stress acceptance used a local session-creation limit of 100 to allow repeated test runs. Repeated extended browser runs eventually hit the 300-operation limit and truthfully returned 429; after restarting the isolated preview, both new and existing browser suites passed with the normal 20-session / 300-operation defaults. The preview helper was started and its live OpenAPI matched the saved contract.

## Deployment audit and incomplete work

- Vercel connector verified project `brand-proof`, ID `prj_GEGiIsaOoEp0mww0FY5LIkOZKyf6`, Vite, Node 24, supplied public alias, and a READY latest preview. Listing deployments with its returned team ID was denied 403. No installed Vercel CLI was available for the prescribed fallback. That existing preview is not this task's build.
- Repository configuration: frontend Vercel rewrite forwards `/api/*` to `https://brandproof-api-slz9.onrender.com/api/*`; Render blueprint uses the existing Docker service with automatic deployment off and external AI disabled. Docker/serve use one worker. Current Render account/deployment/database settings could not be inspected because its connector requires an explicitly selected workspace. Do not assume historical database expiry or deployment SHA is current.
- Read-only public verification: frontend HTTPS **200** with assets `index-DxK5a0Ox.js` / `index-Dj64Y8K8.css`; proxied `/api/v1/health` **502** twice. Direct Render health returned **200/database OK** and its direct OpenAPI contains guideline-document import but **no new logout route**. Frontend `/openapi.json` returned 404 because the existing rewrite proxies only `/api/*`. Production API proxy reliability and exact deployed commit remain unaccepted.
- **No cloud preview created:** no selected Render workspace/isolated cloud backend was available, Vercel deployment inventory was permission-denied, and the default frontend preview rewrite would share the production API. Do not publish that configuration as an isolated preview. The local preview is functional and isolated.
- **No real account/password sign-in:** intentionally not introduced into the synthetic guest model. Production team identity/authentication remains future scope. Public demo “roles” must continue to be labelled synthetic.
- **No new database migration for this demo change.** The incorporated upstream feature baseline already defines migrations through `0006_advertising_profile`; startup can apply them. An eventual public backend rollout must compare its actual schema, back up, and obtain explicit authorization for any pending production migrations. None were run against production here. Application rollback alone would remove new logout/reset routes and weaken revocation behavior; retain the patched backend while rolling back UI, and never restore an old database backup without revoking restored demo credentials before reopening access.
- Public release still needs: repair/verify the existing API proxy, an authorized isolated cloud backend/database/preview target, same-origin HTTPS cookie/CSRF checks at that ingress, PostgreSQL/cleanup acceptance and a retention schedule. Optional Noto cases, live provider quality and representative OCR/visual usability remain outside this run.

## Files changed by this task

- Backend: `config.py`, `demo_sessions.py`, new `demo_limits.py`, new `demo_cleanup.py`, `main.py`, `routes.py`, `schemas.py`; new `tests/test_judge_demo.py`.
- Frontend: `package.json`, `App.css`, `ReviewWorkspace.tsx`, `ContentWorkspace.tsx`, `DocumentImport.tsx`, new `DemoEntry.tsx` / `DemoEntry.css`, `exampleCampaign.ts`, `api/backend.ts`, `api/client.ts`, `api/readiness.ts`; new lifecycle/browser tests, adapted improvements browser entry/empty-state/PDF selectors; new `public/demo/workshop-guidelines.pdf`.
- Tools: `scripts/judge_demo_preview.py`, `scripts/generate_demo_guidelines.py`.
- Documentation: this report, frontend handoff, OpenAPI, task-status and configured-runtime acceptance additions; screenshot PNGs and sanitized browser results.

Pre-existing edits to the two status/QA documents and the untracked October deployment assessment are preserved separately. They are not relabelled as new task work. The exact final commit and tracked file list are available with `git log -1` and `git show --stat HEAD`.

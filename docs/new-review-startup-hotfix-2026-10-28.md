# New Review 502 incident and production acceptance

## Diagnosis and change

The public API initially returned a Vercel 502. Render logs showed a normal Free-service idle shutdown, followed by a successful startup; direct health recovered after about 24 seconds. Subsequent public campaign creation/list/get succeeded. There was no evidence of a database failure or application crash.

The isolated production hotfix adds credential-free same-origin health GET polling before demo creation, session resume and campaign creation, with a 90-second bound, database-health validation, visible startup progress, concurrent-check sharing and a 15-second readiness cache. POST creation requests are never retried. Failed resume never creates a replacement workspace. Form values remain intact on failure; ambiguous gateway failures advise reloading saved reviews before resubmission.

## Public release

- Judge URL: https://brand-proof-tau.vercel.app/
- Frontend source: `298c7769f40ea268032c1c49d6a3c4d3c977220b`, integration branch, Vercel production deployment `dpl_D4mDdc8wWptzih3vaBhWcDRPVyKJ`, READY and public alias assigned.
- Public bundle: `index-CpehTTKe.js`, independently checked in the public HTML (200).
- Backend remains `36cb8ae95adf42a252808e08f8dcdf972627c360` on the existing Render service. No backend, database, environment or hosting changes; no main merge; no Round 3 features deployed.

## Validation

- Hotfix frontend: 52 unit tests passed; lint and production build passed. Feature-branch carry-forward: 54 unit tests passed, lint and build passed.
- Backend health and hosted-app regression: 17 tests passed against the unchanged production-source backend.
- Real public HTTP: session creation, campaign creation/persistence/list/get/revisions, 401/403/404/422 guards and workspace isolation passed. Tokens stayed in memory and were not printed.
- Public New Review: actual UI created exactly one session and one campaign, opened Sources, and restored the same review after refresh. No uncaught browser exceptions or token keys in local storage.
- Cold-start regression: the disposable browser simulated two failed health GETs, observed startup progress, then completed the real public API flow. The built hotfix passed before deployment; the actual deployed bundle passed again without artifact substitution. This is a simulated transient failure test, not a controlled Render sleep-duration measurement.
- Post-deploy connected browser regression: 23 groups passed, including sources/confirmation/history, caption save/conflict handling, findings/history, human decisions/approval receipts, upload failure handling, review-request failure handling, same-session restoration, exact fresh `/#/new` flow, outage/retry behavior, responsive layouts and no uncaught exceptions. Optional OCR/logo-specific flags were not enabled for this incident run.
- Public health after deployment: HTTP 200, status ok, database ok.

The local preview initially hit the production origin guard, as expected; acceptance used the allowed public origin in a dedicated disposable browser. Existing uncommitted documentation edits and the untracked synchronization assessment were preserved.

## Limits

Render Free can still sleep. The frontend waits visibly for up to 90 seconds, then offers a truthful failure without submitting creation. This does not guarantee always-on hosting or eliminate later network interruptions. OCR/provider/logo limitations and the November 27 Free PostgreSQL retention deadline remain as previously recorded. The Round 3 feature branch still requires its separate review, migration and deployment gates.

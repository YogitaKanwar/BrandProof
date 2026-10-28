# Implement guided reviews, document evidence, measured poster checks and governance insights

Base: `integration/round2-backend-pr1`
Head: `feat/brandproof-improvements-20261028`
Status: prepared for review; do not merge/deploy until PostgreSQL/container CI and the migration release gate are accepted.

Creators can now try a fictional campaign with a real sample poster, follow server-derived approval prerequisites, import PDF guidelines as pending page-cited sources, save poster-specific descriptions and explicitly copy unverified rewrite candidates into drafts. Contextual AI can assess caption and high-confidence poster OCR as separate assets. Governance Insights links repeated finding signals and reviewer reasons to the exact saved run/source version.

This preserves explicit owner confirmation, per-review external-AI consent, current revision checks, private historical images, human decision/notes requirements and session recovery. Measured background colour and text contrast have narrow supported scopes and abstain on uncertain imagery. No font recognition, truth/accuracy score, automatic content approval or production identity is claimed.

Database changes are additive, versioned and checked against the deployed legacy schema. Leased inference uses heartbeats, periodic recovery and fenced completion; a late worker cannot overwrite a recovered result. No destructive migration or production database update was performed. An unused legacy workspace component was removed; active local-draft behavior remains.

Validation:

- Backend 514 tests passed; frontend 50 tests passed; Ruff lint/format, frontend lint/build, dependency check and running/saved OpenAPI parity passed.
- Follow-up: 516 backend / 51 frontend tests now pass with connected Recent Reviews Delete/Cancel/Confirm and exact-generation Undo. Removal retains history, excludes normal access and denies running/stale/unauthorized attempts. Additive migration `0005_review_removal`; deletion browser/reload and all 26 existing browser groups passed. This feature is not live in production.
- Seven genuine HTTP suites and all 26 existing browser groups passed, including actual Tesseract and logo-reference flow.
- New real HTTP and browser acceptance passed PDF pending provenance/confirmation, OCR claim boxes, draft acceptance, description revision/staleness, measured background, readiness, governance/sample guards, exact historical links and responsive/reload behavior.
- Backend wheel built; independently imported/started from its installed wheel with packaged migrations. Frozen lock is accepted by the Docker-pinned uv 0.12.21.
- Added feature-branch/PR CI for the production Docker image, PostgreSQL legacy upgrade/idempotence and new HTTP smoke, backend regression and frontend checks. Fresh CI completion is a release gate, not inferred from local SQLite tests.

Production remains on `36cb8ae` at the existing Vercel + Render URLs. A read-only-configuration resource probe used only fictional records: 5,155,064-byte PNG upload returned 200 in 10.32s; logo review returned partial/not-assessed with a time-limit reason; initial cold health 502 was followed by 200 after warming. These are single observations, not latency percentiles or a controlled sleep test. Provider remains unavailable; quotas were not raised. Render Free PostgreSQL expires 27 November 2026.

Before production release:

1. Review this branch and pass the new Docker/PostgreSQL CI. Confirm hosted backup/export access and restore procedure; do not treat `create_all` or a local SQLite copy as a PostgreSQL backup.
2. Stop admission and all old workers, take the approved production backup, run `python -m brandproof.migrations --check` in the intended environment, then `--apply` only after release approval. Existing schema drift must stop the release. Do not delete data/tables to force a migration through.
3. Deploy the reviewed integration commit using the existing manual Render/Vercel workflow; do not change hosting/providers or publish main. Repeat public HTTP/browser/new-feature and redeploy/session/image persistence acceptance.
4. If live AI is wanted, privately configure the existing Render provider/model/key/enablement and account-appropriate quotas, then perform explicitly consented live acceptance. This PR does not silently copy local secrets or enable provider billing.
5. Resolve the database retention deadline and cold-start availability expectation. Logo fine-detail inspection and unsupported visual/accessibility cases remain manual.

Rollback: stop new workers and return to the prior application release while retaining additive tables and data. The deployed `36cb8ae` application tolerates extra tables, but feature-specific records/check keys may be inaccessible to that older UI; do not approve new-format runs through an older application. No destructive downgrade command is provided.

Full implementation, test boundaries and recommendation mapping: `docs/improvements-final-report.md` and `docs/improvements-implementation.md`.

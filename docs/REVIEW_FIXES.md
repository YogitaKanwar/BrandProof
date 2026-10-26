# Independent review findings and verification record

Status: the user-approved candidate-first redesign passed focused independent re-review. The reviewer ran 48 targeted tests and additional persisted local API checks and reported no concrete regressions within the declared finite grammar. The parent independently ran the full suite (100 passing), Ruff and formatting, restarted the actual API and verified both HTTP smoke scripts with persisted review readback. This accepts the local backend milestone only, not production security or comprehensive semantic reliability.

## Fixes and evidence

The initial 30 tests did not expose six defects. Regression work now covers:

1. Concurrent first caption saves: one succeeds and the stale writer gets a conflict; immutable initial history is preserved.
2. Review snapshot races: a shared database write-lock strategy serializes caption/source mutations and review insertion. Response state is refreshed after commit. Currentness is not a promise that later edits cannot occur before delivery.
3. Truncated numerical expressions: candidate discovery consumes a whole adjoining numeric-looking token before format validation, rather than comparing a supported prefix.
4. False completed coverage: each exact rule reports its own completed/partial/not_assessed state. Pending/invalid sources and unsupported expressions cannot silently count as assessed.
5. Scope mistakes: cashback, deposits, deadlines, negation and unknown prose require clarification rather than automatic main-price/main-date corrections.
6. Oversized revision inputs: supported integer bounds reserve increment headroom and reject invalid requests with 422, with explicit snapshot exhaustion conflicts.

The first re-review found two remaining parser issues: repeated separators such as INR499..99, and unsupported expressions hidden alongside supported ones. Rushab explicitly selected a conservative full-candidate redesign instead of more regex exceptions or disabling the feature. The implementation now separates candidate discovery, format classification, scope checking, comparison and coverage. A recognized unsupported candidate suppresses all numerical replacement suggestions for that rule kind in the run.

The positive corrected caption is also a regression control: 'An affordable workshop on 2026-11-12. Book for INR 499. Terms apply.' It returns zero findings and completed exact-rule coverage, but the overall run remains partial because AI and poster checks are unavailable.

## Reproducible execution

From the repository root, with the local API running:

    uv run pytest --junitxml=docs/test-results.xml -q
    uv run ruff check .
    uv run ruff format --check backend scripts
    uv run python scripts/smoke.py
    uv run python scripts/parser_smoke.py

Observed verification results:
- 100 tests passed, including synchronized file-backed SQLite concurrency tests.
- The main HTTP smoke test found four planted errors and zero exact findings in corrected copy, persisted the results, and confirmed old run currentness becomes false after editing.
- Ten negative HTTP cases were read back by review ID. Repeated separators, extra fractional digits, Indian grouping, cashback, mixed currency placement, registration deadlines, mixed date formats, malformed dates and prose dates did not receive completed exact coverage or replacement suggestions.
- An oversized revision request returned HTTP 422.
- OpenAPI was regenerated from the running service and Swagger returned HTTP 200.

Machine-readable actual HTTP output is in docs/examples/live-review.json and docs/examples/parser-regressions.json. These use fictional inputs and contain no session tokens. Test results are in docs/test-results.xml.

## Boundaries

Candidate discovery and main-scope matching remain finite declared grammars. They do not recognize every currency, language, number notation, relative date or commercial construction. Unknown formats must remain outside claims of comprehensive analysis. Per-rule completed means the supported checks on recognized candidates completed, not that every possible semantic statement is verified.

PostgreSQL execution, remote deployment, real private-user authentication, model inference, OCR, human content approval, held-out task evaluation and real-user feedback are not included in this milestone. At review acceptance, the implementation had not been committed or published; later publication is recorded in the actual Git history using Rushab’s supplied identity. Independent acceptance applies only to the reviewed local scope. Its machine-readable verdict is in docs/foundation-review.json.

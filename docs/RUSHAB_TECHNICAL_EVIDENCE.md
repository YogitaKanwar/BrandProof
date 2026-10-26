# Rushab's backend technical evidence

Team: YOGI2KANWAR. Scope: Rushab's AI/backend assignment only. Frontend, visual design, final PDF and team submission belong to Yogita and are not implemented here.

## Architecture

FastAPI exposes workspace-scoped campaign, source, content, review and collaboration endpoints. SQLAlchemy persists SQLite records locally. PostgreSQL's psycopg driver is present, but an actual PostgreSQL server has not been exercised. Tables are bootstrapped with create_all; there is no general schema-migration guarantee.

Owner-confirmed source versions are immutable snapshots. A campaign's publication date determines validity. Pending, future and expired versions are excluded explicitly. Uploading a source never makes it authoritative. The API derives canonical rule text from typed inputs; it does not claim PDF guideline import.

Caption saves and image replacements increment one shared content revision. The original caption and all subsequent captions are retained. Image bytes are validated, normalised and stored in the database as private canonical PNG snapshots. Local Tesseract returns word positions/confidence corresponding to that PNG. There is no public file URL or user-supplied filesystem path.

A review locks the campaign while collecting its caption, image and approved source snapshot, computes exact findings and persists a running record. External model work happens after commit without holding the database transaction. Finalisation locks again but preserves the original snapshot; edits during inference make the old run historical, not a review of the new content.

Database locks, expected revisions and unique version/request constraints protect concurrent writes. Tests use actual file-backed SQLite sessions and synchronised competing writers. An in-process mutex is not used as a cross-worker correctness guarantee. PostgreSQL compatibility is a code/configuration path, not an execution claim.

## Exact checks and OCR

The candidate-first parser discovers complete money/date-like tokens before validation. Recognisable unsupported expressions make coverage incomplete and suppress unsafe same-kind numerical replacements. Main price/date comparison is deliberately scoped; qualifiers, cashback, deposits, deadlines, negation and ambiguous values need clarification. Required wording and terminology use bounded literal whole-term matching. This is not unrestricted extraction of business conditions, dates, currencies or time zones.

OCR inputs are PNG/JPEG, at most 5 MiB and 16 million pixels. Normalisation accounts for EXIF orientation and transparency. Tesseract runs with fixed arguments, no shell, a 15-second process deadline and bounded output. Empty, low-confidence and failed extraction remain partial/unavailable. Image findings retain historical poster ID, exact extracted quote, confidence and boxes. Missing text under incomplete OCR must require visual confirmation, not claim proven absence.

Grouped findings link issues sharing category/source/version while preserving individual finding IDs and both assets' original locations. They do not invent evidence that two uncited expressions share the same commercial scope. Images are corrected by reupload, never silent substitution.

## Contextual model

Configured provider: Groq. Verified available and exercised model: openai/gpt-oss-120b. Keys stay in ignored, mode-0600 local .env or a deployment secret store. No key appears in output examples. OpenRouter has an adapter but no live execution claim in this milestone.

External inference requires both deployment enablement and explicit per-request consent. The caption and selected approved reference text are transmitted; no confidential content is appropriate in this public synthetic demo. Retrieval is deterministic keyword selection with mandatory tone/claim policies, not embeddings or a vector database.

Limits include 20,000 draft characters, at most 24 sources/12,000 serialized source-pack characters, one provider request, 1,500 requested output tokens, 65,536 response bytes, 16,000 completion characters and 20 findings. HTTP timeout is per operation (default 15 seconds), not a guaranteed total wall-clock deadline.

JSON-object mode is requested, not claimed as provider-enforced strict schema. Local validation checks IDs, versions, exact source quotes and Unicode draft spans. Rejected findings remain partial, never silently clean. Unsupported claims are not declared false merely because evidence is absent. Verbatim provenance does not prove semantic entailment; reviewers still decide. All model-proposed replacements are withheld.

Persistent conservative provider admission defaults to six workspace reservations and 24 global reservations per rolling hour, with one workspace/two global in-flight calls. Failed attempts count. Admission is bounded synchronous execution, not the originally proposed durable queue. Denials persist unavailable coverage. No automatic retry, account rotation or paid fallback is implemented. Actual provider/account limits can be lower and remain to be confirmed in the account console.

## Human decision invariants

Comments bind to a version pair. Finding decisions append a reasoned history. Creator requests do not approve content. Only an eligible owner/reviewer can decide; an actor who has edited any campaign content cannot approve it through a different requester.

Approval requires current latest review/request, no pending/expired sources and resolved or explicitly excepted blocking issues. Exactly the incomplete required check categories need manual reviewer notes. Those are attestations, not automated completion. In-flight reviews cannot be approved through this manual path.

A caption/image/source edit, newer review/request or changed decision makes earlier readiness stale while retaining history. BrandProof records an internal decision; it does not control publication on external services or provide legal certification. Synthetic role switching is not independent identity verification.

## Measured evidence and limits

- docs/examples/live-groq-probe.json: genuine fictional-input Groq API run, one validated tone finding, persisted readback verified. API probe latency was 1.907 seconds; one example is not a benchmark.
- docs/examples/live-model-evaluation.json: six frozen, author-labelled examples. Three development cases matched expectations with completed contextual coverage. All three heldout cases were unassessed: one rejected finding, two provider failures. No holdout accuracy is claimed, and the original results were not overwritten or tuned away.
- docs/examples/live-review.json: real HTTP four-error example and corrected copy with zero exact findings.
- docs/examples/parser-regressions.json: ten actual HTTP parser cases with saved-result readback and bounded expectation rejection.
- docs/examples/workflow-smoke.json: real HTTP/Tesseract plus explicit suggestions, comments, finding decisions, manual-supplement approval and stale readiness after image replacement. Reviewer actions are scripted, not human feedback.
- docs/examples/installed-wheel-*.json: an installed wheel in a separate environment exercised the API and OCR, not merely imports.
- scripts/restart_probe.py: real two-phase process-restart verification preserved campaign/review. An initial UTC serialization mismatch was reproduced, regression-tested and fixed before the probe passed.
- docs/test-results.xml: measured automated counts; see the current release evidence rather than historical milestone totals.

The original broader evaluation has been reduced. These synthetic examples and regression tests are not interviews, a representative accuracy study, accessibility certification or evidence that unfamiliar users can use the product unaided.

## Deployment, recovery and unresolved work

Dockerfile, Compose configuration, container entry point and deployment instructions are prepared. Python wheel/source builds and local installed-package execution are verified. Docker image build/runtime is not verified because daemon access is denied. Remote hosting was explicitly deferred by Rushab; no cloud resources, HTTPS URL, remote database, sleep behaviour or remote persistence are claimed.

Manual recovery marks interrupted running reviews partial/contextual-unavailable while preserving inputs/findings. Stop every worker before invoking python -m brandproof.recovery --older-than-seconds 300. It is not automatic job orchestration. Local restart proof does not establish cloud recovery or retention.

Remaining release dependencies include hosting/ingress abuse controls, persistent remote storage, actual account limits, broader model evaluation, schema migration/backup policy and verified deletion/retention. Production private accounts are not implemented. Do not represent those tasks as complete or expose the local demo directly to the internet.

## Contribution and reuse

Backend code, tests and technical documentation were produced for Rushab with significant OpenAI-model assistance through Hermes Agent. Human contributions should follow actual review and commit history. No frontend/design contribution is attributed by this document. Third-party packages and Tesseract are reused components; pyproject.toml and uv.lock record dependencies. A project licence is not selected. A secret scan found no configured key in non-ignored project files or Git history; rerun before publication.

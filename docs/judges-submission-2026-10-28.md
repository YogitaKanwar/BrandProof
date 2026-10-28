# Copy-ready judging answers

Public link: https://brand-proof-tau.vercel.app/
Verified public frontend/backend commit: `639fe5fb8a4b43d9a46f1bec503e2b8031273f78`.

These answers distinguish the public release from the Round 3 feature branch. Connected-review deletion and Undo are now live. PDF import, measured accessibility, governance insights and contextual OCR/draft extensions remain on the review branch and are not deployed at this link. The three commitments below are the exact proposed public Round 3 deliverables; do not also promise real SSO, font recognition or universal visual/claim accuracy.

## Your three improvements for Round 3

**Improvement 1: PDF guideline import with traceable evidence**

We will let owners import PDF brand guidelines and review supported structured rule candidates with exact page quotations. Candidates remain pending until the owner confirms them. This replaces repetitive manual entry while keeping every active reference traceable to its document and version. Scanned or unsupported pages will be reported clearly instead of generating invented rules.

**Improvement 2: Measured visual consistency and accessibility checks**

We will add checks for supported brand background colours, text/background contrast where reliable measurement is possible, and poster alt text containing key information. Users will see measurements and locations that need attention. We will evaluate a fixed test set and abstain on unsupported imagery; font-family recognition and complete visual/accessibility certification are not promised.

**Improvement 3: Governance insights with evidence-linked guideline review**

We will summarize recurring finding categories across campaigns and identify source versions frequently dismissed or excepted by reviewers. Owners can inspect the actual findings, source versions and decision reasons before clarifying a guideline. Minimum sample requirements will prevent a few decisions from being presented as a reliable ambiguity trend.

## The list of features you completed

- Isolated fictional demo workspaces with saved campaigns and Recent Reviews.
- Dashboard review deletion with confirmation, Cancel, and in-page Undo while retaining audit history.
- Owner-confirmed price, date, terminology, required-text, tone and claim-policy references.
- Immutable reference versions and publication-date validity checks.
- Caption saving, revision history and explicit removal for poster-only reviews.
- Private PNG/JPEG upload, normalization and historical image retrieval.
- Real Tesseract OCR with extracted text, confidence and responsive word-box highlights.
- Bounded price, date, terminology and required-wording checks against confirmed references.
- Local English claim-risk screening of captions and extracted poster text without requiring an AI provider.
- Explained findings with evidence status, source/version citations and exact supported locations.
- Explicit acceptance of supported caption corrections, creating a new content revision.
- Persisted comments and reasoned reviewer finding decisions.
- Creator review requests and reviewer approval/request-changes with required manual-check notes.
- Approval receipts that become stale when relevant saved content, sources or decisions change.
- Same-browser demo-session recovery using a protected recovery cookie.
- An editable fictional example campaign with confirmed reference facts and flawed caption text.
- Private reference-logo upload, owner confirmation and retained reference versions.
- Responsive desktop and mobile review workspace.
## Technology and implementation details

React 19, TypeScript and Vite power the frontend. FastAPI, Pydantic and SQLAlchemy provide the Python API and persistence. Pillow normalizes images, and local Tesseract extracts text, confidence and word boxes. Deterministic parsers compare supported expressions with owner-confirmed rules; versioned English regex patterns flag selected risky promises for human review.

The public frontend runs on Vercel and proxies API requests to the existing Render Docker service. Render PostgreSQL 16 stores campaigns, source versions, image bytes, review snapshots, comments and decisions. SQLite supports isolated local development/tests. A multi-stage Docker build packages the compiled frontend, API and local OCR runtime.

The technically difficult work was preserving immutable evidence and revision consistency across caption/poster/source edits, rejecting stale concurrent writes, mapping Python Unicode code-point spans into JavaScript correctly, scaling historical OCR boxes, preventing self-approval and restoring the same demo session without browser-stored bearer tokens. Findings and automated coverage are kept separate from human approval.

Optional Groq/OpenRouter integration uses an OpenAI-compatible HTTP API, bounded keyword-selected reference text and exact citation/span validation. It requires server enablement plus explicit consent per review. It is not counted as working live contextual AI in this public release. Regression tests are separate from OCR/model accuracy; we do not report a universal compliance score.

## What changed from your original proposal, and why?

We narrowed the first public release to owner-confirmed structured references, bounded deterministic checks and local OCR so findings could be explained and traced to saved evidence. Automatic document ingestion, broader visual/accessibility checks and cross-campaign governance reporting became the three Round 3 deliverables.

Bounded keyword retrieval replaced vector retrieval, persisted synchronous review snapshots replaced a durable worker queue, and synthetic demo actors replaced production team login for the judging workflow. These choices reduced infrastructure and integration risk while keeping missing coverage visible.

We added immutable revision history, explicit corrections, stale approval receipts, same-browser session recovery, combined poster upload/review, reference-logo storage and local claim-risk screening. Those additions made the core workflow usable even when external AI is unavailable.

## What does NOT work yet?

- Live external contextual AI is not yet accepted as working in the public deployment; unavailable checks remain incomplete and require human review.
- Logo upload/confirmation works, but automatic logo comparison can time out on Render Free compute. Fine-detail logo verification remains manual.
- PDF import, measured colour/contrast and alt-text checks, and Governance Insights are on the review branch, not the judges' public release.
- OCR can miss or misread text. Complex layouts, low-confidence extraction and unsupported claim/price/date formats require manual inspection. Local claim screening is bounded English pattern matching, not general truth or legal-compliance verification.
- Demo roles are synthetic and do not represent real authenticated team members or independent humans.
- Free backend cold starts can take up to 90 seconds; the page now waits with a starting-service message before submitting. Longer outages still report an error. Current Free PostgreSQL expires 27 November 2026, so long-term retention is not promised.

## Delete option implementation note — verified live

Connected Recent Reviews now has explicit Delete/Cancel/Confirm and Undo on the public dashboard. Owner-authorized, revision-checked removal hides the campaign from the list and rejects normal reads/writes, retaining original audit/image/source data. Running reviews cannot be deleted. Undo is bound to the exact deletion ID so an old Undo cannot restore a later deletion; its handle is lost on full reload. Startup adds only `campaign_removals`; it does not drop existing data. This is reversible workspace removal, not permanent data erasure. The original local-draft deletion remains supported.

The isolated public release passed 501 backend tests, 53 frontend tests, lint/build, eight live HTTP suites and public browser Delete/Cancel/Undo/mobile/reload checks. A pre-deployment fictional persistence probe confirmed unchanged session, source, review and image bytes across the backend release. See REVIEW_DELETION_RELEASE.md.

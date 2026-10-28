# Yogita's frontend integration handoff

## Manual-audit fixes — 28 October 2026

`POST /api/v1/campaigns/{campaign_id}/caption/clear` accepts `{ "expected_revision": n }` and returns CampaignOut. It requires an owner/creator, an existing saved poster and the current content revision. It records an empty-caption revision, retains the poster/history and invalidates previous review/approval currency. Ordinary PUT /caption still rejects empty text. The UI asks for explicit confirmation through Remove saved caption. See the regenerated OpenAPI contract.

Workflow, campaign, source and caption-revision timestamps now include UTC timezone metadata, including SQLite readback. OCR uses bounded variable-size column segmentation and preserves actual TSV line boundaries/offsets. Required wording and terminology accept whitespace across line wraps. An OCR extraction completing does not certify all text was read. Qualifiers such as “only if” or negative copy still require clarification; source applicability remains separate from source confirmation.

Known caption conflicts immediately stale the visible review and disable correction, comment and human-request controls until reconciliation. Source cards expose expired/future applicability and confirmation messaging respects it. Audit baseline and fix verification: MANUAL_QA_2026-10-28.md.

## Setup and scope

Run locally from this repository. http://127.0.0.1:8000 is not a public URL. Swagger: /docs; live contract: /openapi.json; saved contract: docs/openapi.json. Default CORS: http://localhost:5173 and http://127.0.0.1:5173. Never put provider keys in browser code.

Sources, caption/poster revisions, exact findings, real local OCR, contextual-provider integration, comments, explicit suggestions, decisions, requests and receipts are implemented. Provider contract tests simulate the network. A genuine Groq openai/gpt-oss-120b API probe is also recorded; a reduced six-case evaluation had three assessed development matches and three unassessed holdouts, not a validated accuracy benchmark. Visual branding, accessibility and contextual poster analysis are not automated. Independent foundation acceptance does not cover this new milestone; see STATUS.md.

POST /api/v1/demo-sessions without a body creates an isolated fictional workspace and owner/creator/reviewer tokens. Store tokens in memory, never logs; attach Authorization: Bearer <token>. Every new session creates another sandbox. Show the synthetic-demo notice. Role switching is not production auth or proof of independent human sign-off. Do not upload confidential materials.

Session continuity added 2026-10-27: creation also sets a 24-hour HttpOnly, SameSite=Strict browser cookie scoped to /api/v1/demo-sessions. POST /demo-sessions/resume with X-BrandProof-Session: resume and credentials:include returns the same workspace, actor IDs and role tokens without extending expiry or writing records. The cookie is Secure by default; explicitly set BRANDPROOF_DEMO_COOKIE_SECURE=false only for local HTTP. Session responses use no-store. Missing/invalid/expired cookies return 401 without creating a sandbox; unsafe browser provenance returns 403. Do not automatically create on a failed resume. Use a same-origin frontend/API proxy in production. Cookie-only access to campaign APIs is not supported; those still require the in-memory role bearer.

Owner configures sources and can perform content/reviewer actions except self-approval. Creator edits content, comments and requests review; no source confirmation/decisions/approval. Reviewer reads/comments, decides findings and approves/requests changes; no content/source edits. Server permissions are authoritative.

POST /api/v1/campaigns with {"name":"Workshop","publication_date":"2026-11-12"}. GET /campaigns lists this workspace; GET /campaigns/{id} returns caption/content_revision/source_revision. Remaining paths below start with /api/v1/campaigns/{id}. Fetch actual revisions; never hardcode examples.

## Sources

POST /sources with {"title":"Workshop price","rule":{"kind":"price","amount":"499","currency":"INR"}} returns pending version 1. Owner POST /sources/{source_id}/confirm with {"expected_version":1} creates approved version 2. Source text is server-generated from typed rules, not PDF extraction or independent proof. Its status determines authority.

PUT /sources/{source_id} includes expected_version plus full title/rule/validity fields; omitted optional dates are cleared. Edits create pending versions; old approvals remain historical, not active. GET /sources lists heads; GET /sources/{source_id}/versions reads history. Source actions increment source_revision.

Other rules:

    {"kind":"date","date":"2026-11-12"}
    {"kind":"terminology","term":"cheap","preferred":"affordable"}
    {"kind":"required_text","text":"Terms apply"}
    {"kind":"tone","guidance":"Use a calm, respectful tone."}
    {"kind":"claim_policy","guidance":"Objective promises require supporting evidence."}

Optional valid_from/valid_until are checked against publication_date. Price currencies: INR/USD/EUR/GBP. Price/date represent only the main campaign value. Pending/expired/not-yet-valid sources are explicitly excluded.

## Caption, images and history

PUT /caption with {"expected_revision":1,"text":"Our cheap workshop. Terms apply."}. Whitespace is preserved; max 20,000 characters, no blank text. Saves increment content_revision. GET /revisions returns chronological {revision,caption,created_at}, including the initial revision. Poster uploads share this revision and preserve the caption.

PUT /posters?expected_revision=<current content revision> takes raw PNG/JPEG bytes with matching Content-Type, not JSON/base64/multipart. Limits: 5 MiB input, 16 million pixels. The server validates format, normalises orientation/transparency into PNG, runs local Tesseract, then rechecks revision; concurrent edits return 409.

GET /posters returns latest metadata. GET /posters/{poster_id} returns historical metadata. GET /posters/{poster_id}/content returns authenticated canonical PNG. Fetch with Authorization and create a temporary object URL; a bare img URL lacks the bearer header. Revoke object URLs on replacement/unmount.

Metadata includes id/content_revision/dimensions/SHA-256 and ocr:{engine,status,reason,text,words}. Words include text, code-point start/end, x/y/width/height and confidence [0,1]. Coordinates refer to canonical PNG; scale overlays by displayed/stored dimensions. Below 0.7 confidence is partial; unreadable/tool failures are not clean results.

OCR is not complete image review: logos, typography, contrast/accessibility and contextual poster claims require manual inspection. Revise an image by reuploading it.

## Review, evidence and privacy

POST /reviews with {"expected_content_revision":2,"expected_source_revision":4,"external_ai_consent":false}. Normally returns HTTP 201 after analysis. This is not a durable task queue. A running snapshot is persisted before an external call; GET /reviews or /reviews/{review_id} may show running. Wait for completion before approval. A crash can leave a running record; start a new review, never treat it as approved.

Contextual calls require BOTH server enablement and explicit external_ai_consent:true per request. Default is off. Consent must explain that caption and selected approved source text leave this server for the configured provider. Never silently opt users in. No frontend keys. Missing config, denial, quota/timeout/refusal/invalid output leave incomplete coverage, not fabricated results.

Retrieval is bounded keyword selection with mandatory tone/claim-policy rules, not embeddings. Citations/spans are validated against the selected pack. Provenance is not proof of semantic entailment or claim truth. Contextual replacements are withheld; contextual poster analysis is not included.

Runs bind immutable caption, approved sources, poster identity/extraction and findings to content/source revisions. External calls do not hold a campaign writer lock. An edit during inference can make the returned snapshot historical (is_current:false); show that and rerun.

The additive finding_groups array groups issues by category and the same approved source/version, retaining individual finding_ids and assets. The findings array remains authoritative for exact locations; no locations are merged or invented. Findings expose id/category/severity/evidence_status/message/location/evidence/suggested_replacement. Caption offsets are Python Unicode code points, end-exclusive: use Array.from(caption).slice(start,end) in JS for emojis/non-BMP characters. Missing wording has null offsets; show a whole-asset action, not a fake highlight. Render all text as text, not unsanitised HTML.

Poster locations include asset=poster, poster_id, boxes and optional ocr_confidence. Highlight the historical poster belonging to this run, not latest now. Boxes can be empty for missing wording. Low-confidence affected words need clarification; OCR findings ask reviewers to verify the image.

Evidence includes source_id/source_version_id/source_version and exact canonical quote. Distinguish contradicted, needs_clarification and insufficient_evidence. Lack of support is not proof of falsehood; severity is not certainty.

Checks report status/reason, per-rule coverage and details. No supported price/date expression means not_assessed, not pass. Finite parsing abstains on ambiguous scope/qualifiers/cashback/deposits/deadlines/negation/recognised unsupported numeric tokens. One unsupported candidate can suppress same-kind numerical replacements. This is not unrestricted language understanding.

A completed run means its declared checks completed, not human approval. Attached posters remain partial because visual/accessibility/contextual image checks are incomplete. is_current is a snapshot, not a guarantee against later edits.

## Collaboration and approval

Creator/owner POST /reviews/{review_id}/findings/{finding_id}/apply with both expected revisions explicitly applies an available verified caption substitution, checks the exact original span and creates a revision. Replay/staleness returns 409. Contextual/unsupported/image edits require manual action. Reload and rerun after edits.

All roles POST /comments with {"expected_content_revision":2,"expected_source_revision":4,"review_id":"<review id>","text":"Please verify this wording."}. review_id is optional. Comments bind to current revisions and remain historical. GET /comments reads the thread.

Owner/reviewer POST /reviews/{review_id}/findings/{finding_id}/decisions with both expected revisions, expected_decision_version (initially 0), decision (dismiss/exception/reopen) and a required reason. Each append increments version. GET the same path reads history. Error findings, insufficient evidence and clarification block approval until corrected or explicitly decided; ordinary warnings remain visible.

Creator/owner POST /reviews/{review_id}/requests with both expected revisions creates a request, NOT approval.

Reviewer/eligible owner POST /reviews/{review_id}/approvals:

    {"expected_content_revision":2,"expected_source_revision":4,"request_id":"<request id>","decision":"approve","reason":"Explain the decision.","manual_checks":{"contextual":"Describe the actual manual tone and claim checks performed."}}

Decision is approve or request_changes. Approver must differ from requester and must not have edited ANY content revision in this campaign. Switching requester cannot bypass self-approval. One decision per request; another decision needs a fresh request.

Latest review/request must be current and not running. Approval requires active sources, no excluded sources and no unresolved blocking findings. manual_checks must name EXACTLY the incomplete required checks: exact_text/contextual, plus poster when attached and claim_risk when recorded on the run. Collect actual reviewer notes (minimum 20 characters); never auto-fill claims that the person performed them. request_changes uses an empty manual_checks object.

Manual notes do not change automated coverage. approved_with_manual_checks can coexist with partial automation: a reviewer attestation, not an AI pass or legal certification.

GET /receipt returns readiness, scope, checks, sources, request/approval history and latest finding decisions. Readiness: not_approved/approved/approved_with_manual_checks/changes_requested/stale. Never infer readiness from zero findings. Caption/poster/source edits, newer reviews/requests and decision changes stale earlier readiness while retaining history. BrandProof does not control external publication.

## Errors and acceptance

Errors: {"error":{"code":"...","message":"..."}}. 401 invalid/expired token; 403 forbidden role/self-approval; 404 absent/inaccessible resource; 409 stale/superseded state, unresolved findings, incomplete checks or unsafe edit (reload/reconcile, do not blindly replay); 413 byte limit; 415 unsupported media; 422 invalid fields/image/bounds. Never turn errors into green checks.

With a running API:

    uv run python scripts/smoke.py
    uv run python scripts/parser_smoke.py
    uv run python scripts/workflow_smoke.py

The last script uses real HTTP and Tesseract. Its exceptions/notes/approval are scripted demo actions, not user feedback. Saved results contain no tokens. These tests do not establish frontend completion, deployment, PostgreSQL support or real user testing.


## Reference-logo comparison (2026-10-27)

See [LOGO_COMPARISON_REVIEW.md](LOGO_COMPARISON_REVIEW.md) for actual new routes, raw PNG/JPEG format, owner confirmation, private image fetching, source revision changes and checks.poster.details.logo. Sources panel includes Brand logo. Results show possible mismatch plus historical reference/whole poster; no inferred bounding box or content approval. This is a bounded plain-background template comparison, not reliable subtle-logo-change or forgery detection. API contract regenerated in openapi.json.


## Local claim-risk screening — 28 October

New runs add `checks.claim_risk`; caption and OCR-based poster findings use category `claim_risk`, warning severity and `needs_clarification`, with no invented source evidence or replacement. This works with no approved facts and AI disabled. Partial claim coverage requires dedicated reviewer notes in addition to explicit finding disposition. Existing runs without this check remain unchanged. See [CLAIM_RISK_SCREENING.md](CLAIM_RISK_SCREENING.md) for supported patterns, limits and the judge demonstration. Saved OpenAPI includes the new manual-check key.

# Yogita's frontend integration handoff

## Scope and address

The implemented surface is the source/copy/exact-findings path. Comments, content approval, AI and images are not implemented. Build those screens against agreed future contracts only; do not display them as working.

Rushab's running local API uses http://127.0.0.1:8000. That address only reaches the current machine. On your own machine, run the backend locally from this repository or use an explicitly provided hosted API once deployment is complete. There is no public backend URL yet.

Interactive contract: /docs. Machine contract: /openapi.json (snapshot in docs/openapi.json). CORS currently permits http://localhost:5173 and http://127.0.0.1:5173. Vite can proxy /api to localhost:8000, or a frontend can use an API base URL. Browser code must never contain a model key.

## Integration order

1. POST /api/v1/demo-sessions with no body. Store the returned workspace ID and demo actor tokens in memory for the session. Show the synthetic-demo notice. Do not log tokens. Every new call creates a fresh isolated workspace.
2. Use the owner bearer token for source setup; creator for content work; reviewer for read-only inspection at this stage. Attach Authorization: Bearer <access_token> to protected requests. These are demo roles, not production identity or actual sign-off.
3. POST /api/v1/campaigns with name and publication_date (YYYY-MM-DD). GET /campaigns lists only the current workspace. GET /campaigns/{id} returns caption/content_revision/source_revision.
4. Create sources, then explicitly confirm them. Reload campaign state after source actions because source_revision changes.
5. Save a caption using its expected content revision.
6. Read current campaign state and start a review with BOTH expected content/source revisions.
7. Display findings, evidence, coverage, excluded sources and historical status. All runs remain partial in this milestone.

## Source setup

POST /api/v1/campaigns/{id}/sources

    {"title":"Workshop price","rule":{"kind":"price","amount":"499","currency":"INR"}}

The response is pending version 1. Text is derived on the server from the typed rule; it is not a quote extracted from an uploaded PDF. Mark its status clearly even though the canonical wording says 'approved campaign price'. To confirm:

POST /api/v1/campaigns/{id}/sources/{source_id}/confirm

    {"expected_version":1}

Confirmation produces a new approved version 2 and records confirmed_by. The owner can revise a source with PUT to the source path, including expected_version plus its full title/rule/validity fields. Omitted optional dates are cleared, not preserved. Every edit is pending; the previous approved version is no longer active. GET /sources lists current heads; GET /sources/{source_id}/versions returns history.

Other rule examples:

    {"kind":"date","date":"2026-11-12"}
    {"kind":"terminology","term":"cheap","preferred":"affordable"}
    {"kind":"required_text","text":"Terms apply"}
    {"kind":"tone","guidance":"Clear and helpful; avoid exaggeration."}
    {"kind":"claim_policy","guidance":"Objective promises need approved supporting evidence."}

Sources accept optional valid_from and valid_until dates. Price currency is currently one of INR, USD, EUR, GBP; scope is campaign_main_price. Date scope is campaign_main_date. Tone/claim guidance is stored but contextual checks are not connected.

## Caption and review

PUT /api/v1/campaigns/{id}/caption

    {"expected_revision":1,"text":"A cheap workshop on 2026-11-13. Book for INR 599."}

The result increments content_revision. Whitespace is preserved so offsets refer to the stored exact caption. Empty/whitespace-only and oversized captions are rejected.

POST /api/v1/campaigns/{id}/reviews

    {"expected_content_revision":2,"expected_source_revision":8}

The source revision above is illustrative: always fetch the actual value, never hardcode it. The endpoint synchronously completes a bounded exact review and returns HTTP 201 with a persisted run. It is NOT yet a queued AI job. Use GET /reviews or /reviews/{review_id} to load historical results.

## Finding rendering

Each finding includes id, category, severity, evidence_status, message, location, evidence and optional suggested_replacement. Location is currently caption-only with start/end offsets (Python Unicode code-point indices, end-exclusive) and quote. JavaScript uses UTF-16 indices; convert using Array.from(caption) before slicing when emojis/non-BMP characters occur. A missing required phrase has null offsets and quote: show it as a whole-caption action, not a fabricated highlight.

Evidence includes source_id, source_version_id, source_version and the exact canonical source quote. It proves which owner-confirmed rule produced the finding; it is not independent substantiation of a promotional claim.

When evidence_status is needs_clarification, show the reason and request owner input rather than an automatic replacement. Do not interpret severity as certainty. Never apply suggested_replacement automatically; explicit edit saving is available, but individual suggestion-acceptance and concurrency-safe suggestion application are future workflow work.

## Coverage and stale state

- status: partial for all runs until contextual/poster scope is implemented.
- checks.exact_text: completed / partial / not_assessed, with reason. Its rules array reports source_id, source_version, kind, status and reason for each applicable exact rule. No comparable supported price/date expression means not_assessed; do not display it as a successful comparison. Missing required wording and terminology are independently assessed.
- Price/date scope follows a deliberately narrow grammar. Ambiguous amounts, cashback/deposits, offer qualifiers, registration deadlines and negation require clarification without automatic replacements. Candidate discovery also recognizes suffix-currency notation, selected prose/slash dates and malformed numerical tokens as unsupported. If one recognized candidate of a kind is unsupported, the engine suppresses all numerical replacements for that kind and downgrades coverage; one supported expression cannot hide the unsupported one. This is not exhaustive natural-language extraction.
- checks.contextual: unavailable; checks.poster: not_assessed.
- excluded_sources: source ID/version/kind and reason for pending or invalid sources.
- sources_used: immutable approved source snapshots used by that run.
- is_current: compares run content/source revisions with campaign's current versions.
- readiness: not_approved. No approve control should appear functional yet.

A corrected caption can have zero exact findings and still need contextual review. Editing a caption/source makes historical runs not current without changing their findings. Conservative invalidation includes pending source changes.

## Errors and permissions

All API errors use {"error":{"code":"...","message":"..."}}; validation can also include safe location/message details. Check HTTP status:
- 401: missing/invalid/expired token; start a new demo session.
- 403: current demo role cannot perform that action.
- 404: missing or inaccessible resource; never assume the other workspace exists.
- 409: expected revision/version is stale; reload and let the user reconcile. A source snapshot at its supported limit also returns a conflict rather than overflowing.
- 422: invalid input; show a useful field-level message. Expectation fields have portable integer limits; mutation expectations reserve room for the next version.

Owner: create campaigns, create/edit/confirm sources, save caption and run review.
Creator: create campaigns, save captions and run review; cannot edit/confirm sources.
Reviewer: read campaigns, sources and runs; approval is not implemented yet.
Server enforces these permissions; changing UI visibility does not grant a role.

## What you can finish now

Y01/Y02/Y03/Y05 can connect to real endpoints. Y06 can start caption revision interactions but comments/decision APIs are still pending. Y04/Y07/Y08 need later poster/approval contracts. Use labelled development fixtures for unfinished areas, never fake working results in the submitted live path.

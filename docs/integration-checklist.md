# Integration map (Y01 scope)

Sources: `FRONTEND_HANDOFF.md` (actual filename), `openapi.json`, backend routes/schemas and `plan.md`. All protected routes use Bearer demo actor tokens. No model credentials belong in the frontend.

| Task | Actual contract | Frontend reuse / gap |
| --- | --- | --- |
| Y01 | POST `/api/v1/demo-sessions`, no body/auth -> `DemoSessionOut`: workspace_id, mode=synthetic_demo, notice, expires_at, actors[role]={role,access_token}. POST `/api/v1/campaigns` with `CampaignCreate`={name,publication_date}; GET same route -> CampaignOut[]; GET `/{campaign_id}` -> CampaignOut. Creator/owner create; all demo roles read. | Reuse dashboard, form, transport and ReviewAdapter. Backend campaign is a draft grouping, NOT a ReviewOut. Add publication date. Preserve exact response: id,workspace_id,name,publication_date,caption,content_revision,source_revision,created_at. Brand/brief are local context, not CampaignCreate fields. |
| Y02 (mapped only) | POST/GET `/api/v1/campaigns/{campaign_id}/sources`; PUT `/{source_id}`; POST `/{source_id}/confirm` with {expected_version}; GET `/{source_id}/versions`. Owner mutates/confirms. SourceCreate={title,rule,valid_from?,valid_until?}; SourceUpdate adds expected_version. SourceOut includes id,version_id,version,title,status,rule,text,valid_from,valid_until,confirmed_by,created_at. | Reuse Reference Information. Typed rule kinds: price(amount,currency INR/USD/EUR/GBP, campaign_main_price scope), date(date,campaign_main_date scope), terminology(term,preferred), required_text(text), tone/claim_policy(guidance). Freeform context is not automatically a rule. Sources start pending; confirmation creates a new approved version. Editing returns to pending. Version is server-generated. No source API wired in Y01. |
| Y03 (mapped only) | PUT `/api/v1/campaigns/{campaign_id}/caption` with {text,expected_revision} -> CampaignOut. POST `.../reviews` with {expected_content_revision,expected_source_revision} -> ReviewOut (201). Creator/owner mutate/run. | Reuse caption editor and errors; local saves are not remote revisions. Exact stored whitespace matters. Fetch current revisions; never hardcode them. Runs are synchronous bounded exact checks, not queued AI jobs. |
| Y05 (mapped only) | GET `.../reviews` and `.../reviews/{review_id}` -> ReviewOut/list. Includes id,campaign_id,content_revision,source_revision,caption,status,is_current,readiness,checks,sources_used,excluded_sources,findings,created_at. Finding: id,category,severity,evidence_status,message,location,evidence,suggested_replacement. | Future result renderer must show immutable source/version evidence, excluded sources, per-rule coverage and stale history. Python code-point offsets need Array.from(caption) conversion. Null offsets are whole-caption actions. All current runs remain partial, readiness not_approved; zero findings != approval. Never auto-apply replacements. |
| Y06–Y08 | Caption/source revisions and historical stale status exist. Comments, correction acceptance, human content decisions/receipts, image upload and OCR routes do not exist. Contextual AI unavailable; poster not_assessed. | Keep caption/poster draft UI; no working approval, comment, OCR or AI claims. |

## Error and session contract

Actual runtime errors are `{error:{code,message,details?:[{location,message}]}}` from backend/errors.py. OpenAPI still lists standard HTTPValidationError for 422: document this mismatch, parse actual runtime envelope. 401: explicitly start a new demo (never silently rotate); 403: denied role; 404: inaccessible/missing resource; 409: stale expectation, reload/reconcile; 422: display safe field details. Do not fallback permission/validation failures into apparent local success.

Tokens and workspace ID stay in JS memory. Existing database campaigns persist server-side, but a page reload loses the only access tokens. POST demo-sessions always creates a NEW workspace; there is no resume/token-refresh route. Persisting a campaign ID alone cannot restore access. Do not put tokens in localStorage/sessionStorage/URLs/logs. To satisfy refresh access Rushab must add a server-managed session/resume contract (e.g. HttpOnly, SameSite cookie plus authenticated resume returning the same workspace, expiry/logout and appropriate CSRF/CORS), or explicitly revise the memory-only policy. Y01 refresh persistence is therefore partial. Local fixtures remain separately labelled and preserved, never silently uploaded.

## Y01 acceptance checks (refresh access remains blocked above)

- [x] Explicit demo connect; show synthetic notice and refresh limitation.
- [x] Creator bearer token for protected campaign create/list/get; keep owner/reviewer only in memory for later work.
- [x] Exact name/publication_date payload; preserve returned revisions and retrieve selected campaign.
- [x] Vite `/api` proxy for local dev/preview; no credentials hardcoded.
- [x] Envelope errors, no silent reconnection/mutation fallback, real HTTP and browser tests.
- [x] Preserve one-page reference/content workspace, local drafts and honest unfinished Y02+ controls.

## Y02 implementation verification

- [x] Same demo owner token for source mutations, creator token for reads; no persisted tokens or session-policy workaround.
- [x] Source create/list, explicit confirm, version-aware edit and immutable history connected. Reload sources/campaign state after mutations.
- [x] Six typed rule kinds, no automatic guideline extraction or owner approval. Server versions read-only; publication-date validity and pending exclusions explicit.
- [x] Real INR 499 pending v1 -> approved v2, source_revision increments, edits become pending, 403/409/422 and pending exclusion verified. Browser concurrency test preserves stale entries and blocks stale writes.
- [x] Y01 refresh limitation retained. Stop for Yogita's Y02 review; no Y03 implementation or deployment.

The table records the initial gaps. Y02 is connected in api/backend.ts and LiveSources.tsx. Subsequent authorised work connects Y03 caption/review/history endpoints and Y05 evidence/coverage/stale result rendering in LiveCaption.tsx and ReviewResults.tsx. Y04 upload persistence and Y06-Y08 missing contracts remain blockers; see task-status.md.

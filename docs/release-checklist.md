# BrandProof release handoff

Current fix branch: fix/demo-session-resume. Protected frontend checkpoint: a93f782. Backend PR #1: cdda60fd48371662a1380f82029836960271aa76. Current history already includes merged frontend integration PRs. This continuation adds browser-session recovery and its frontend connection; no deployment/publication was performed.

- [x] Existing frontend protected and new backend merged without conflicts.
- [x] Sources/caption/reviews reverified against current schemas.
- [x] Private raw PNG/JPEG upload/replacement/retrieval connected, including real error/conflict responses.
- [x] Poster findings render historical canonical images and responsive boxes; bounds/geometry tested.
- [x] Persisted comments, explicit corrections, revisions and reviewer finding decisions connected.
- [x] Creator requests, reviewer decisions, exact incomplete-check manual notes, receipts and stale history connected.
- [x] Consent-required contextual calls wired with no browser secrets or automatic opt-in.
- [x] Local frontend build/lint/service/browser and genuine HTTP checks pass; backend runtime failures recorded rather than masked.
- [ ] Real Tesseract/Groq final acceptance on a configured backend. Local missing prerequisites are not success. See configured-backend-tests.md.
- [ ] Real-user accessibility/usability feedback and hosted end-to-end/restart/private-image tests.
- [x] Session-resume contract and frontend recovery verified locally; secure-cookie and production proxy requirements documented.
- [x] Editable fictional example creates real source/content records and leaves findings/approval to actual actions.
- [ ] Hosted cookie recovery, public security/CORS/durable storage and final submission evidence.
- [ ] Yogita's explicit deployment/main-merge approval.

Testing flow and API mappings: integration-sprint.md. Current counts/task status: task-status.md. Backend hosting/security scope: BACKEND_DEPLOYMENT.md. A built bundle is not a deployed or fully configured product.

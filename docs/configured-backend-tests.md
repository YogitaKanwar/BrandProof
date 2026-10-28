# Final tests requiring a fully configured backend

These are remaining acceptance tests, not features silently reported complete. Continue frontend work against local responses; do not wait for public hosting or fabricate outputs.

- [ ] Real Tesseract extraction on canonical PNG/JPEG, including rotated/transparent inputs, blank images, low-confidence text and unavailable/tool timeout. Windows currently returns tool_missing.
- [ ] Approved reference price INR 499 vs actual poster INR 599 -> real poster contradiction. Inspect real boxes at desktop/mobile sizes; verify old-run overlays keep their historical poster after replacement.
- [ ] Live Groq: consent false makes no external call; explicit true with server enablement/key/model produces actual validated contextual output. Verify unsupported guarantees mean missing substantiation/clarification, not proven falsehood. Preserve refusals/quotas/timeouts as incomplete.
- [ ] Overlay DOM and screenshots with genuine OCR boxes. Pure percentage/bounds tests pass locally but do not prove OCR quality.
- [x] Replay full backend suite on its documented Linux/font/Tesseract runtime. On 27 October: 419 passed, including the new session-recovery tests; lint and formatting passed. The earlier Windows prerequisite failures remain historical evidence, not the current Linux result.
- [ ] Public HTTPS frontend/API: CORS/authenticated private images, exact revisions, comments, source/caption/poster stale receipts and provider outage. Test page refresh/session contract honestly.
- [ ] Persistent database/images/receipts survive actual service restart/redeploy; verify storage/retention/security limits from BACKEND_DEPLOYMENT.md.
- [ ] Real reviewer usability and accessibility feedback. Test actual incomplete-check notes without prefilled attestations; scripted local approvals are not user feedback.
- [ ] Final release URL, submission screenshots/materials, ownership/provenance and account-specific provider quota checks.

Local additions verified 27 October: session-cookie resume preserves the existing campaign/actor identity across reload; three real HTTP smoke scripts passed with completed Tesseract extraction and poster-price findings. The seven frontend HTTP scripts passed; their small poster fixture correctly reported partial/low-confidence OCR. No fresh live-model call, public deployment or full Chrome/CDP regression is claimed by these results.

This checklist does not authorise a paid service, public deployment or system-level OCR installation.

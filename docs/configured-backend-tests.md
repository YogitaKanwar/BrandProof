# Final tests requiring a fully configured backend

These are remaining acceptance tests, not features silently reported complete. Continue frontend work against local responses; do not wait for public hosting or fabricate outputs.

- [ ] Real Tesseract extraction on canonical PNG/JPEG, including rotated/transparent inputs, blank images, low-confidence text and unavailable/tool timeout. Windows currently returns tool_missing.
- [ ] Approved reference price INR 499 vs actual poster INR 599 -> real poster contradiction. Inspect real boxes at desktop/mobile sizes; verify old-run overlays keep their historical poster after replacement.
- [ ] Live Groq: consent false makes no external call; explicit true with server enablement/key/model produces actual validated contextual output. Verify unsupported guarantees mean missing substantiation/clarification, not proven falsehood. Preserve refusals/quotas/timeouts as incomplete.
- [ ] Overlay DOM and screenshots with genuine OCR boxes. Pure percentage/bounds tests pass locally but do not prove OCR quality.
- [ ] Replay full backend suite on its documented Linux/font/Tesseract runtime. Current Windows run: 310 passed, 21 failed, 1 collection error from font/OCR prerequisites. No backend tests changed to mask this.
- [ ] Public HTTPS frontend/API: CORS/authenticated private images, exact revisions, comments, source/caption/poster stale receipts and provider outage. Test page refresh/session contract honestly.
- [ ] Persistent database/images/receipts survive actual service restart/redeploy; verify storage/retention/security limits from BACKEND_DEPLOYMENT.md.
- [ ] Real reviewer usability and accessibility feedback. Test actual incomplete-check notes without prefilled attestations; scripted local approvals are not user feedback.
- [ ] Final release URL, submission screenshots/materials, ownership/provenance and account-specific provider quota checks.

No paid service, public deployment, system-level OCR install or backend modification is authorised by this checklist.

# BrandProof agent instructions

- Use docs/plan.md for product scope and updated docs/FRONTEND_HANDOFF.md plus docs/openapi.json for actual API contracts. Keep original plan.pdf; do not repeat extraction.
- Yogita owns React/TypeScript/Vite frontend and integration. Rushab owns backend/AI/OCR/database. Backend modifications require a confirmed defect and user agreement.
- Current sprint authorised all frontend integration slices, locally and independently. Do not wait for hosting; report unavailable OCR/Groq truthfully. Do not install unrelated infrastructure.
- Work on integration/round2-backend-pr1. Preserve main and pushed frontend checkpoint a93f782. PR #1 exact backend commit: cdda60fd48371662a1380f82029836960271aa76. No reset, force-push or merge into main without approval.
- Demo workspace/tokens stay in memory, never logs/storage/URLs. No provider secrets in frontend. AI requires explicit per-review consent and server enablement.
- Source confirmation != content approval. Never invent findings, boxes, attestations or approvals. Use actual versions/roles; require explicit suggestion acceptance and real manual-check notes.
- Preserve the minimal navy/white/teal design and one review workspace. Reuse dependencies/components. Verify each slice with lint/build and relevant genuine API/browser tests.
- Update docs/task-status.md after slices. Keep final configured-runtime acceptance separate in docs/configured-backend-tests.md.
- No deployment or publication of main authorised. Keep updates concise: completed, tests, blockers, next action.

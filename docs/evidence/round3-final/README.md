# Final evidence index - 2 November 2026

Tested application/tests: **61dfa47dc8c4d34b0a006280fb45253a52dd20db**. Public Vercel/Render source: **e01f52b6ee02b6c85c480619cfc82cc486a56123**. The final documentation commit can differ without changing the tested application. No push/deployment was performed.

- `backend-tests.xml`: final full suite, 594 collected / 576 passed / 18 optional font skips / 0 failures.
- `backend-initial.txt`: retained first-run two recovery subprocess timeouts; subsequent focused/full passes are described in final QA.
- `frontend-verify.txt`: final 62 tests, lint/build and seven HTTP suites; removal/PDF separately passed.
- `local-judge/`, `public-judge/`: genuine screenshots and sanitized judge journey summaries; public failure.png retains initial cold-start failure.
- `local-improvements/`, `public-improvements/`: actual shipped seven-rule PDF, expanded quote, numeric 21:1 contrast against 4.5 target on a controlled real Noto72 black/white poster, Insights/sample/history screenshots. Public uses explicit saved-description reload; candidate does not. Local failure.png records the pre-fix journey, not final success.
- `errors/`: actual loopback browser 503/10-second timeout injection, preserved draft, duplicate activation and invalid-PDF recovery.
- `local-pdf.json`, `public-pdf.json`: both shipped PDFs through real HTTP, no precomputed findings/approval.
- `restart.json`: actual isolated process replacement, ten unchanged resource readbacks, session/role continuity, credentials held in memory.
- `deployed-ci.json`: successful GitHub CI at deployed e01f52b, **not** fresh final-candidate container CI.
- `public-readonly.json`: initial health/contract/asset probes, including proxy 502 and direct health recovery. Candidate JS differs intentionally; CSS/PDF bytes match. Vercel /openapi.json 404 is expected because only /api is proxied.
- `summary.json`: sanitized counts, release boundary and SHA-256 of selected tested files.

Full commands, initial failures, retries, clean setup and unrun gates: ../../ROUND3_FINAL_QA.md. No raw bearer, cookie jar or workspace identifier is written here. Only fictional UI screenshots and non-credential evidence are included.

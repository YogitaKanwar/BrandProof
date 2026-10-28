# Backend deployment package — Rushab

Current update, 28 October 2026: the Docker package now includes the compiled React frontend and serves it with the API under one origin. [FREE_HOSTING.md](FREE_HOSTING.md) is the current Render Free + Neon Free setup guide. No cloud resources have been created and there is no public project URL. The operational boundaries below still apply.

## What is prepared and what is exercised

Dockerfile: Node 24 builds React using the frontend lockfile; Python 3.12 runs locked Python dependencies via uv, Pillow, Tesseract English OCR, Noto fonts, non-root UID 10001, one Uvicorn worker and a database-backed health probe. The entry point reads PORT (1–65535) and disables access logs. compose.yaml keeps the port on loopback, persists /app/data in a named volume and applies basic container restrictions. .dockerignore allows only required source/build manifests and excludes local data and credentials.

The Python wheel/source package builds with `uv build`. The entry-point contract and local API/OCR are tested. `docker compose config --quiet` validates the Compose configuration. Docker image build/start is NOT verified: this machine denies access to the Docker daemon. Installing a Dockerfile is not a deployment success.

## Local container route, once Docker access is available

    docker compose build
    docker compose up -d
    docker compose ps

Open http://127.0.0.1:8000/api/v1/health and /docs. Run the three scripts in README.md against that address. Test actual OCR, not merely health. Do not use `down -v`: that removes the persistent database volume. A named volume is not an off-host backup.

A container host must provide a writable persistent /app/data volume owned by UID 10001. An ephemeral filesystem loses campaigns, images and approval history on redeploy. SQLite requires one instance and persistent local storage; do not run multiple independent SQLite replicas or place the file on unsupported network storage. Do not imply PostgreSQL has been exercised merely because a driver exists.

## Hosting acceptance checklist — not yet completed

- Choose a Python/container host with Tesseract support, HTTPS and durable storage.
- Confirm actual service price, disk retention, sleep/cold-start policy, concurrency, memory and timeout limits before accepting a plan. No paid fallback is authorised.
- Configure ingress body/time/concurrency limits and session-creation abuse limits. Existing per-provider admission is not complete public abuse protection.
- Set BRANDPROOF_CORS_ORIGINS to the exact deployed frontend origin (JSON list); do not use wildcard credentials.
- Serve the frontend and /api under one public origin. Demo resume uses a host-only HttpOnly, SameSite=Strict cookie and credentialed fetch. Secure cookies default on; BRANDPROOF_DEMO_COOKIE_SECURE=false is only a local HTTP override. Verify that the reverse proxy preserves the cookie and that refresh restores the same workspace, without extending its 24-hour lifetime.
- Keep secrets server-side, never image build arguments, repository files, frontend bundles or logs.
- Deploy the image, verify HTTPS health plus a persisted campaign round trip, then restart/redeploy and read the same campaign and historical image bytes back.
- Run fresh-session, clean/flawed content, OCR, permission, approval/edit and outage checks against the remote API.
- Confirm retention/backup/deletion operations and availability throughout judging.

Public demo workspaces accept fictional material only. They are not private authenticated customer accounts. Production private membership, storage quotas, expiry cleanup and verified data-erasure tooling are not implemented. Do not claim confidential-workspace support or expose the un-hardened local server directly to the internet.

## External AI configuration

Default: off. Configure locally or in the host's secret manager:

    BRANDPROOF_AI_PROVIDER=groq
    BRANDPROOF_AI_MODEL=openai/gpt-oss-120b
    BRANDPROOF_AI_API_KEY=<secret, never commit>
    BRANDPROOF_EXTERNAL_AI_ENABLED=true

The request must also set external_ai_consent:true. Disclose that caption and selected approved reference text leave the server. User data is never sent just because a key exists. Sources/draft remain untrusted data; citations/spans are validated but semantic entailment is not guaranteed.

The account's actual model list, free tier, rate limits and data policy must be verified while signed in. The application does not create a provider account, obtain an unauthorised key or bypass quota. The local key and model list were verified, followed by a real persisted API probe. A small frozen six-case evaluation produced three completed development matches and three unassessed heldout cases (one rejected output, two provider failures). It is not a successful representative heldout benchmark. Do not substitute the assessed subset for the full denominator.

Persistent conservative admission defaults:

    BRANDPROOF_AI_WORKSPACE_HOURLY_LIMIT=6
    BRANDPROOF_AI_GLOBAL_HOURLY_LIMIT=24
    BRANDPROOF_AI_WORKSPACE_CONCURRENCY_LIMIT=1
    BRANDPROOF_AI_GLOBAL_CONCURRENCY_LIMIT=2

Hourly limits are rolling-hour reservation counts in the shared database. Failed attempts still count. Separate synthetic sessions cannot bypass the deployment-wide cap. A denied reservation produces a persisted unavailable contextual check; exact/OCR results remain available. No hidden retry or paid fallback exists. This is bounded synchronous admission, not a durable inference queue (a deliberate reduction from the original plan). Account/token quotas may be tighter; configure conservatively after measuring the real account. Do not rotate accounts to evade limits.

## Recovery and release

Before changing schema or recovering jobs, stop admission and all API workers; take a tested backup. An in-flight review can remain running after a process crash. The manual recovery CLI preserves inputs/findings and marks contextual coverage unavailable (process_interrupted), never approves it or fabricates completion. Run python -m brandproof.recovery --older-than-seconds 300 only after stopping every worker. The cutoff is bounded to 60–86400 seconds; age alone cannot identify a slow active worker. Do not run recovery over workers actively processing the same database.

create_all bootstraps new tables; it is not a migration framework and cannot safely alter existing columns. The current additions create new workflow/poster/admission tables. There is no established general migration/rollback guarantee, hosted release, secure deletion guarantee or off-host backup policy yet. Keep D01/D06 open until their real acceptance checks pass.

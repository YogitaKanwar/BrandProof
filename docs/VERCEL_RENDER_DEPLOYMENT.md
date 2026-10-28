# Vercel frontend and Render API

## Verified release proposal - 28 October 2026

Connections verified with read-only MCP calls: Render workspace BrandProof
(`tea-dbgt7ne1egvs73e4jvug`) and Vercel team yogitakanwar's projects
(`team_eSdP2YkhSfq2ycJJGlgRV38r`). Both report yogi2kanwar@gmail.com;
Vercel authenticated username is yogitakanwar. No existing Render web services,
PostgreSQL instances or Vercel projects were returned. Resource creation and
deployment are still awaiting explicit approval.

Proposed public resources, using only integration/round2-backend-pr1:

| Resource | Name | Plan | Region | Monthly base USD |
| --- | --- | --- | --- | --- |
| Render PostgreSQL 16, new empty database, 1 GB storage | brandproof-db | 0.1c-256mb (formerly basic-256mb), 100 connections | Singapore | 6.00 compute + 0.30 storage |
| Render Docker web service, one instance | brandproof-api | 0.5c-512mb (formerly Starter), 512 MB RAM | Singapore | 7.00 |
| Vercel static Vite project | brandproof | existing Hobby team, Node 24 | Global CDN; API stays in Singapore | 0.00 |

Proposed base total: USD 13.30/month, before taxes, usage above included limits,
or Groq charges. No paid workspace upgrade, domain purchase, extra disk, worker,
Redis, autoscaling or automatic plan upgrade is proposed. Keep the existing
workspace tier; if it requires a paid upgrade, stop for approval. Hobby Vercel
is appropriate here only for the noncommercial hackathon/personal demo.

If the user chooses a zero-cost temporary demo instead, explicitly use Free web
and Free PostgreSQL (1 GB): PostgreSQL expires after 30 days and is eventually
deleted; web sleeps after 15 minutes. This does not satisfy indefinite durable
hosting. A lower-cost durable option is Free web plus the paid database above,
USD 6.30/month base, with cold-start and proxy timeout acceptance still required.

Sources checked during preparation:
- https://render.com/pricing (current indexed compute prices)
- https://render.com/docs/compute-plans (current plan IDs and legacy mappings)
- https://render.com/articles/how-much-does-cloud-application-hosting-cost-for-small-businesses (1 GB storage choice, USD 0.30/GB, usage charges)
- https://render.com/docs/free (sleep and database expiry)
- https://vercel.com/docs/plans/hobby (free, noncommercial personal use)

Render creation parameters: repo https://github.com/YogitaKanwar/BrandProof,
branch integration/round2-backend-pr1, runtime docker, context ., Dockerfile
./Dockerfile, default CMD, autoDeploy no. Do not apply the old render.yaml as a
Blueprint: it proposes a different web plan and no database. The MCP creation
tool cannot set healthCheckPath; configure /api/v1/health in the Render dashboard
before acceptance. No general Render service-settings update tool is exposed.
If private-repository access is unavailable, follow Render's GitHub authorization
flow rather than changing repository visibility.

Vercel: root frontend, framework vite, install npm ci, build npm run build,
output dist, Node 24, public production URL, production Git branch explicitly
integration/round2-backend-pr1. Disable automatic preview deployments and external
rewrite caching. Commit frontend/vercel.json only after the assigned Render
hostname is returned; its exact contents are the rewrite template below with
only the destination hostname substituted. That follow-up commit requires push
authorization too. Do not guess either provider's assigned hostname.

Database internal URL and Groq key must be configured privately in Render. Never
reuse or upload the local .env. Initially provider none/external AI false; after
private key/model setup, configure groq and enable only approved consented tests
with the limits below. No fresh live Groq success is claimed by this release.

Release verification: 445 backend tests, Ruff lint/format, frontend build/lint,
47 unit tests, seven HTTP suites, 26 connected browser groups, and actual
Tesseract workflow smoke passed. External AI was disabled. Local QA uses an
isolated ignored SQLite database; no hosted PostgreSQL/HTTPS durability claim.
Docker CLI is unavailable on this session's PATH; earlier container/PostgreSQL CI
evidence is recorded separately in configured-backend-tests.md.

Fetch confirmed nine commits ahead / zero behind the integration remote at
627be7a2680a91d410f230ff8fea850cf84a5a34. Source checkpoint is
8e93438a854369c83e343250dd7d3e478e3e1c91, followed by a local release-documentation
and browser-test checkpoint. Review the exact final SHA before push. No backend
source changes were made in this preparation. Both protected historical
checkpoints remain ancestors. Credential scan: 198 tracked files and 323 unique
blobs across the nine unpublished commit trees; no credential matches found.
Local .env, virtual environments, databases and caches are ignored, excluded
from the Docker context, and must stay local.

Prepared 28 October 2026. Account connections are verified. Deployment is pending push/resource approvals, assigned hostnames and a privately configured durable PostgreSQL database. Use team-owned accounts. The existing FREE_HOSTING.md describes the alternative all-on-Render setup.

1. After explicit resource/public-deployment approval, deploy the existing Dockerfile from `integration/round2-backend-pr1`, containing tested commit `8e93438` or a subsequently verified checkpoint. The local integration branch is nine commits ahead of its remote as last checked: publish and verify the intended checkpoint before selecting it in either dashboard. Never substitute main or the old integration remote. Keep Free compute and external AI disabled initially. Enter the Render PostgreSQL internal URL privately in Render; never use ephemeral SQLite for the hosted service. Require `/api/v1/health` to return database/status ok. Do not infer the assigned URL from the service name.
2. In Vercel select this repository, the verified branch and root directory `frontend`. Use Vite, `npm ci`, build `npm run build`, output `dist`. Keep `VITE_API_BASE_URL=/api/v1`. Do not put provider keys or database credentials in Vercel's frontend environment.
3. Once the actual Render HTTPS origin is known, create `frontend/vercel.json` with the configuration below, substituting that verified origin. This is a template, not a deployable configuration with an assigned hostname:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://REPLACE_WITH_VERIFIED_RENDER_HOST/api/:path*"
    }
  ]
}
```

The app uses hash navigation, so no catch-all SPA rewrite is needed. The browser must call relative `/api` paths through Vercel, preserving one browser origin for the recovery cookie. Direct calls to a separate Render origin are not accepted as a tested substitute. Vercel supports external API rewrites: https://vercel.com/docs/routing/rewrites.

4. Set Render `BRANDPROOF_CORS_ORIGINS` to a JSON list containing the exact verified Vercel HTTPS origin. Keep `BRANDPROOF_DEMO_COOKIE_SECURE=true`. The backend accepts configured CORS origins for session provenance; arbitrary preview origins must not be whitelisted. Keep `RENDER_EXTERNAL_URL` platform-managed. Never trust arbitrary forwarded origin headers.
5. Deploy the frontend and test from its actual HTTPS URL: session creation/resume after reload, same campaign and sources, caption contradiction, PNG/JPEG OCR and aligned boxes, owner-confirmed logo, private historical images, creator/reviewer permissions, manual notes, explicit corrections, receipts and stale approvals. Verify the proxy preserves Set-Cookie and subsequent Cookie headers; inspect no-store responses and ensure private content is not cached. Test a poster near the 5 MiB API limit and review latency through the proxy.
6. Redeploy/restart Render and verify the same campaign, review and original image remain available through Vercel. Verify again after a free-service sleep. Render Free loses local files and sleeps when idle: https://render.com/docs/free. Record actual results in configured-backend-tests.md. Public HTTPS, PostgreSQL durability and proxy behavior cannot be certified from local SQLite tests.

No paid resources, main merge, provider call or use of another person's account is implied. Account ownership and database configuration must be established before resource creation. The existing hosting package serves a duplicate UI on Render; retaining it requires no backend change and does not prevent using Vercel as the frontend entrypoint.

## Dashboard configuration and approval gates

Use Render PostgreSQL in the same workspace and region as the API. Approve database creation separately before applying it; confirm plan and retention in the dashboard. The existing render.yaml defines only the web service, not PostgreSQL. The current Free Render PostgreSQL offer expires after 30 days; do not upgrade silently. Use a new database: startup calls SQLAlchemy create_all to create tables. There is no migration command/framework or automatic SQLite data migration. Starting against an existing production database requires explicit approval and a backup/schema review.

Posters and logos are LargeBinary database records. PostgreSQL must persist these alongside campaigns and review history; no extra disk is needed for current uploads. Prove persistence by fetching the same historical image and campaign after a redeploy.

Render build: Docker runtime, repository root context, ./Dockerfile. Do not supply a native Python build command. Docker installs locked dependencies, Tesseract English and Noto fonts. Start command is the Dockerfile default, `python -m brandproof.serve`, binding 0.0.0.0 to Render's PORT with one worker. Health path: /api/v1/health. Keep automatic deploys off until reviewed configuration is approved.

| Dashboard | Variable | Configuration |
| --- | --- | --- |
| Render | BRANDPROOF_DATABASE_URL | Secret: use the Render PostgreSQL internal connection URL privately |
| Render | BRANDPROOF_FRONTEND_DIST | /app/frontend-dist (existing image also serves UI) |
| Render | BRANDPROOF_DEMO_COOKIE_SECURE | true |
| Render | BRANDPROOF_CORS_ORIGINS | JSON list of the exact verified Vercel HTTPS origin |
| Render | OMP_NUM_THREADS | 1 |
| Render | BRANDPROOF_AI_PROVIDER | groq after private provider configuration; none initially |
| Render | BRANDPROOF_AI_MODEL | Account-supported model selected and verified before live acceptance |
| Render | BRANDPROOF_AI_API_KEY | Secret: enter only in Render's private environment editor |
| Render | BRANDPROOF_EXTERNAL_AI_ENABLED | false initially; true only for approved consented testing |
| Render | BRANDPROOF_AI_WORKSPACE_HOURLY_LIMIT | 6 |
| Render | BRANDPROOF_AI_GLOBAL_HOURLY_LIMIT | 24 |
| Render | BRANDPROOF_AI_WORKSPACE_CONCURRENCY_LIMIT | 1 |
| Render | BRANDPROOF_AI_GLOBAL_CONCURRENCY_LIMIT | 2 |
| Vercel | VITE_API_BASE_URL | /api/v1; real Render hostname belongs in the API rewrite |

Render supplies PORT and RENDER_EXTERNAL_URL. No custom-domain public-origin override is needed for its assigned hostname. Provider key/model validity must be checked without logging secrets, and each live AI review needs explicit consent. Vercel requires no database/provider secrets. BRANDPROOF_API_TARGET is a local Vite proxy setting, not a production routing configuration.

Before applying cloud changes, present verified Vercel team, Render workspace, region, resource names/plans, exact commit and database initialization/public-deployment scope to the user for approval. Connection authorization alone is not resource or production approval.

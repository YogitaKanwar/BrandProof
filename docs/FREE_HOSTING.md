# Free hosting setup - BrandProof

Prepared 28 October 2026. No cloud resources or public URL have been created. The connected Vercel account is not the user's account and must not be used.

## Chosen route

One Render **Free web service** builds the repository Dockerfile. FastAPI serves the compiled React app at `/` and the API at `/api/v1`. This keeps the recovery cookie on the same HTTPS origin. Tesseract runs in the container; no external OCR subscription is needed.

A separate **Neon Free PostgreSQL** database stores campaigns, source versions, review snapshots, image/logo bytes and human decisions. Do not use SQLite on Render Free: its filesystem is erased on restart, redeploy and idle shutdown. No disk purchase, domain purchase or paid AI plan is required by this setup. Provider AI defaults off; exact checks, local OCR and human review still work, while missing contextual coverage stays visibly incomplete.

Official limits checked on 28 October 2026:

- [Render Free](https://render.com/docs/free): sleeps after 15 idle minutes; waking takes about one minute. Free instance hours, bandwidth/build limits and resource limits apply. Services can be suspended when limits are reached. Leave payment details unset if you want suspension rather than supplementary billing.
- [Neon Free](https://neon.com/pricing): $0, no time limit/card requirement, currently 1 GB/project and 100 CU-hours/project/month. Image storage consumes that allowance. Do not upgrade to Launch or Scale.
- Render's own free Postgres expires after 30 days; Neon is the selected database to avoid that expiry. Neither service is an availability guarantee for judging.

## Account setup and deployment

1. Create your own free accounts at [Neon](https://console.neon.tech/) and [Render](https://dashboard.render.com/). Use accounts controlled by the team. Do not send passwords, keys or database connection strings in chat.
2. In Neon, create a Free project/database, preferably near the Render region. Copy the pooled PostgreSQL connection URL from **Connect**, keeping `sslmode=require` and any generated TLS parameters. Use a fresh database; the app creates initial tables, not migrations for arbitrary older schemas.
3. In Render, connect GitHub and grant this repository access. The repo is currently **private**; its owner may need to grant Render access. Select **New > Blueprint**, the BrandProof repository, and branch `fix/demo-session-resume` (or the branch containing these files after review). Use the root `render.yaml`.
4. Enter the Neon URL privately for `BRANDPROOF_DATABASE_URL`. Plain `postgresql://` and `postgres://` automatically use the installed psycopg 3 driver. Do not paste SQL commands or quotes around the URL.
5. Confirm the service's instance type is **Free**, there are no paid resources/disks, and AI is disabled. Create the Blueprint. Automatic deploys are off; use **Manual Deploy > Deploy latest commit** for later updates. The Dockerfile reads Render's `PORT`.
6. Wait for a successful build, healthy service and an assigned HTTPS `onrender.com` address. Never invent the URL from the service name. Open `/api/v1/health`; require `status: ok` and `database: ok`. Open `/`; require the app, not just the health endpoint.

If Blueprint access is unavailable, create a Free **Web Service**, select the same repository/branch, choose **Docker**, root `Dockerfile`, health check `/api/v1/health`, and copy the environment names/values from `render.yaml`. Enter the database URL only in Render's secret environment editor. Keep `BRANDPROOF_DEMO_COOKIE_SECURE=true` on HTTPS. No separate Vercel deployment is needed.

Render's [default environment](https://render.com/docs/environment-variables) supplies `RENDER_EXTERNAL_URL`. The app accepts that exact public origin even when TLS ends before the container. For a custom domain or another host, set `BRANDPROOF_PUBLIC_ORIGIN` to the exact verified HTTPS origin. Wildcards, credentials, query strings and paths are rejected; arbitrary forwarded headers do not establish an authorised origin.

## Required acceptance before calling it deployed

Use fictional data only. This is a public demo with selectable simulated roles, not customer authentication.

1. In a private browser window, open the HTTPS app without signing in. Start the editable workshop example, inspect its approved fictional rules and run review. Expect four explained caption issues with source/version evidence. Make a correction explicitly; run review again.
2. Upload a legible PNG/JPEG with `INR 599` and compare with an owner-confirmed `INR 499` main-price source. Verify real OCR text/boxes, a private image request and an explained issue. Low-confidence OCR must stay partial.
3. Confirm a reference logo and test it against a poster. Similarity is a candidate for manual checking, not certified logo compliance. Check unavailable/ambiguous output remains visible.
4. Exercise creator request, reviewer notes for incomplete checks, reviewer decision and a receipt. Change content afterwards; the old approval must become stale. A demo role switch is not independent human identity.
5. Reload the exact review URL; it must restore the same workspace/campaign. Record a campaign/review ID, manually redeploy the service, then verify that campaign, findings and original image still load in the same browser. Check once after the service has slept. Do not claim persistence from a health check alone.
6. Open the final project, source repository and PDF links in a private window. The **source repository is currently private**, so the team owner must explicitly make the submission source public or provide an organiser-approved public source copy. A collaborator-only GitHub link does not meet the email's public-access requirement.

The complete Docker image and PostgreSQL workflow **passed** in [GitHub Actions run 40670242539](https://github.com/YogitaKanwar/BrandProof/actions/runs/40670242539) on commit `da1c810`. The run built the UI/runtime, connected to PostgreSQL 16 and passed real caption/parser/OCR/human-workflow scripts: four flawed-caption findings, ten parser cases, completed OCR, a poster contradiction, explicit correction, persisted records, manual-supplement approval and stale approval after poster replacement. The run is CI evidence, not a public deployment. Local Docker daemon access remains denied; real hosted HTTPS/sleep/redeploy acceptance stays pending.

## Optional contextual AI later

In Render's private environment editor, configure provider/model/key and enable `BRANDPROOF_EXTERNAL_AI_ENABLED` only for an authorised provider account with a confirmed budget. Keep per-review consent in the UI and conservative global/workspace caps. No local `.env` file or credentials are copied into the image. A free web host does not imply free provider inference. No key is necessary to deploy and exercise the deterministic/OCR/human core.

## Limits and recovery

This setup is a hackathon demo, not a production service. Public session creation, storage/retention cleanup, ingress limits, stronger identity and migrations remain work. Use fictional data and inspect storage/usage during judging. Free service cold starts can delay judges; disclose them. Do not add automatic pings to evade a provider's idle policy.

Neon preserves data outside the app container; keep a tested database backup before schema changes. Existing SQLite campaigns are not automatically migrated. New hostnames do not inherit a browser's local recovery cookie. The demo cookie expires after 24 hours, and successful resume does not extend it. Record hosted acceptance separately in `docs/configured-backend-tests.md`.

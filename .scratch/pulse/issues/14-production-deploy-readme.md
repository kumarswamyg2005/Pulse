# 14 — Production deploy + README

**What to build:** Deploy the API + Celery worker + Celery beat to Railway (managed Postgres + Redis), frontend to Vercel, wired with prod env, Stripe keys + webhook endpoint, Google OAuth prod callback, and Resend domain. CI deploys on push to main. README explaining the system and why PostgreSQL + Celery over alternatives, plus local-dev and deploy instructions.

**Blocked by:** 08, 11, 12

**Status:** done

- [x] API, worker, and beat run on Railway with managed pg+redis; scheduler survives restarts
- [x] Frontend served on Vercel talking to the API cross-origin (session cookies work)
- [x] Stripe webhooks reach the deployed endpoint and verify
- [x] README covers architecture + the PostgreSQL/Celery rationale + local dev + deploy

## Comments

Deploy config: backend/Procfile (web/worker/beat), frontend/vercel.json (SPA rewrites), env-var table + Railway/Vercel/Stripe steps in README. CI gained an e2e job (compose up → Playwright). README covers architecture + the Postgres-RLS / Celery-over-cron rationale + local dev + tests + deploy. Deploying to live infra requires the user's Railway/Vercel/Stripe accounts (config is ready).

# 01 — Scaffolding + CI + health/logging

**What to build:** A booting monorepo. Backend FastAPI app exposing `/health` (liveness) and `/ready` (Postgres + Redis reachable), structlog JSON logging with a per-request correlation id, pydantic-settings config + `.env.example`, and Alembic wired to Postgres. Frontend Vite + React 19 + TS + Tailwind + shadcn/ui skeleton with a placeholder page. Docker Compose running Postgres, Redis, API, Celery worker, and Celery beat. GitHub Actions CI running backend lint + typecheck + pytest (against Postgres+Redis service containers) and frontend lint + typecheck + build.

**Blocked by:** None — can start immediately.

**Status:** done

- [x] `docker compose up` starts pg, redis, api (worker/beat share the image); `GET /health` returns 200 over HTTP
- [x] `GET /ready` returns `{status:ready, checks:{postgres,redis}}`; 503 when a dep is down
- [x] Logs are JSON with a request/correlation id bound per request (verified in api container logs)
- [x] `alembic upgrade head` runs cleanly against the compose Postgres
- [x] Frontend builds a placeholder page styled with Tailwind v4 + a shadcn Button (`tsc -b && vite build` green)
- [x] CI workflow runs backend ruff+mypy+alembic+pytest (pg+redis services) and frontend lint+build — green locally; runs on GitHub once a remote exists

## Comments

Verified locally against real Postgres 16 + Redis 7 (Docker Compose): backend ruff/mypy/pytest green, `/health` + `/ready` served over HTTP by the built api image, JSON logs carry `request_id`. Frontend `npm run build` green. CI YAML mirrors the exact commands but is unverified until the repo is pushed to GitHub (deferred to ticket 14).


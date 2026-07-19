# 06 — Scheduler + HTTP check execution + results + uptime

**What to build:** DB-driven dispatcher — a Celery Beat tick (~10s) selecting due monitors (`next_check_at <= now()`, not paused) with `SELECT ... FOR UPDATE SKIP LOCKED`, enqueuing one check task per monitor, and writing back `next_check_at = now() + interval ± 15% jitter` (randomized phase at create). HTTP check function (httpx: status-in-set within timeout, optional keyword match, TLS cert-expiry warning). `check_results` table indexed on `(monitor_id, checked_at)`. Monitor current status + uptime % computed on demand and shown on the detail page.

**Blocked by:** 05

**Status:** ready-for-agent

- [ ] Due monitors are dispatched and checked automatically on their interval
- [ ] `next_check_at` advances with jitter; concurrent beats don't double-dispatch (SKIP LOCKED)
- [ ] HTTP check records up/down, latency, status; keyword + cert-expiry evaluated
- [ ] Scheduler resumes correctly after a restart (state lives in Postgres)
- [ ] Monitor detail shows current status, recent results, and uptime %

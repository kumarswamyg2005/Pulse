# Pulse

Multi-tenant uptime-monitoring SaaS. Teams add HTTP/TCP/ping monitors, background workers
check them on a schedule, incidents open/close automatically, users get alerts, and each team
gets a public status page. Free/Pro/Team tiers gated by Stripe.

**Stack:** React 19 + Vite + TS + Tailwind + shadcn/ui (frontend, Vercel) ·
FastAPI + PostgreSQL + Celery + Redis (backend, Railway) · Stripe · Resend · GitHub Actions CI.

Architecture decisions and the full requirement set: `.scratch/pulse/spec.md`.
Domain vocabulary: `CONTEXT.md`. Architecture decision records: `docs/adr/`.

## Working style

Ponytail mode (`full`) is active — climb the YAGNI ladder (stdlib → native → installed dep →
one line → minimum custom code) and stop at the first rung that holds. Mark deliberate
shortcuts with `ponytail:` comments naming the ceiling and upgrade path.

Build test-first, issue-by-issue, via the `/tdd` skill. Postgres RLS is used for tenant
isolation, so tests run against real Postgres + Redis — never SQLite.

## Agent skills

### Issue tracker

Local markdown under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root.

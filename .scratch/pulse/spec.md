# Spec: Pulse — Multi-Tenant Uptime Monitoring SaaS

Status: ready-for-agent

## Problem Statement

Teams that run internet-facing services need to know the moment something goes down — before
their customers tell them. They want to point a tool at their URLs, ports, and hosts; have it
checked continuously from the outside; be alerted automatically when checks fail; and give
their own users a public page that shows current health. They also want this to cost nothing
to try and to scale in price as their needs grow. Building and operating this in-house is a
distraction from their actual product.

## Solution

Pulse is a hosted, multi-tenant uptime monitor. A **Team** signs up (email/password or
Google), adds **Monitors** (HTTP, TCP, or ping), and Pulse checks each on its own schedule
from background workers. When a monitor fails repeatedly an **Incident** opens automatically
and the team's owners and admins are alerted by email and via configured **Webhooks**; when
it recovers the incident resolves itself. Each team gets a public **Status Page** at
`/status/<team-slug>` showing the monitors it chooses to expose. Usage is gated by a
Stripe-backed **Plan** (Free/Pro/Team) covering monitor count, check frequency, seats, webhook
access, retention, and status-page count. **RBAC** (owner/admin/member) governs who can do
what; **Postgres RLS** guarantees one team can never see another's data.

## User Stories

### Authentication & account

1. As a visitor, I want to sign up with email and password, so that I can start using Pulse.
2. As a visitor, I want to sign up / log in with Google, so that I don't need a separate password.
3. As a user, I want my session kept in a secure httpOnly cookie, so that I stay logged in safely across the SPA.
4. As a user, I want to log out, so that my session is revoked server-side.
5. As a user, I want to reset a forgotten password via an emailed token, so that I can regain access.
6. As a new user, I want a personal Team created automatically at signup with me as owner, so that I can add monitors immediately.

### Teams, membership & RBAC

7. As an owner, I want to create additional Teams, so that I can separate work by client or project.
8. As an owner/admin, I want to invite people by email with a chosen Role, so that my teammates can join.
9. As an invitee, I want a tokenized, expiring invite link that works whether or not I already have an account, so that joining is frictionless.
10. As an owner/admin, I want to change a member's role or remove them, so that access stays correct.
11. As an owner, I want to transfer ownership or delete the team, so that I control the tenant's lifecycle.
12. As a member, I want read-only access plus the ability to acknowledge incidents, so that I can help triage without changing config.
13. As any user, I want to switch the "current Team" I'm acting in, so that I can work across the teams I belong to.
14. As any user, I want to never see another team's data, so that tenant isolation holds even if application code has a bug (enforced by RLS).

### Monitors

15. As an admin, I want to create an HTTP monitor with a URL, expected status set, timeout, interval, and optional keyword assertion, so that I'm alerted when the endpoint misbehaves.
16. As an admin, I want to create a TCP monitor (host + port), so that I can watch non-HTTP services.
17. As an admin, I want to create a ping monitor (host), so that I can watch basic reachability.
18. As an admin, I want HTTPS monitors to warn me before the TLS certificate expires, so that I renew in time.
19. As an admin, I want to edit, pause, resume, and delete monitors, so that I manage what's watched.
20. As an admin, I want to mark a monitor public, so that it appears on the status page (default off).
21. As a member, I want to view all monitors and their current status, so that I know system health.
22. As a user, I want to see a monitor's recent check history and uptime %, so that I can judge reliability.

### Scheduling & checks

23. As a team, I want each monitor checked on its own interval, so that critical services are watched more often.
24. As an operator, I want checks spread with jitter, so that they don't all fire at once and hammer targets or workers.
25. As an operator, I want the scheduler to survive restarts, so that monitoring continues after a deploy or crash (state lives in Postgres).
26. As an operator, I want a monitor's interval clamped to the team's plan minimum, so that frequency respects billing.

### Incidents

27. As a team, I want an incident to open only after N consecutive failures, so that transient blips don't page anyone.
28. As a team, I want an incident to auto-resolve after M consecutive successes, so that recovery is recorded without manual action.
29. As a member, I want to acknowledge an open incident, so that teammates know it's being handled.
30. As a user, I want a timeline of past incidents per monitor, so that I can review history.

### Alerts

31. As an owner/admin, I want an email when an incident opens and when it resolves, so that I react quickly.
32. As an admin, I want to configure webhook URLs that receive a JSON POST on incident events, so that I can integrate Slack/PagerDuty/etc.
33. As an admin (Pro+), I want webhooks gated by plan, so that the feature reflects the tier.

### Billing (Stripe)

34. As an owner, I want to upgrade via Stripe Checkout, so that I unlock higher limits.
35. As an owner, I want to manage payment method, invoices, and cancellation via the Stripe Customer Portal, so that I control billing myself.
36. As the system, I want subscription state driven by verified Stripe webhooks, so that our records match Stripe even across failures.
37. As an admin, I want a clear error when I hit a plan limit (e.g. monitor count, seats), so that I know to upgrade.
38. As an owner, I want that when I downgrade below current usage, excess monitors are paused (not deleted), so that I lose no data.
39. As an owner, I want to see my current plan, usage against limits, and renewal date, so that I understand my account.

### Public status page

40. As a visitor, I want to view a team's public status page without logging in, so that I can check service health.
41. As a visitor, I want the status page to show each public monitor's current status and uptime %, so that I trust the service.
42. As a visitor, I want open and recent incidents shown on the status page, so that I understand ongoing issues.

### Platform & operations

43. As an operator, I want structured JSON logs with request/correlation IDs across API and workers, so that I can trace a request end-to-end.
44. As an operator, I want errors reported to Sentry, so that I catch failures in production.
45. As an operator, I want `/health` and `/ready` endpoints, so that the platform can health-check the service.
46. As an operator, I want API rate limits (strict on auth, moderate on API, cached public page), so that the service resists abuse.
47. As a developer, I want a seed script producing a demo team, one user per role, sample monitors (incl. one down with an open incident), and a Stripe test subscription, so that I can develop and demo quickly.
48. As a developer, I want Docker Compose for local dev (Postgres, Redis, API, worker, beat), so that I can run the whole system locally.
49. As a maintainer, I want CI (GitHub Actions) running lint, typecheck, and tests against real Postgres+Redis, so that regressions are caught before merge.

## Implementation Decisions

**Tenancy & isolation**
- Shared-schema multi-tenancy. Every tenant-owned table has a `team_id`. Postgres **Row-Level Security** policies scope all reads/writes to the current team; the app sets the current team per request/task via a session GUC (e.g. `SET LOCAL app.current_team_id`). RLS is defense-in-depth on top of query-level scoping.
- The DB connection runs as a non-superuser role so RLS is enforced (superusers/`BYPASSRLS` skip policies).

**Auth & sessions**
- Authlib for Google OAuth; passlib/bcrypt for password hashing.
- Sessions are opaque tokens stored in Redis, delivered in an httpOnly + Secure + SameSite=None cookie; CORS configured with credentials for the Vercel↔Railway cross-origin setup. Server-side revocable.
- Password reset and email verification via signed, expiring tokens sent through the email sender.

**Membership & RBAC**
- `users`, `teams`, `memberships(user_id, team_id, role)`. A user's "current team" is resolved per request (from a header/path or a stored preference).
- Authorization enforced by a dependency that resolves the caller's role in the current team and checks a permission. Roles: owner ⊃ admin ⊃ member capability sets.
- Invites are rows with a hashed token, role, email, and expiry; accepting creates/links a user and a membership.

**Monitors, scheduler & checks**
- `monitors` hold type, target config, `interval_seconds`, `timeout_seconds`, expected-status set, optional keyword, `public` flag, `paused`, and `next_check_at`.
- Scheduler: a Celery Beat periodic task ("dispatch due checks", ~10s) selects `monitors WHERE next_check_at <= now() AND NOT paused`, enqueues one check task per monitor, and updates `next_check_at = now() + interval ± 15% jitter` (with randomized initial phase at create time). Postgres is the schedule of record → restart-safe. Use `SELECT ... FOR UPDATE SKIP LOCKED` to make dispatch safe under multiple beat/worker instances.
- Check execution: HTTP via httpx (assert status in expected set within timeout; optional body-keyword; TLS cert-expiry check for HTTPS). TCP via socket connect within timeout. Ping via ICMP echo (with a subprocess/`ping` fallback where raw sockets aren't permitted). Each check writes a `check_results` row.
- Interval is clamped to the team's plan minimum at write time and at dispatch.

**Incidents & alerts**
- Incident state machine per monitor: after 3 consecutive failed results with no open incident → open an `incidents` row; after 2 consecutive successes while an incident is open → set resolved. `degraded` is out of scope.
- On open/resolve, emit alerts: email to owners+admins via the email sender, and POST a JSON payload to each configured webhook. SSL-expiry produces a warning-level alert, not a down incident.
- Webhook delivery is a Celery task with limited retries.

**Billing**
- Three Stripe Products/Prices (Free is $0/no Stripe subscription needed; Pro, Team are paid). Flat per-tier — subscription item quantity 1; seats are an in-app limit only.
- Hosted Checkout to subscribe/upgrade; hosted Customer Portal for payment method, invoices, cancel, plan change.
- Webhook endpoint verifies the Stripe signature, dedupes by event id, and handles `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`. It persists `stripe_customer_id`, `stripe_subscription_id`, `tier`, `status`, `current_period_end` on the team. On downgrade recompute limits and pause excess monitors (keep data).
- Plan limits live in one config/table (monitor count, min interval, seats, webhook allowed, retention days, status-page count) and are the single source enforcement reads.

**Status page**
- Public unauthenticated route `/status/<team-slug>`. Shows monitors where `public = true`: current status, uptime % over a window, open + recent incidents. Response cached briefly (Redis) and rate-limited per IP.

**Storage & retention**
- `check_results` indexed on `(monitor_id, checked_at)`. Uptime % and latency computed on demand from raw rows. A daily Celery task prunes rows older than the team's retention. Precomputed rollups are deferred until the status/history query is measurably slow.

**Observability & platform**
- structlog emitting JSON, with a request/correlation id bound per API request and per Celery task; Sentry SDK for errors; `/health` (liveness) and `/ready` (DB+Redis reachable).
- Rate limiting via slowapi over Redis: strict on auth endpoints, moderate per-user on API, per-IP on the public status page.
- Alembic migrations; pydantic-settings + `.env.example`; UTC everywhere; Docker Compose (pg/redis/api/worker/beat) for local dev.

**Frontend**
- React 19 + Vite + TS + Tailwind + shadcn/ui. Server state via TanStack Query (also drives dashboard polling ~15–30s); routing via React Router; auth + current-team in a Context provider. No global store until cross-tree state demands it.

**Repo & deploy**
- Monorepo: `/frontend`, `/backend`, `/docs`. Frontend → Vercel; backend API + Celery worker + Celery beat → Railway (with managed Postgres + Redis). CI via GitHub Actions with path filters.

## Testing Decisions

**What makes a good test:** exercise external behavior through the highest seam, not implementation details. Assert on API responses, DB state visible through the API, emitted emails/webhooks (captured via a test sender/collector), and status transitions — not private functions.

**Primary seam — the FastAPI app boundary.** Drive the running app in-process (httpx/TestClient) against **real Postgres + Redis** (CI service containers; RLS and `SKIP LOCKED` cannot be exercised on SQLite). This one seam covers auth, RBAC, monitor CRUD, incidents surfaced via API, billing endpoints, the Stripe webhook endpoint, and the public status page.

**Secondary seams (kept minimal):**
- **Check + incident pipeline** — invoke the check task and dispatch task directly (Celery eager mode) so a scripted sequence of up/down check outcomes drives incident open/resolve and alert emission, asserted through the API and the captured alert sender. Network to real targets is stubbed at the check function's HTTP/socket boundary.
- **Stripe webhooks** — POST signed test events to the webhook endpoint (signature built with the test signing secret; no live Stripe calls) and assert the team's tier/limits/paused-monitors update; assert idempotency on duplicate event ids.

**Required integration coverage (non-negotiable):** billing flow (checkout → webhook → tier applied → limit enforced → downgrade pauses excess) and incident flow (consecutive failures open an incident + alert; consecutive successes resolve it).

**Frontend:** Vitest + React Testing Library for components/hooks; one Playwright happy-path smoke (log in → add monitor → see it on dashboard).

**Prior art:** none yet (greenfield) — the first vertical slice establishes the API-seam test harness (real pg/redis fixtures, auth helper, captured email/webhook sender) that later slices reuse.

## Out of Scope (v1)

- `degraded` monitor state and latency-SLO alerting.
- Multi-region checking (single region only).
- Custom domains / subdomain-per-team status pages (path-based only).
- Per-seat billing and proration; per-user notification preferences; on-call schedules/escalation.
- Precomputed rollup tables and TimescaleDB.
- Additional OAuth providers beyond Google; SSO/SAML.
- Websocket live updates (polling instead).
- Additional alert channels beyond email + webhook (Slack app, SMS, etc.).

## Further Notes

- Ponytail (`full`) governs implementation: climb the YAGNI ladder, prefer stdlib/native/installed deps, mark deliberate shortcuts with `ponytail:` comments naming the ceiling.
- Build order (see `issues/`): HTTP monitor is the tracer bullet; TCP and ping follow as thin additions once the check→incident→alert pipeline exists.
- Any new dependency beyond the fixed stack must be flagged before adding.

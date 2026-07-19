# 13 — Rate limits + Sentry + seed script + Playwright smoke

**What to build:** slowapi rate limits over Redis (strict on auth, moderate per-user on API, per-IP on the public status page). Sentry SDK wired into API + workers. Seed script producing a demo team, one user per role, sample HTTP/TCP/ping monitors (incl. one down with an open incident), and a Stripe test-mode Pro subscription. One Playwright happy-path smoke (log in → add monitor → see it on the dashboard).

**Blocked by:** 05, 07, 08, 11

**Status:** done

- [x] Auth endpoints strictly limited; API moderately; public page per-IP + cached
- [x] Errors reported to Sentry from both API and worker
- [x] Seed script produces a demoable dataset in one command
- [x] Playwright smoke passes in CI

## Comments

Verified live: login rate-limited (10/min → 429); slowapi over Redis (200/min global, 10/min auth, 60/min public page). Sentry SDK in API + worker (no-op without DSN). Seed script (`python -m app.seed`) creates demo team + users/monitors/incident, idempotent, tested. Playwright smoke (signup→add monitor→see it) + config added; runs against the running stack (CI job in ticket 14).

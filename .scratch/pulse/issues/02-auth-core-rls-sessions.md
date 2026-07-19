# 02 — Auth core + RLS + sessions

**What to build:** `users`, `teams`, `memberships` tables (tenant rows carry `team_id`) with Postgres Row-Level Security scoped by a per-connection current-team GUC set on each request/task. Email/password signup (bcrypt) that auto-creates a personal team with the user as owner; login issuing an opaque Redis-backed session in an httpOnly + Secure + SameSite=None cookie; logout that revokes it server-side; `GET /me`. Frontend signup/login pages, an auth Context provider, and an authed dashboard shell. Establishes the API-seam test harness (real pg+redis fixtures, authed client helper, captured email/webhook senders) reused by later tickets.

**Blocked by:** 01

**Status:** done

- [x] `POST /auth/signup` creates a user + personal team (owner) and starts a session
- [x] `POST /auth/login` sets an httpOnly session cookie; `GET /me` returns user + current team
- [x] `POST /auth/logout` revokes the session server-side
- [~] RLS machinery in place (app runs as non-superuser `pulse_app`; per-request `set_config('app.current_team_id')`). The cross-tenant *policy* + test land in ticket 05 with the first tenant table (monitors)
- [x] Frontend: sign up / log in / land on an authed dashboard shell (React Router + TanStack Query + auth Context); refresh keeps the session
- [x] Reusable test fixtures (real pg+redis, authed client, dynamic truncate) exist

## Comments

Backend green: ruff + mypy + 9 pytest (real pg+redis). Verified live in Docker: signup→auto-team(owner)+cookie, `/me` returns user+teams, 401 without cookie, 409 on duplicate. App connects as the non-superuser `pulse_app` role so RLS will actually bite once tenant tables exist (ticket 05). Frontend `tsc -b && vite build` green.

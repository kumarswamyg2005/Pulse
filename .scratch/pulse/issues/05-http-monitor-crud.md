# 05 — HTTP monitor CRUD + dashboard

**What to build:** `monitors` table (carries `team_id`, RLS) with `type=http`, url, expected-status set, timeout, interval, optional keyword assertion, `public` flag (default off), `paused`, `next_check_at`. Create/edit/pause/resume/delete gated to admin+. Interval clamped to the team's plan minimum at write. Dashboard list + monitor detail page (no checking yet).

**Blocked by:** 04

**Status:** done

- [x] Admin can create/edit/pause/resume/delete an HTTP monitor; member gets 403 (read-only)
- [x] Interval clamped to the team's plan minimum on write (verified live: 30→300 on free)
- [x] `public` flag defaults off
- [x] Dashboard lists monitors; detail page shows config + pause/delete
- [x] All monitor rows are team-scoped by **Postgres RLS** — cross-tenant test proves team B sees none of A's monitors and 404s by id

## Comments

Backend green: ruff + mypy + 29 pytest incl. the headline cross-tenant RLS test. First real tenant table (`monitors`) with `ENABLE/FORCE ROW LEVEL SECURITY` + a `current_setting('app.current_team_id')` policy; app runs as non-superuser `pulse_app`. Added `app/plans.py` (Preset A limits) + `teams.tier`. Frontend: create form + list + detail (pause/delete), all role-gated.

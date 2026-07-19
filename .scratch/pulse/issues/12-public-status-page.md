# 12 — Public status page + caching

**What to build:** Public unauthenticated route `/status/<team-slug>` rendering monitors where `public = true`: current status, uptime % over a window, and open + recent incidents. Response cached briefly in Redis and rate-limited per IP. Public-facing page (public SPA route or server-rendered).

**Blocked by:** 07

**Status:** done

- [x] `/status/<slug>` loads without auth and shows only public monitors
- [x] Current status, uptime %, and open/recent incidents render
- [x] Response is cached (short TTL) and per-IP rate-limited
- [x] Non-public monitors never appear on the page

## Comments

Backend green: 3 pytest (only-public, 404, 30s cache). Public `/status/<slug>` sets RLS GUC to the team explicitly (no session). Verified live: unauth GET shows only public monitors, hides private. Per-IP rate limit added in ticket 13. Frontend: public StatusPage route + per-monitor public toggle.

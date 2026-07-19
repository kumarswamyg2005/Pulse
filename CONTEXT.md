# Pulse — Domain Glossary (Ubiquitous Language)

Use these terms consistently across code, specs, tickets, and UI.

- **Team** — the tenant. The unit of isolation, billing, and RBAC. Every domain row carries a `team_id`; Postgres RLS scopes reads/writes to the current team.
- **User** — a person with credentials (email/password or Google). A user belongs to many teams.
- **Membership** — the join between a user and a team, carrying a **Role**.
- **Role** — `owner` (billing, delete team, everything), `admin` (manage monitors, members, incidents, status page — no billing), `member` (read-only + acknowledge incidents).
- **Invite** — a tokenized, expiring email link that adds its accepter to a team with a pre-assigned role.
- **Monitor** — a target the system checks on a schedule. Type is `http`, `tcp`, or `ping`. Holds interval, timeout, expected-status set, optional keyword assertion, and a `public` opt-in flag for the status page.
- **Check** — a single execution of a monitor. Produces a **Check Result**.
- **Check Result** — the raw outcome of one check: up/down, latency, status code, error. High-volume; pruned by tier retention.
- **Scheduler** — the DB-driven dispatcher: a Celery Beat tick selects monitors due (`next_check_at ≤ now`), enqueues per-monitor check tasks, and writes back `next_check_at` with jitter.
- **Jitter** — randomized phase + ±15% spread applied to `next_check_at` so checks don't fire in a synchronized thundering herd.
- **Incident** — an open period of downtime for a monitor. Opens after N consecutive failed checks (default 3), auto-resolves after M consecutive successes (default 2).
- **Acknowledge** — a member/admin marking an open incident as seen (does not resolve it).
- **Alert** — a notification emitted on incident open/resolve: email to owners+admins, plus any configured webhooks.
- **Webhook** — a team/monitor-configured URL that receives a JSON POST on alert.
- **Status Page** — a public, unauthenticated page at `/status/<team-slug>` showing opted-in monitors' current status, uptime %, and incidents.
- **Plan / Tier** — `free`, `pro`, `team`. Gates monitor count, min check interval, seats, webhook access, retention, and status-page count.
- **Subscription** — the Stripe-backed billing state for a team. Stripe webhooks are the source of truth for tier + status.
- **Seat** — a membership slot counted against the plan's seat limit.
- **Retention** — the tier-defined window after which raw Check Results are pruned.

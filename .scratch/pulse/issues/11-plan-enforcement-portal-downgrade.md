# 11 — Plan-limit enforcement + Customer Portal + downgrade-pause

**What to build:** Enforce plan limits on writes — monitor count, seats (invites), min-interval clamp, webhook-allowed, status-page count — with clear over-limit errors. Customer Portal session for self-serve billing. On downgrade below usage, pause excess monitors (keep data), driven from the `subscription.updated` webhook recomputing limits. Usage-vs-limits UI on the billing page.

**Blocked by:** 10, 05, 04

**Status:** done

- [x] Creating past a plan limit returns a clear error naming the limit
- [x] Interval clamp + webhook gating reflect the current tier
- [x] Customer Portal opens for the team's Stripe customer
- [x] Downgrade below usage pauses excess monitors (no deletion); covered by a test
- [x] Billing page shows usage against each limit

## Comments

Backend green: 58 pytest. Enforced monitor count, seats (invite+accept), webhook Pro-gate, interval clamp. Portal endpoint (owner). Downgrade webhook pauses excess monitors (RLS-scoped via set_config). Live: 4th monitor→402, webhook on free→402.

# 08 — Alerts: email + webhooks

**What to build:** On incident open/resolve, email all owners+admins (via the email sender) and POST a JSON payload to each configured team/monitor webhook (Celery task with limited retries). Webhook config UI (Pro+ gating applied later in 11). SSL cert-expiry emits a warning-level alert, not a down incident.

**Blocked by:** 07, 03

**Status:** done

- [x] Incident open + resolve each send an email to owners+admins (captured in tests)
- [x] Configured webhooks receive a JSON POST on incident events; failures retry with backoff
- [x] SSL cert-expiry warning produces an alert without opening a down incident
- [x] Plain members receive no alert

# 10 — Stripe Checkout + verified webhooks + tier sync

**What to build:** Plan-limits config (free/pro/team dimensions from Preset A) as the single source enforcement reads. Stripe products/prices. Checkout session creation to subscribe/upgrade. Webhook endpoint verifying the Stripe signature, deduping by event id, handling `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`; persisting `stripe_customer_id`, `stripe_subscription_id`, `tier`, `status`, `current_period_end` on the team. Billing page shows current plan + renewal.

**Blocked by:** 02

**Status:** done

- [x] Owner starts Checkout; on completion the team's tier updates via webhook
- [x] Webhook signature verified; invalid signatures rejected; duplicate event ids ignored (idempotent)
- [x] `subscription.updated`/`.deleted` and `invoice.payment_failed` update tier/status
- [x] Billing page shows plan, status, renewal date
- [x] Billing flow covered by a signed-webhook integration test (non-negotiable)

## Comments

Backend green: 53+ pytest. Signed-webhook tests verify checkout→tier, idempotency (dedupe by event id in Redis), subscription.updated/.deleted/payment_failed. Hosted Checkout via stripe SDK. Frontend billing page shows plan/limits + upgrade buttons. Live: GET /billing returns free/3.

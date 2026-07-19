import json
import uuid
from datetime import UTC, datetime

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.deps import get_current_membership, get_db, require_role
from app.models import Membership, Monitor, Role, Team
from app.plans import PlanLimits, limits
from app.redis import redis_client

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutIn(BaseModel):
    tier: str


class CheckoutOut(BaseModel):
    url: str


class BillingOut(BaseModel):
    tier: str
    status: str | None
    current_period_end: datetime | None
    limits: PlanLimits


@router.get("", response_model=BillingOut)
async def get_billing(
    membership: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
) -> BillingOut:
    team = await db.get(Team, membership.team_id)
    assert team is not None
    return BillingOut(
        tier=team.tier,
        status=team.subscription_status,
        current_period_end=team.current_period_end,
        limits=limits(team.tier),
    )


@router.post("/checkout", response_model=CheckoutOut)
async def create_checkout(
    body: CheckoutIn,
    membership: Membership = Depends(require_role(Role.owner)),
    db: AsyncSession = Depends(get_db),
) -> CheckoutOut:
    if body.tier not in ("pro", "team"):
        raise HTTPException(400, "Invalid tier")
    price_id = settings.price_for_tier(body.tier)
    if not price_id or not settings.stripe_secret_key:
        raise HTTPException(503, "Billing is not configured")

    stripe.api_key = settings.stripe_secret_key
    team = await db.get(Team, membership.team_id)
    assert team is not None
    if not team.stripe_customer_id:
        customer = stripe.Customer.create(metadata={"team_id": str(team.id)})
        team.stripe_customer_id = customer.id

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=team.stripe_customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=settings.billing_success_url,
        cancel_url=settings.billing_cancel_url,
        metadata={"team_id": str(team.id), "tier": body.tier},
        subscription_data={"metadata": {"team_id": str(team.id), "tier": body.tier}},
    )
    return CheckoutOut(url=session.url)


@router.post("/portal", response_model=CheckoutOut)
async def customer_portal(
    membership: Membership = Depends(require_role(Role.owner)),
    db: AsyncSession = Depends(get_db),
) -> CheckoutOut:
    team = await db.get(Team, membership.team_id)
    assert team is not None
    if not team.stripe_customer_id or not settings.stripe_secret_key:
        raise HTTPException(503, "No billing account yet")
    stripe.api_key = settings.stripe_secret_key
    session = stripe.billing_portal.Session.create(
        customer=team.stripe_customer_id, return_url=settings.billing_success_url
    )
    return CheckoutOut(url=session.url)


async def _enforce_monitor_limit(db: AsyncSession, team: Team) -> None:
    """On downgrade, pause monitors beyond the new plan limit (keep the oldest active)."""
    max_monitors = limits(team.tier)["max_monitors"]
    if max_monitors < 0:
        return
    # Scope RLS to this team so the webhook context can see + pause its monitors.
    await db.execute(
        text("SELECT set_config('app.current_team_id', :t, true)"), {"t": str(team.id)}
    )
    active = (
        (
            await db.execute(
                select(Monitor).where(Monitor.paused.is_(False)).order_by(Monitor.created_at)
            )
        )
        .scalars()
        .all()
    )
    for monitor in active[max_monitors:]:
        monitor.paused = True


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except Exception as exc:
        raise HTTPException(400, "Invalid signature") from exc

    # Signature verified; work with plain JSON dicts.
    event = json.loads(payload)

    # Idempotency: process each Stripe event id at most once.
    if not await redis_client.set(f"stripe_evt:{event['id']}", "1", ex=86400, nx=True):
        return {"status": "duplicate"}

    await _handle_event(db, event["type"], event["data"]["object"])
    return {"status": "ok"}


async def _team_for_customer(db: AsyncSession, customer_id: str | None) -> Team | None:
    if not customer_id:
        return None
    return (
        await db.execute(select(Team).where(Team.stripe_customer_id == customer_id))
    ).scalar_one_or_none()


async def _team_for_subscription(db: AsyncSession, obj) -> Team | None:
    team_id = (obj.get("metadata") or {}).get("team_id")
    if team_id:
        return await db.get(Team, uuid.UUID(team_id))
    return await _team_for_customer(db, obj.get("customer"))


async def _handle_event(db: AsyncSession, event_type: str, obj) -> None:
    if event_type == "checkout.session.completed":
        team_id = (obj.get("metadata") or {}).get("team_id")
        tier = (obj.get("metadata") or {}).get("tier")
        team = await db.get(Team, uuid.UUID(team_id)) if team_id else None
        if team:
            team.stripe_customer_id = obj.get("customer") or team.stripe_customer_id
            team.stripe_subscription_id = obj.get("subscription")
            if tier:
                team.tier = tier
            team.subscription_status = "active"

    elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
        team = await _team_for_subscription(db, obj)
        if team:
            team.subscription_status = obj.get("status")
            team.stripe_subscription_id = obj.get("id")
            items = obj.get("items") or {}
            data = items.get("data") or []
            if data:
                mapped = settings.tier_for_price(data[0]["price"]["id"])
                if mapped:
                    team.tier = mapped
            cpe = obj.get("current_period_end")
            team.current_period_end = datetime.fromtimestamp(cpe, UTC) if cpe else None
            await _enforce_monitor_limit(db, team)

    elif event_type == "customer.subscription.deleted":
        team = await _team_for_subscription(db, obj)
        if team:
            team.tier = "free"
            team.subscription_status = "canceled"
            team.stripe_subscription_id = None
            await _enforce_monitor_limit(db, team)

    elif event_type == "invoice.payment_failed":
        team = await _team_for_customer(db, obj.get("customer"))
        if team:
            team.subscription_status = "past_due"

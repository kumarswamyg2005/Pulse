import hashlib
import hmac
import json
import time
import types

import stripe


async def _owner(clients, email="bill@x.com"):
    c = await clients()
    team = (await c.post("/auth/signup", json={"email": email, "password": "password123"})).json()[
        "current_team"
    ]["id"]
    return c, team


def _signed(payload: dict, secret: str = "whsec_test") -> tuple[str, str]:
    body = json.dumps(payload)
    ts = int(time.time())
    sig = hmac.new(secret.encode(), f"{ts}.{body}".encode(), hashlib.sha256).hexdigest()
    return body, f"t={ts},v1={sig}"


async def test_checkout_returns_url(clients, monkeypatch):
    monkeypatch.setattr(stripe.Customer, "create", lambda **kw: types.SimpleNamespace(id="cus_1"))
    monkeypatch.setattr(
        stripe.checkout.Session,
        "create",
        lambda **kw: types.SimpleNamespace(url="https://checkout.stripe.test/x"),
    )
    c, _ = await _owner(clients)
    r = await c.post("/billing/checkout", json={"tier": "pro"})
    assert r.status_code == 200
    assert r.json()["url"].startswith("https://checkout")


async def test_checkout_owner_only(clients, monkeypatch):
    import re

    from app.email import outbox
    from tests.helpers import set_tier

    owner, team = await _owner(clients, "own@x.com")
    set_tier(team, "team")
    member = await clients()
    await member.post("/auth/signup", json={"email": "mem@x.com", "password": "password123"})
    await owner.post(f"/teams/{team}/invites", json={"email": "mem@x.com"})
    token = re.search(r"/invite/([\w-]+)", outbox[-1].html).group(1)
    await member.post(f"/invites/{token}/accept")
    await member.post(f"/teams/{team}/switch")
    assert (await member.post("/billing/checkout", json={"tier": "pro"})).status_code == 403


async def test_webhook_rejects_bad_signature(clients):
    c, _ = await _owner(clients)
    r = await c.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "t=1,v1=bad"})
    assert r.status_code == 400


async def test_webhook_checkout_completed_applies_tier(clients):
    c, team = await _owner(clients)
    payload = {
        "id": "evt_1",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"team_id": team, "tier": "pro"},
                "customer": "cus_1",
                "subscription": "sub_1",
            }
        },
    }
    body, sig = _signed(payload)
    r = await c.post("/billing/webhook", content=body, headers={"stripe-signature": sig})
    assert r.status_code == 200
    billing = (await c.get("/billing")).json()
    assert billing["tier"] == "pro"
    assert billing["status"] == "active"
    assert billing["limits"]["max_monitors"] == 25


async def test_webhook_is_idempotent(clients):
    c, team = await _owner(clients)
    payload = {
        "id": "evt_dup",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"team_id": team, "tier": "pro"}, "customer": "cus_1"}},
    }
    body, sig = _signed(payload)
    assert (
        await c.post("/billing/webhook", content=body, headers={"stripe-signature": sig})
    ).json() == {"status": "ok"}
    # same event id again -> ignored
    body2, sig2 = _signed(payload)
    assert (
        await c.post("/billing/webhook", content=body2, headers={"stripe-signature": sig2})
    ).json() == {"status": "duplicate"}


async def test_webhook_subscription_deleted_downgrades(clients):
    c, team = await _owner(clients)
    # first go pro
    up, sig = _signed(
        {
            "id": "evt_up",
            "object": "event",
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {"team_id": team, "tier": "pro"}, "customer": "cus_9"}},
        }
    )
    await c.post("/billing/webhook", content=up, headers={"stripe-signature": sig})
    assert (await c.get("/billing")).json()["tier"] == "pro"

    # then cancel
    down, sig2 = _signed(
        {
            "id": "evt_down",
            "object": "event",
            "type": "customer.subscription.deleted",
            "data": {"object": {"metadata": {"team_id": team}, "customer": "cus_9"}},
        }
    )
    await c.post("/billing/webhook", content=down, headers={"stripe-signature": sig2})
    b = (await c.get("/billing")).json()
    assert b["tier"] == "free"
    assert b["status"] == "canceled"

import hashlib
import hmac
import json
import time
import types

import stripe


def _event(payload: dict) -> tuple[str, dict[str, str]]:
    body = json.dumps(payload)
    ts = int(time.time())
    sig = hmac.new(b"whsec_test", f"{ts}.{body}".encode(), hashlib.sha256).hexdigest()
    return body, {"stripe-signature": f"t={ts},v1={sig}"}


async def _owner(clients, email="lim@x.com"):
    c = await clients()
    team = (await c.post("/auth/signup", json={"email": email, "password": "password123"})).json()[
        "current_team"
    ]["id"]
    return c, team


async def _set_tier(c, team, tier, evtid, customer=None):
    body, headers = _event(
        {
            "id": evtid,
            "object": "event",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {"team_id": team, "tier": tier},
                    "customer": customer or f"cus_{evtid}",
                }
            },
        }
    )
    r = await c.post("/billing/webhook", content=body, headers=headers)
    assert r.status_code == 200, r.text


async def test_monitor_limit_enforced(clients):
    c, _ = await _owner(clients)
    for i in range(3):
        assert (
            await c.post("/monitors", json={"name": f"m{i}", "url": "http://x.test"})
        ).status_code == 201
    assert (
        await c.post("/monitors", json={"name": "m4", "url": "http://x.test"})
    ).status_code == 402


async def test_seat_limit_free_then_pro(clients):
    c, team = await _owner(clients)
    # free: max_seats 1, owner already occupies it
    assert (await c.post(f"/teams/{team}/invites", json={"email": "x@x.com"})).status_code == 402
    await _set_tier(c, team, "pro", "seat1")
    assert (await c.post(f"/teams/{team}/invites", json={"email": "x@x.com"})).status_code == 201


async def test_webhooks_require_pro(clients):
    c, team = await _owner(clients)
    assert (await c.post("/webhooks", json={"url": "https://h.x"})).status_code == 402
    await _set_tier(c, team, "pro", "wh1")
    assert (await c.post("/webhooks", json={"url": "https://h.x"})).status_code == 201


async def test_downgrade_pauses_excess_monitors(clients):
    c, team = await _owner(clients)
    await _set_tier(c, team, "pro", "up1", customer="cus_dg")
    for i in range(4):
        await c.post("/monitors", json={"name": f"m{i}", "url": "http://x.test"})

    body, headers = _event(
        {
            "id": "del1",
            "object": "event",
            "type": "customer.subscription.deleted",
            "data": {"object": {"metadata": {"team_id": team}, "customer": "cus_dg"}},
        }
    )
    assert (await c.post("/billing/webhook", content=body, headers=headers)).status_code == 200

    monitors = (await c.get("/monitors")).json()
    assert sum(1 for m in monitors if not m["paused"]) == 3  # free limit
    assert sum(1 for m in monitors if m["paused"]) == 1


async def test_customer_portal(clients, monkeypatch):
    c, team = await _owner(clients)
    await _set_tier(c, team, "pro", "port1")  # gives the team a stripe_customer_id
    monkeypatch.setattr(
        stripe.billing_portal.Session,
        "create",
        lambda **kw: types.SimpleNamespace(url="https://portal.stripe.test/x"),
    )
    r = await c.post("/billing/portal")
    assert r.status_code == 200
    assert r.json()["url"].startswith("https://portal")

import app.alerts as alerts_mod
import app.checks as checks_mod
from app.checks import CheckOutcome
from app.email import outbox
from app.models import MonitorType
from app.tasks import run_check
from tests.helpers import set_tier


async def _enable_webhooks(c):
    team = (await c.get("/auth/me")).json()["current_team"]["id"]
    set_tier(team, "pro")


async def _setup(clients, monkeypatch, up=False):
    state = {"up": up}
    monkeypatch.setitem(
        checks_mod.CHECKERS,
        MonitorType.http,
        lambda m: CheckOutcome(up=state["up"], status_code=200 if state["up"] else 500),
    )
    c = await clients()
    await c.post("/auth/signup", json={"email": "al@x.com", "password": "password123"})
    mid = (await c.post("/monitors", json={"name": "M", "url": "http://x.test"})).json()["id"]
    return c, mid, state


async def test_incident_open_emails_admins(clients, monkeypatch):
    c, mid, state = await _setup(clients, monkeypatch, up=False)
    for _ in range(3):
        run_check(mid)
    assert any(e.to == "al@x.com" and "DOWN" in e.subject for e in outbox)


async def test_resolve_emails_admins(clients, monkeypatch):
    c, mid, state = await _setup(clients, monkeypatch, up=False)
    for _ in range(3):
        run_check(mid)
    outbox.clear()
    state["up"] = True
    for _ in range(2):
        run_check(mid)
    assert any("back UP" in e.subject for e in outbox)


async def test_webhook_fires_on_incident(clients, monkeypatch):
    delivered: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        alerts_mod, "_post_webhook", lambda url, payload: delivered.append((url, payload))
    )
    c, mid, state = await _setup(clients, monkeypatch, up=False)
    await _enable_webhooks(c)
    assert (
        await c.post("/webhooks", json={"url": "https://hooks.example.com/x"})
    ).status_code == 201
    for _ in range(3):
        run_check(mid)
    assert len(delivered) == 1
    assert delivered[0][0] == "https://hooks.example.com/x"
    assert delivered[0][1]["event"] == "opened"


async def test_webhook_crud(clients, monkeypatch):
    c, mid, state = await _setup(clients, monkeypatch)
    await _enable_webhooks(c)
    wid = (await c.post("/webhooks", json={"url": "https://h.example.com"})).json()["id"]
    assert len((await c.get("/webhooks")).json()) == 1
    assert (await c.delete(f"/webhooks/{wid}")).status_code == 204
    assert (await c.get("/webhooks")).json() == []

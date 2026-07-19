import app.checks as checks_mod
from app.checks import CheckOutcome
from app.models import MonitorType
from app.tasks import run_check


async def _setup(clients, monkeypatch):
    state = {"up": True}
    monkeypatch.setitem(
        checks_mod.CHECKERS,
        MonitorType.http,
        lambda m: CheckOutcome(up=state["up"], status_code=200 if state["up"] else 500),
    )
    c = await clients()
    await c.post("/auth/signup", json={"email": "inc@x.com", "password": "password123"})
    mid = (await c.post("/monitors", json={"name": "M", "url": "http://x.test"})).json()["id"]
    return c, mid, state


async def test_incident_opens_after_threshold_and_auto_resolves(clients, monkeypatch):
    c, mid, state = await _setup(clients, monkeypatch)

    state["up"] = False
    run_check(mid)
    run_check(mid)
    assert (await c.get("/incidents")).json() == []  # 2 failures < threshold of 3

    run_check(mid)  # third consecutive failure
    incs = (await c.get("/incidents")).json()
    assert len(incs) == 1
    assert incs[0]["status"] == "open"
    assert incs[0]["monitor_name"] == "M"

    run_check(mid)  # more failures do not open a second incident
    assert len((await c.get("/incidents")).json()) == 1

    state["up"] = True
    run_check(mid)
    assert (await c.get("/incidents")).json()[0]["status"] == "open"  # 1 success < threshold of 2
    run_check(mid)
    assert (await c.get("/incidents")).json()[0]["status"] == "resolved"


async def test_acknowledge_incident(clients, monkeypatch):
    c, mid, state = await _setup(clients, monkeypatch)
    state["up"] = False
    for _ in range(3):
        run_check(mid)

    inc = (await c.get("/incidents")).json()[0]
    r = await c.post(f"/incidents/{inc['id']}/acknowledge")
    assert r.status_code == 200
    assert r.json()["acknowledged_at"] is not None
    assert r.json()["acknowledged_by"] is not None


async def test_monitor_incident_timeline(clients, monkeypatch):
    c, mid, state = await _setup(clients, monkeypatch)
    state["up"] = False
    for _ in range(3):
        run_check(mid)
    assert len((await c.get(f"/monitors/{mid}/incidents")).json()) == 1

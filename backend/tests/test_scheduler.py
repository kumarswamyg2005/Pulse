import app.checks as checks_mod
import app.tasks as tasks_mod
from app.checks import CheckOutcome
from app.models import MonitorType
from app.tasks import dispatch_due_checks, run_check


async def _owner_with_monitor(clients, monkeypatch, up=True):
    monkeypatch.setitem(
        checks_mod.CHECKERS,
        MonitorType.http,
        lambda m: CheckOutcome(up=up, status_code=200 if up else 500, latency_ms=7),
    )
    c = await clients()
    await c.post("/auth/signup", json={"email": "s@x.com", "password": "password123"})
    mid = (await c.post("/monitors", json={"name": "M", "url": "http://x.test"})).json()["id"]
    return c, mid


async def test_run_check_records_result_and_uptime(clients, monkeypatch):
    c, mid = await _owner_with_monitor(clients, monkeypatch, up=True)

    run_check(mid)  # sync task body, admin connection (bypasses RLS)

    results = (await c.get(f"/monitors/{mid}/results")).json()
    assert len(results) == 1
    assert results[0]["up"] is True

    detail = (await c.get(f"/monitors/{mid}")).json()
    assert detail["last_status"] is True
    assert detail["uptime_24h"] == 100.0


async def test_run_check_records_down(clients, monkeypatch):
    c, mid = await _owner_with_monitor(clients, monkeypatch, up=False)
    run_check(mid)
    detail = (await c.get(f"/monitors/{mid}")).json()
    assert detail["last_status"] is False
    assert detail["uptime_24h"] == 0.0


async def test_dispatch_enqueues_due_monitor(clients, monkeypatch):
    c, mid = await _owner_with_monitor(clients, monkeypatch)
    enqueued: list[str] = []
    monkeypatch.setattr(tasks_mod.run_check, "delay", lambda x: enqueued.append(x))

    # monitor's next_check_at was set to now at create -> due
    dispatched = dispatch_due_checks()
    assert dispatched == 1
    assert enqueued == [mid]


async def test_dispatch_skips_paused(clients, monkeypatch):
    c, mid = await _owner_with_monitor(clients, monkeypatch)
    await c.patch(f"/monitors/{mid}", json={"paused": True})
    monkeypatch.setattr(tasks_mod.run_check, "delay", lambda x: None)
    assert dispatch_due_checks() == 0

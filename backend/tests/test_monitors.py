import re

from app.email import outbox
from tests.helpers import set_tier


async def _owner(clients, email="a@x.com"):
    c = await clients()
    r = await c.post("/auth/signup", json={"email": email, "password": "password123"})
    return c, r.json()["current_team"]["id"]


async def _member(clients, owner, team, email="m@x.com"):
    set_tier(team, "team")  # multi-member team needs a paid plan
    m = await clients()
    await m.post("/auth/signup", json={"email": email, "password": "password123"})
    await owner.post(f"/teams/{team}/invites", json={"email": email})
    token = re.search(r"/invite/([\w-]+)", outbox[-1].html).group(1)
    await m.post(f"/invites/{token}/accept")
    await m.post(f"/teams/{team}/switch")  # act inside the owner's team
    return m


async def test_create_and_list(clients):
    a, _ = await _owner(clients)
    r = await a.post("/monitors", json={"name": "Site", "url": "https://example.com"})
    assert r.status_code == 201, r.text
    assert r.json()["url"] == "https://example.com"
    assert len((await a.get("/monitors")).json()) == 1


async def test_interval_clamped_to_plan_min(clients):
    a, _ = await _owner(clients)
    r = await a.post(
        "/monitors", json={"name": "x", "url": "https://x.com", "interval_seconds": 30}
    )
    # free tier min is 300s
    assert r.json()["interval_seconds"] == 300


async def test_member_is_read_only(clients):
    a, team = await _owner(clients)
    m = await _member(clients, a, team)
    assert (await m.get("/monitors")).status_code == 200
    r = await m.post("/monitors", json={"name": "x", "url": "https://x.com"})
    assert r.status_code == 403


async def test_cross_tenant_isolation(clients):
    a, _ = await _owner(clients, "a@x.com")
    mon_id = (await a.post("/monitors", json={"name": "A", "url": "https://a.com"})).json()["id"]

    b, _ = await _owner(clients, "b@x.com")
    # RLS: B sees none of A's monitors and cannot fetch by id
    assert (await b.get("/monitors")).json() == []
    assert (await b.get(f"/monitors/{mon_id}")).status_code == 404
    # A still sees its own
    assert len((await a.get("/monitors")).json()) == 1


async def test_update_and_delete(clients):
    a, _ = await _owner(clients)
    mid = (await a.post("/monitors", json={"name": "m", "url": "https://x.com"})).json()["id"]
    r = await a.patch(f"/monitors/{mid}", json={"paused": True, "name": "renamed"})
    assert r.json()["paused"] is True
    assert r.json()["name"] == "renamed"
    assert (await a.delete(f"/monitors/{mid}")).status_code == 204
    assert (await a.get("/monitors")).json() == []


async def test_http_requires_url(clients):
    a, _ = await _owner(clients)
    assert (await a.post("/monitors", json={"name": "x"})).status_code == 422

from app.seed import seed


async def test_seed_creates_demo_team(clients):
    seed()

    visitor = await clients()
    r = await visitor.get("/status/demo")
    assert r.status_code == 200
    body = r.json()
    assert body["team"] == "Demo Co"

    names = [m["name"] for m in body["monitors"]]
    assert "Marketing site" in names  # public
    assert "Postgres" not in names  # private tcp monitor
    assert len(body["incidents"]) >= 1  # open incident on the API monitor


async def test_seed_is_idempotent(clients):
    seed()
    seed()  # second run replaces, doesn't duplicate
    visitor = await clients()
    body = (await visitor.get("/status/demo")).json()
    # 3 public monitors: Marketing site, API, Gateway
    assert len(body["monitors"]) == 3

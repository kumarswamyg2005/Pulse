async def test_public_status_shows_only_public_monitors(clients):
    owner = await clients()
    signup = (
        await owner.post("/auth/signup", json={"email": "st@x.com", "password": "password123"})
    ).json()
    slug = signup["current_team"]["slug"]

    await owner.post(
        "/monitors", json={"name": "PublicMon", "url": "http://x.test", "public": True}
    )
    await owner.post(
        "/monitors", json={"name": "PrivateMon", "url": "http://x.test", "public": False}
    )

    # unauthenticated visitor
    visitor = await clients()
    r = await visitor.get(f"/status/{slug}")
    assert r.status_code == 200
    body = r.json()
    assert body["team"] == signup["current_team"]["name"]
    names = [m["name"] for m in body["monitors"]]
    assert "PublicMon" in names
    assert "PrivateMon" not in names


async def test_public_status_unknown_slug_404(clients):
    visitor = await clients()
    assert (await visitor.get("/status/does-not-exist")).status_code == 404


async def test_public_status_is_cached(clients):
    owner = await clients()
    slug = (
        await owner.post("/auth/signup", json={"email": "cache@x.com", "password": "password123"})
    ).json()["current_team"]["slug"]
    await owner.post("/monitors", json={"name": "First", "url": "http://x.test", "public": True})

    visitor = await clients()
    assert len((await visitor.get(f"/status/{slug}")).json()["monitors"]) == 1

    # add another public monitor; the cached response should still show the old count
    await owner.post("/monitors", json={"name": "Second", "url": "http://x.test", "public": True})
    assert len((await visitor.get(f"/status/{slug}")).json()["monitors"]) == 1

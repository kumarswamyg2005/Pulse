async def test_signup_creates_user_team_session(client):
    r = await client.post("/auth/signup", json={"email": "a@b.com", "password": "password123"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["user"]["email"] == "a@b.com"
    assert body["current_team"]["slug"]
    assert client.cookies.get("pulse_session")


async def test_me_returns_user_and_team(auth_client):
    r = await auth_client.get("/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["email"] == "owner@example.com"
    assert body["current_team"]["name"]
    assert len(body["teams"]) == 1


async def test_short_password_rejected(client):
    r = await client.post("/auth/signup", json={"email": "a@b.com", "password": "short"})
    assert r.status_code == 422


async def test_duplicate_email_rejected(client):
    await client.post("/auth/signup", json={"email": "a@b.com", "password": "password123"})
    r = await client.post("/auth/signup", json={"email": "a@b.com", "password": "password123"})
    assert r.status_code == 409


async def test_me_requires_auth(client):
    r = await client.get("/auth/me")
    assert r.status_code == 401


async def test_login_logout_cycle(client):
    await client.post("/auth/signup", json={"email": "a@b.com", "password": "password123"})
    r = await client.post("/auth/logout")
    assert r.status_code == 204
    assert (await client.get("/auth/me")).status_code == 401

    r = await client.post("/auth/login", json={"email": "a@b.com", "password": "password123"})
    assert r.status_code == 200
    assert (await client.get("/auth/me")).status_code == 200


async def test_wrong_password_rejected(client):
    await client.post("/auth/signup", json={"email": "a@b.com", "password": "password123"})
    await client.post("/auth/logout")
    r = await client.post("/auth/login", json={"email": "a@b.com", "password": "wrongpass1"})
    assert r.status_code == 401

import re

from app.email import outbox


def _token_from_last_email() -> str:
    m = re.search(r"token=([\w-]+)", outbox[-1].html)
    assert m, "no reset token in email"
    return m.group(1)


async def test_forgot_then_reset_password(client):
    await client.post("/auth/signup", json={"email": "a@b.com", "password": "password123"})
    await client.post("/auth/logout")

    r = await client.post("/auth/forgot-password", json={"email": "a@b.com"})
    assert r.status_code == 202
    assert len(outbox) == 1

    token = _token_from_last_email()
    r = await client.post("/auth/reset-password", json={"token": token, "password": "newpass123"})
    assert r.status_code == 200

    r = await client.post("/auth/login", json={"email": "a@b.com", "password": "newpass123"})
    assert r.status_code == 200


async def test_forgot_unknown_email_is_202_and_sends_nothing(client):
    r = await client.post("/auth/forgot-password", json={"email": "nobody@x.com"})
    assert r.status_code == 202
    assert outbox == []


async def test_reset_with_invalid_token_rejected(client):
    r = await client.post("/auth/reset-password", json={"token": "bogus", "password": "newpass123"})
    assert r.status_code == 400


async def test_reset_token_is_single_use(client):
    await client.post("/auth/signup", json={"email": "a@b.com", "password": "password123"})
    await client.post("/auth/forgot-password", json={"email": "a@b.com"})
    token = _token_from_last_email()

    assert (
        await client.post("/auth/reset-password", json={"token": token, "password": "newpass123"})
    ).status_code == 200
    # second use of the same token is rejected
    assert (
        await client.post("/auth/reset-password", json={"token": token, "password": "other12345"})
    ).status_code == 400

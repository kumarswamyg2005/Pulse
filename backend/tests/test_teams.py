import re

from app.email import outbox
from tests.helpers import set_tier


async def _signup(c, email, pw="password123"):
    r = await c.post("/auth/signup", json={"email": email, "password": pw})
    assert r.status_code == 201, r.text
    return r.json()


def _invite_token() -> str:
    m = re.search(r"/invite/([\w-]+)", outbox[-1].html)
    assert m, "no invite token in email"
    return m.group(1)


async def _invite_and_accept(owner, member, team, email, role="member"):
    set_tier(team, "team")  # multi-member teams need a paid plan (seat limit)
    r = await owner.post(f"/teams/{team}/invites", json={"email": email, "role": role})
    assert r.status_code == 201, r.text
    r = await member.post(f"/invites/{_invite_token()}/accept")
    assert r.status_code == 201, r.text


async def test_owner_invites_and_member_accepts(clients):
    owner, member = await clients(), await clients()
    team = (await _signup(owner, "owner@x.com"))["current_team"]["id"]
    await _signup(member, "member@x.com")
    await _invite_and_accept(owner, member, team, "member@x.com")

    members = (await owner.get(f"/teams/{team}/members")).json()
    assert len(members) == 2
    assert len((await member.get("/auth/me")).json()["teams"]) == 2


async def test_member_cannot_invite(clients):
    owner, member = await clients(), await clients()
    team = (await _signup(owner, "owner@x.com"))["current_team"]["id"]
    await _signup(member, "member@x.com")
    await _invite_and_accept(owner, member, team, "member@x.com")
    r = await member.post(f"/teams/{team}/invites", json={"email": "third@x.com"})
    assert r.status_code == 403


async def test_non_member_cannot_view(clients):
    owner, stranger = await clients(), await clients()
    team = (await _signup(owner, "owner@x.com"))["current_team"]["id"]
    await _signup(stranger, "stranger@x.com")
    assert (await stranger.get(f"/teams/{team}/members")).status_code == 403


async def test_accept_requires_matching_email(clients):
    owner, wrong = await clients(), await clients()
    team = (await _signup(owner, "owner@x.com"))["current_team"]["id"]
    set_tier(team, "team")
    await _signup(wrong, "wrong@x.com")
    r = await owner.post(f"/teams/{team}/invites", json={"email": "invited@x.com"})
    assert r.status_code == 201
    assert (await wrong.post(f"/invites/{_invite_token()}/accept")).status_code == 403


async def test_change_role_and_remove(clients):
    owner, member = await clients(), await clients()
    team = (await _signup(owner, "owner@x.com"))["current_team"]["id"]
    m_uid = (await _signup(member, "member@x.com"))["user"]["id"]
    await _invite_and_accept(owner, member, team, "member@x.com")

    assert (
        await owner.patch(f"/teams/{team}/members/{m_uid}", json={"role": "admin"})
    ).status_code == 204
    # promoted member (now admin) can invite
    assert (
        await member.post(f"/teams/{team}/invites", json={"email": "z@x.com"})
    ).status_code == 201
    assert (await owner.delete(f"/teams/{team}/members/{m_uid}")).status_code == 204
    assert len((await owner.get(f"/teams/{team}/members")).json()) == 1


async def test_cannot_remove_or_demote_owner(clients):
    owner, member = await clients(), await clients()
    o = await _signup(owner, "owner@x.com")
    team, owner_uid = o["current_team"]["id"], o["user"]["id"]
    m_uid = (await _signup(member, "member@x.com"))["user"]["id"]
    await _invite_and_accept(owner, member, team, "member@x.com")
    await owner.patch(f"/teams/{team}/members/{m_uid}", json={"role": "admin"})

    assert (await member.delete(f"/teams/{team}/members/{owner_uid}")).status_code == 403
    assert (
        await member.patch(f"/teams/{team}/members/{owner_uid}", json={"role": "member"})
    ).status_code == 403


async def test_transfer_ownership(clients):
    owner, member = await clients(), await clients()
    o = await _signup(owner, "owner@x.com")
    team, owner_uid = o["current_team"]["id"], o["user"]["id"]
    m_uid = (await _signup(member, "member@x.com"))["user"]["id"]
    await _invite_and_accept(owner, member, team, "member@x.com")

    assert (
        await owner.post(f"/teams/{team}/transfer-ownership", json={"user_id": m_uid})
    ).status_code == 204
    roles = {r["user_id"]: r["role"] for r in (await owner.get(f"/teams/{team}/members")).json()}
    assert roles[m_uid] == "owner"
    assert roles[owner_uid] == "admin"


async def test_switch_team(clients):
    owner, member = await clients(), await clients()
    owner_team = (await _signup(owner, "owner@x.com"))["current_team"]["id"]
    await _signup(member, "member@x.com")
    await _invite_and_accept(owner, member, owner_team, "member@x.com")

    assert (await member.post(f"/teams/{owner_team}/switch")).status_code == 200
    assert (await member.get("/auth/me")).json()["current_team"]["id"] == owner_team


async def test_create_team_makes_owner(clients):
    user = await clients()
    await _signup(user, "solo@x.com")
    r = await user.post("/teams", json={"name": "Second Team"})
    assert r.status_code == 201
    new_team = r.json()["id"]
    members = (await user.get(f"/teams/{new_team}/members")).json()
    assert members[0]["role"] == "owner"

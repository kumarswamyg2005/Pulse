from app.accounts import get_or_create_oauth_user


async def test_oauth_upsert_creates_then_reuses(db):
    user1, team1 = await get_or_create_oauth_user(db, "g@example.com")
    await db.commit()
    assert team1 is not None

    user2, team2 = await get_or_create_oauth_user(db, "g@example.com")
    assert user2.id == user1.id
    assert team2 == team1
    assert user1.password_hash is None  # OAuth-only user has no password

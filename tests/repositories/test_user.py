import pytest

from movielibrary.repositories.user import UserRepository
from tests.helpers import create_user


@pytest.mark.asyncio
async def test_get_receiver_emails_returns_empty_list_when_no_users(db_session):
    repository = UserRepository(db_session)

    result = await repository.get_receiver_emails()

    assert result == []


@pytest.mark.asyncio
async def test_get_receiver_emails_returns_all_emails(db_session):
    users = [
        create_user(email="alice@example.com"),
        create_user(email="bob@example.com"),
        create_user(email="charlie@example.com"),
    ]
    db_session.add_all(users)
    await db_session.commit()

    repository = UserRepository(db_session)

    result = await repository.get_receiver_emails()

    assert set(result) == {
        "alice@example.com",
        "bob@example.com",
        "charlie@example.com",
    }
    assert len(result) == 3

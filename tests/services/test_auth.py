import pytest
from fastapi import HTTPException

from movielibrary.auth_utils import get_password_hash, verify_password
from movielibrary.schemas.user import UserCreate
from movielibrary.services.auth import AuthService
from tests.helpers import create_user


@pytest.mark.asyncio
async def test_register_user_success(db_session):
    payload = UserCreate(
        email="alice@example.com",
        password="secret123",
    )

    service = AuthService(db_session)
    user = await service.register_user(payload)

    assert user.id is not None
    assert user.email == "alice@example.com"
    assert user.password_hash != "secret123"
    assert verify_password("secret123", user.password_hash)


@pytest.mark.asyncio
async def test_register_user_duplicate_email_raises_400(db_session):
    payload = UserCreate(
        email="alice@example.com",
        password="secret123",
    )

    service = AuthService(db_session)
    await service.register_user(payload)

    with pytest.raises(HTTPException) as exc_info:
        await service.register_user(payload)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Пользователь уже существует"


@pytest.mark.asyncio
async def test_authenticate_user_success(db_session):
    user = create_user(
        email="alice@example.com",
        password_hash=get_password_hash("secret123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = AuthService(db_session)
    result = await service.authenticate_user("alice@example.com", "secret123")

    assert result.id == user.id
    assert result.email == "alice@example.com"
    assert result.last_login is not None


@pytest.mark.asyncio
async def test_authenticate_user_not_found(db_session):
    service = AuthService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate_user("noone@example.com", "secret123")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Пользователя не существует"


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session):
    user = create_user(
        email="alice@example.com",
        password_hash=get_password_hash("secret123"),
    )
    db_session.add(user)
    await db_session.commit()

    service = AuthService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate_user("alice@example.com", "wrong-password")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Неправильный пароль"


@pytest.mark.asyncio
async def test_change_user_password_success(db_session):
    user = create_user(
        email="alice@example.com",
        password_hash=get_password_hash("old-password"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = AuthService(db_session)
    result = await service.change_user_password(
        user,
        old_password="old-password",
        new_password="new-password",
    )

    assert verify_password("new-password", result.password_hash)
    assert not verify_password("old-password", result.password_hash)


@pytest.mark.asyncio
async def test_change_user_password_wrong_old_password(db_session):
    user = create_user(
        email="alice@example.com",
        password_hash=get_password_hash("old-password"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = AuthService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.change_user_password(
            user,
            old_password="wrong-old",
            new_password="new-password",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Неверный старый пароль"

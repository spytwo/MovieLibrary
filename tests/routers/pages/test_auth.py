from unittest.mock import AsyncMock, patch
from urllib.parse import unquote

import pytest

from movielibrary.auth_utils import get_password_hash
from tests.helpers import create_user, login_user


@pytest.mark.asyncio
async def test_register_form_returns_html(client):
    response = await client.get("/register")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "csrf_token" in response.text or "csrf" in response.text.lower()
    assert "csrf_token" in response.cookies


@pytest.mark.asyncio
async def test_login_form_returns_html(client):
    response = await client.get("/login")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "csrf_token" in response.cookies


@pytest.mark.asyncio
async def test_register_success(client, db_session):
    form_response = await client.get("/register")
    assert form_response.status_code == 200
    csrf_token = form_response.cookies["csrf_token"]

    with patch(
        "movielibrary.routers.pages.auth.send_welcome_email",
        new_callable=AsyncMock,
    ):
        client.cookies.set("csrf_token", csrf_token)
        response = await client.post(
            "/register",
            data={
                "email": "alice@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
                "csrf_token": csrf_token,
            },
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_register_password_mismatch(client):
    form_response = await client.get("/register")
    csrf_token = form_response.cookies["csrf_token"]
    client.cookies.set("csrf_token", csrf_token)
    response = await client.post(
        "/register",
        data={
            "email": "alice@example.com",
            "password": "secret123",
            "confirm_password": "other-password",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "error=" in location
    assert "Пароли" in location or "paroli" in location.lower() or "%D0%" in location


@pytest.mark.asyncio
async def test_register_duplicate_email(client, db_session):
    from movielibrary.auth_utils import get_password_hash
    from tests.helpers import create_user

    user = create_user(
        email="alice@example.com",
        password_hash=get_password_hash("secret123"),
    )
    db_session.add(user)
    await db_session.commit()

    form_response = await client.get("/register")
    csrf_token = form_response.cookies["csrf_token"]
    client.cookies.set("csrf_token", csrf_token)
    response = await client.post(
        "/register",
        data={
            "email": "alice@example.com",
            "password": "secret123",
            "confirm_password": "secret123",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "error=" in response.headers["location"]


@pytest.mark.asyncio
async def test_login_success(client, db_session):
    user = create_user(
        email="alice@example.com",
        password_hash=get_password_hash("secret123"),
    )
    db_session.add(user)
    await db_session.commit()

    form_response = await client.get("/login")
    csrf_token = form_response.cookies["csrf_token"]
    client.cookies.set("csrf_token", csrf_token)

    response = await client.post(
        "/login",
        data={
            "email": "alice@example.com",
            "password": "secret123",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client, db_session):
    user = create_user(
        email="alice@example.com",
        password_hash=get_password_hash("secret123"),
    )
    db_session.add(user)
    await db_session.commit()

    form_response = await client.get("/login")
    csrf_token = form_response.cookies["csrf_token"]
    client.cookies.set("csrf_token", csrf_token)

    response = await client.post(
        "/login",
        data={
            "email": "alice@example.com",
            "password": "wrong-password",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    location = unquote(response.headers["location"])
    assert "error=" in location
    assert "Неверный email или пароль" in location


@pytest.mark.asyncio
async def test_login_user_not_found(client):
    form_response = await client.get("/login")
    csrf_token = form_response.cookies["csrf_token"]
    client.cookies.set("csrf_token", csrf_token)

    response = await client.post(
        "/login",
        data={
            "email": "nobody@example.com",
            "password": "secret123",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    location = unquote(response.headers["location"])
    assert "error=" in location


@pytest.mark.asyncio
async def test_account_page_requires_login_or_shows_guest(client):
    response = await client.get("/account")
    assert response.status_code in (200, 302, 303)


@pytest.mark.asyncio
async def test_account_page_for_logged_in_user(client, db_session):
    await login_user(client, db_session, email="alice@example.com")

    response = await client.get("/account")

    assert response.status_code == 200
    assert "alice@example.com" in response.text


@pytest.mark.asyncio
async def test_logout(client, db_session):
    await login_user(
        client,
        db_session,
        email="logout-user@example.com",
        password="secret123",
    )

    account_response = await client.get("/account")
    assert account_response.status_code == 200

    csrf_token = account_response.cookies.get("csrf_token")
    assert csrf_token is not None

    client.cookies.delete("csrf_token")
    client.cookies.set("csrf_token", csrf_token)

    response = await client.post(
        "/logout",
        data={"csrf_token": csrf_token},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"

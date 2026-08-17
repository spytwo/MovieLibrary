from unittest.mock import AsyncMock, patch

import pytest

from movielibrary.services.notification import NotificationService
from tests.helpers import create_user


@pytest.mark.asyncio
async def test_send_new_movie_notification_sends_email_when_users_exist(db_session):
    users = [
        create_user(email="alice1@example.com"),
        create_user(email="alice2@example.com"),
    ]
    db_session.add_all(users)
    await db_session.commit()

    service = NotificationService(db_session)

    with patch(
        "movielibrary.services.notification.send_movie_alert",
        new_callable=AsyncMock,
    ) as mock_send:
        await service.send_new_movie_notification("Inception")

        mock_send.assert_awaited_once_with(
            ["alice1@example.com", "alice2@example.com"],
            "Inception",
        )


@pytest.mark.asyncio
async def test_send_new_movie_notification_does_nothing_when_no_users(db_session):
    service = NotificationService(db_session)

    with patch(
        "movielibrary.services.notification.send_movie_alert",
        new_callable=AsyncMock,
    ) as mock_send:
        await service.send_new_movie_notification("Inception")

        mock_send.assert_not_awaited()

import asyncio
from email.mime.text import MIMEText

import aiosmtplib

from movielibrary.settings import settings


async def _send_base_email(to_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = f'"FilmLibrary" <{settings.email}>'
    msg["To"] = to_email
    msg["Subject"] = subject

    await aiosmtplib.send(
        msg,
        sender=settings.email,
        recipients=[to_email],
        hostname="smtp.yandex.ru",
        port=465,
        username=settings.email,
        password=settings.email_app_password,
        use_tls=True,
    )


async def send_movie_alert(
    receiver_emails: list[str],
    movie_title: str,
) -> None:
    text = f"Мы посмотрели новый фильм: {movie_title}"

    await asyncio.gather(
        *[
            _send_base_email(
                email,
                "Привет от FilmLibrary!",
                text,
            )
            for email in receiver_emails
        ],
        return_exceptions=True,
    )


async def send_password_reset(
    receiver_email: str,
    new_password: str,
) -> None:
    text = f"""Здравствуйте!

Ваш пароль на FilmLibrary был сброшен.

🔑 Новый пароль: {new_password}

Рекомендуем изменить его сразу после входа в аккаунт.

С уважением,
Команда FilmLibrary"""

    await _send_base_email(
        receiver_email,
        "Восстановление пароля — FilmLibrary",
        text,
    )

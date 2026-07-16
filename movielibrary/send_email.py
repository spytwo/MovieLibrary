from email.mime.text import MIMEText

import aiosmtplib

from settings import settings

sender_email = settings.email
password = settings.email_app_password


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
        username=sender_email,
        password=password,
        use_tls=True,
    )


async def send_movie_alert(movie_title: str):
    receiver_emails = [
        email.strip() for email in settings.receiver_emails.split(",") if email.strip()
    ]
    for email in receiver_emails:
        text = f"Мы посмотрели новый фильм: {movie_title}"
        await _send_base_email(email, "Привет от FilmLibrary!", text)


async def send_password_reset(receiver_email: str, new_password: str = "456321"):
    text = f"Пароль для входа: {new_password}"
    await _send_base_email(receiver_email, "Восстановление пароля", text)

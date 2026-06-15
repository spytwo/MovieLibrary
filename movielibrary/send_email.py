from email.mime.text import MIMEText

import aiosmtplib

from settings import settings

sender_email = settings.email
password = settings.email_app_password
receiver_emails = [
    email.strip() for email in settings.receiver_emails.split(",") if email.strip()
]


async def send_email_async(title: str) -> None:
    for receiver_email in receiver_emails:
        text = f"Мы посмотрели новый фильм: {title}"
        msg = MIMEText(text, "plain")
        msg["From"] = f'"FilmLibrary" <{sender_email}>'
        msg["To"] = receiver_email
        msg["Subject"] = "Привет от FilmLibrary!"

        await aiosmtplib.send(
            msg,
            sender=sender_email,
            recipients=[receiver_email],
            hostname="smtp.yandex.ru",
            port=465,
            username=sender_email,
            password=password,
            use_tls=True,
        )

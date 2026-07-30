from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.repositories.user import UserRepository
from movielibrary.send_email import send_movie_alert


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.user_repository = UserRepository(db)

    async def send_new_movie_notification(self, movie_title: str) -> None:
        receiver_emails = await self.user_repository.get_receiver_emails()

        if receiver_emails:
            await send_movie_alert(receiver_emails, movie_title)

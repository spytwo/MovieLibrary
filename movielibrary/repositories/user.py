from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_receiver_emails(self) -> list[str]:
        result = await self.session.execute(select(User.email))
        return list(result.scalars())

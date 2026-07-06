from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.models import Genre


class GenreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> list[Genre]:
        stmt = select(Genre)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_names(self) -> list[str]:
        genres = await self.get_all()
        return [g.name for g in genres]

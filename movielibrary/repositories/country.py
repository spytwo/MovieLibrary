from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.models import Country


class CountryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> list[Country]:
        stmt = select(Country)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_names(self) -> list[str]:
        countries = await self.get_all()
        return [c.name for c in countries]

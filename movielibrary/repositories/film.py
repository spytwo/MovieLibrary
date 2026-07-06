from typing import Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from movielibrary.models import Country, Film, FilmCountry, FilmGenre, Genre


class FilmRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.common_options = [
            selectinload(Film.genres).selectinload(FilmGenre.genre),
            selectinload(Film.countries).selectinload(FilmCountry.country),
        ]

    async def get_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
        film_type: str | None = None,
    ) -> Sequence[Film]:
        stmt = select(Film).options(*self.common_options).order_by(desc(Film.id))
        if film_type:
            stmt = stmt.filter(Film.type == film_type)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.db.execute(stmt)
        return result.unique().scalars().all()

    async def get_by_id(self, film_id: int) -> Film | None:
        stmt = select(Film).options(*self.common_options).filter(Film.id == film_id)
        result = await self.db.execute(stmt)
        return result.unique().scalars().first()

    async def search_by_title(
        self, q: str, limit: int = 5, offset: int = 0
    ) -> Sequence[Film]:
        stmt = (
            select(Film)
            .options(*self.common_options)
            .filter(Film.title.ilike(f"%{q}%"))
            .order_by(desc(Film.id))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count_by_query(
        self, q: str | None = None, film_type: str | None = None
    ) -> int:
        stmt = select(func.count(Film.id.distinct())).select_from(Film)
        if q:
            stmt = stmt.filter(Film.title.ilike(f"%{q}%"))
        if film_type:
            stmt = stmt.filter(Film.type == film_type)

        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_by_genre(self, genre_name: str) -> int:
        stmt = (
            select(func.count(Film.id.distinct()))
            .select_from(Film)
            .join(Film.genres)
            .join(FilmGenre.genre)
            .filter(Genre.name == genre_name)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_by_country(self, country_name: str) -> int:
        stmt = (
            select(func.count(Film.id.distinct()))
            .select_from(Film)
            .join(Film.countries)
            .join(FilmCountry.country)
            .filter(Country.name == country_name)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_by_year(self, year: int) -> int:
        stmt = select(func.count()).select_from(Film).filter(Film.year == year)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_by_genre(
        self, genre_name: str, limit: int | None = None, offset: int | None = None
    ) -> Sequence[Film]:
        stmt = (
            select(Film)
            .options(*self.common_options)
            .join(Film.genres)
            .join(FilmGenre.genre)
            .filter(Genre.name == genre_name)
            .order_by(desc(Film.id))
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_country(
        self, country_name: str, limit: int | None = None, offset: int | None = None
    ) -> Sequence[Film]:
        stmt = (
            select(Film)
            .options(*self.common_options)
            .join(Film.countries)
            .join(FilmCountry.country)
            .filter(Country.name == country_name)
            .order_by(desc(Film.id))
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_year(
        self, year: int, limit: int | None = None, offset: int | None = None
    ) -> Sequence[Film]:
        stmt = (
            select(Film)
            .options(*self.common_options)
            .filter(Film.year == year)
            .order_by(desc(Film.id))
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_global_statistics(self) -> dict:
        count_res = await self.db.execute(select(func.count(Film.id)))
        avg_res = await self.db.execute(select(func.avg(Film.rating)))
        return {
            "total_films": count_res.scalar() or 0,
            "average_rating": round(avg_res.scalar() or 0.0, 2),
        }

    async def create(
        self, film: Film, genre_ids: list[int], country_ids: list[int]
    ) -> Film:
        self.db.add(film)
        await self.db.flush()  # Получаем ID сгенерированного фильма

        for g_id in genre_ids:
            self.db.add(FilmGenre(film_id=film.id, genre_id=g_id))
        for c_id in country_ids:
            self.db.add(FilmCountry(film_id=film.id, country_id=c_id))

        await self.db.commit()
        await self.db.refresh(film)
        return film

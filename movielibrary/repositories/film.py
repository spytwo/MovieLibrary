from typing import Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from movielibrary.models import Country, Film, FilmCountry, FilmGenre, Genre


class FilmRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.common_options = (
            selectinload(Film.genres).selectinload(FilmGenre.genre),
            selectinload(Film.countries).selectinload(FilmCountry.country),
        )

    def _apply_pagination(
        self, stmt, limit: int | None = None, offset: int | None = None
    ):
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        return stmt

    async def count(
        self,
        q: str | None = None,
        film_type: str | None = None,
        genre_name: str | None = None,
        country_name: str | None = None,
        year: int | None = None,
        rating: float | None = None,
    ) -> int:

        stmt = select(func.count(Film.id.distinct())).select_from(Film)

        if q:
            stmt = stmt.filter(Film.title.ilike(f"%{q}%"))
        if film_type:
            stmt = stmt.filter(Film.type == film_type)
        if year is not None:
            stmt = stmt.filter(Film.year == year)
        if rating is not None:
            stmt = stmt.filter(Film.rating.between(rating - 0.01, rating + 0.01))

        if genre_name:
            stmt = (
                stmt.join(Film.genres)
                .join(FilmGenre.genre)
                .filter(Genre.name == genre_name)
            )
        if country_name:
            stmt = (
                stmt.join(Film.countries)
                .join(FilmCountry.country)
                .filter(Country.name == country_name)
            )

        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_multi(
        self,
        limit: int | None = None,
        offset: int | None = None,
        q: str | None = None,
        film_type: str | None = None,
        genre_name: str | None = None,
        country_name: str | None = None,
        year: int | None = None,
        rating: float | None = None,
    ) -> Sequence[Film]:
        stmt = select(Film).options(*self.common_options).order_by(desc(Film.id))

        if q:
            stmt = stmt.filter(Film.title.ilike(f"%{q}%"))
        if film_type:
            stmt = stmt.filter(Film.type == film_type)
        if year is not None:
            stmt = stmt.filter(Film.year == year)
        if rating is not None:
            stmt = stmt.filter(Film.rating.between(rating - 0.01, rating + 0.01))

        if genre_name:
            stmt = (
                stmt.join(Film.genres)
                .join(FilmGenre.genre)
                .filter(Genre.name == genre_name)
            )
        if country_name:
            stmt = (
                stmt.join(Film.countries)
                .join(FilmCountry.country)
                .filter(Country.name == country_name)
            )

        stmt = self._apply_pagination(stmt, limit, offset)
        result = await self.db.execute(stmt)

        return result.unique().scalars().all()

    async def get_by_id(self, film_id: int) -> Film | None:
        stmt = select(Film).options(*self.common_options).filter(Film.id == film_id)
        result = await self.db.execute(stmt)
        return result.unique().scalars().first()

    async def get_global_statistics(self) -> dict:
        stmt = select(func.count(Film.id), func.avg(Film.rating))
        result = await self.db.execute(stmt)
        total_films, average_rating = result.one()

        return {
            "total_films": total_films or 0,
            "average_rating": round(float(average_rating or 0.0), 2),
        }

    async def create(
        self, film: Film, genre_ids: list[int], country_ids: list[int]
    ) -> Film:

        self.db.add(film)
        await self.db.flush()

        relations = []
        if genre_ids:
            relations.extend(
                FilmGenre(film_id=film.id, genre_id=g_id) for g_id in genre_ids
            )
        if country_ids:
            relations.extend(
                FilmCountry(film_id=film.id, country_id=c_id) for c_id in country_ids
            )

        if relations:
            self.db.add_all(relations)

        await self.db.commit()
        await self.db.refresh(film)
        return film

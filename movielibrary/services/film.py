from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.models import Film
from movielibrary.models.enums import MediaType
from movielibrary.repositories.film import FilmRepository
from movielibrary.schemas.film import FilmCreate


class FilmService:
    def __init__(self, db: AsyncSession):
        self.repo = FilmRepository(db)

    async def get_films_list(self, film_type: str | None = None) -> list[Film]:
        return list(await self.repo.get_all(film_type=film_type))

    async def get_film_by_id(self, film_id: int) -> Film:
        film = await self.repo.get_by_id(film_id)
        if not film:
            raise HTTPException(status_code=404, detail="Фильм не найден")
        return film

    async def search_films_by_title(self, q: str) -> list[Film]:
        return list(await self.repo.search_by_title(q, limit=100))

    async def get_statistics(self) -> dict:
        return await self.repo.get_global_statistics()

    async def get_latest_films_for_index(self, limit: int = 5) -> list[Film]:
        return list(await self.repo.get_all(limit=limit))

    async def get_paginated_series(
        self, page: int, page_size: int = 5
    ) -> tuple[list[Film], int]:
        offset = (page - 1) * page_size
        total_films = await self.repo.count_by_type(film_type="series")
        films = await self.repo.get_all(
            limit=page_size, offset=offset, film_type="series"
        )
        total_pages = (total_films + page_size - 1) // page_size
        return list(films), total_pages

    async def get_paginated_search(
        self, q: str | None, page: int, page_size: int = 5
    ) -> tuple[list[Film], int]:
        if not q or len(q) < 3:
            return [], 0

        offset = (page - 1) * page_size
        total_films = await self.repo.count_by_query(q=q)
        films = await self.repo.search_by_title(q=q, limit=page_size, offset=offset)
        total_pages = (total_films + page_size - 1) // page_size
        return list(films), total_pages

    async def create_new_film(
        self, payload: FilmCreate, genre_ids: list[int], country_ids: list[int]
    ) -> Film:
        title = payload.title
        if payload.type != MediaType.movie:
            title += " (Сериал)"

        new_film = Film(
            title=title,
            year=payload.year,
            description=payload.description,
            rating=payload.rating,
            photo=payload.photo,
            type=payload.type,
        )

        try:
            return await self.repo.create(new_film, genre_ids, country_ids)
        except Exception:
            raise HTTPException(
                status_code=500, detail="Ошибка при создании фильма"
            ) from None

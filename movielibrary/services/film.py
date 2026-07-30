from fastapi import HTTPException
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.cache.keys import key_builder
from movielibrary.mappers.film import film_to_read, films_to_read
from movielibrary.models import Film
from movielibrary.models.enums import MediaType
from movielibrary.repositories.film import FilmRepository
from movielibrary.schemas.film import FilmCreate, FilmRead


class FilmService:
    def __init__(self, db: AsyncSession):
        self.repo = FilmRepository(db)

    @cache(expire=360, key_builder=key_builder)
    async def get_film_by_id(self, film_id: int) -> FilmRead:
        film = await self.repo.get_by_id(film_id)

        if not film:
            raise HTTPException(
                status_code=404,
                detail="Фильм не найден",
            )

        return film_to_read(film)

    @cache(expire=360, key_builder=key_builder)
    async def get_statistics(self) -> dict:
        return await self.repo.get_global_statistics()

    @cache(expire=360, key_builder=key_builder)
    async def get_films_list(self, **filters) -> list[FilmRead]:
        films = await self.repo.get_multi(**filters)
        return films_to_read(list(films))

    async def get_latest_films_for_index(self, limit: int = 5) -> list[FilmRead]:
        films = await self.repo.get_multi(limit=limit)
        return films_to_read(list(films))

    @cache(expire=360, key_builder=key_builder)
    async def get_paginated_films(
        self, page: int, page_size: int = 5, **filters
    ) -> tuple[list[FilmRead], int]:

        q = filters.get("q")
        if q is not None and len(q) < 3:
            return [], 0

        offset = (page - 1) * page_size

        total_films = await self.repo.count(**filters)
        films = await self.repo.get_multi(
            limit=page_size,
            offset=offset,
            **filters,
        )

        total_pages = (total_films + page_size - 1) // page_size

        return films_to_read(list(films)), total_pages

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

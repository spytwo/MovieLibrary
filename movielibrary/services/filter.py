from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.models import Film
from movielibrary.repositories.country import CountryRepository
from movielibrary.repositories.film import FilmRepository
from movielibrary.repositories.genre import GenreRepository


class FilterService:
    def __init__(self, db: AsyncSession):
        self.film_repo = FilmRepository(db)
        self.genre_repo = GenreRepository(db)
        self.country_repo = CountryRepository(db)

    async def get_genres_list(self) -> list[str]:
        return await self.genre_repo.get_all_names()

    async def get_countries_list(self) -> list[str]:
        return await self.country_repo.get_all_names()

    async def filter_films_by_genre(self, genre_name: str) -> list[Film]:
        return list(await self.film_repo.get_by_genre(genre_name))

    async def filter_films_by_country(self, country_name: str) -> list[Film]:
        return list(await self.film_repo.get_by_country(country_name))

    async def filter_films_by_year(self, year: int) -> list[Film]:
        return list(await self.film_repo.get_by_year(year))

    async def get_paginated_by_genre(
        self, genre_name: str, page: int, page_size: int = 5
    ) -> tuple[list[Film], int]:
        offset = (page - 1) * page_size
        total_films = await self.film_repo.count_by_genre(genre_name)
        films = await self.film_repo.get_by_genre(
            genre_name, limit=page_size, offset=offset
        )
        total_pages = (total_films + page_size - 1) // page_size
        return list(films), total_pages

    async def get_paginated_by_country(
        self, country_name: str, page: int, page_size: int = 5
    ) -> tuple[list[Film], int]:
        offset = (page - 1) * page_size
        total_films = await self.film_repo.count_by_country(country_name)
        films = await self.film_repo.get_by_country(
            country_name, limit=page_size, offset=offset
        )
        total_pages = (total_films + page_size - 1) // page_size
        return list(films), total_pages

    async def get_paginated_by_year(
        self, year: int, page: int, page_size: int = 5
    ) -> tuple[list[Film], int]:
        offset = (page - 1) * page_size
        total_films = await self.film_repo.count_by_year(year)
        films = await self.film_repo.get_by_year(year, limit=page_size, offset=offset)
        total_pages = (total_films + page_size - 1) // page_size
        return list(films), total_pages

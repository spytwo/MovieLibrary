from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.database import get_db
from movielibrary.schemas.film import FilmRead
from movielibrary.services.film import FilmService
from movielibrary.services.filter import FilterService

router = APIRouter()


@router.get(
    "/genres", summary="List Genres", description="Возвращает список всех жанров"
)
async def list_genres(db: AsyncSession = Depends(get_db)):
    service = FilterService(db)
    return await service.get_genres_list()


@router.get(
    "/countries", summary="List Countries", description="Возвращает список всех стран"
)
async def list_countries(db: AsyncSession = Depends(get_db)):
    service = FilterService(db)
    return await service.get_countries_list()


@router.get(
    "/genres/{genre_name}",
    response_model=List[FilmRead],
    summary="List Films By Genre",
    description="Возвращает список всех фильмов, отфильтрованными по выбранному жанру",
)
async def read_films_by_genre(genre_name: str, db: AsyncSession = Depends(get_db)):
    service = FilterService(db)
    films = await service.filter_films_by_genre(genre_name)
    return [FilmRead.model_validate(film) for film in films]


@router.get(
    "/countries/{country_name}",
    response_model=List[FilmRead],
    summary="List Films By Country",
    description="Возвращает список всех фильмов, отфильтрованными по выбранной стране",
)
async def read_films_by_country(country_name: str, db: AsyncSession = Depends(get_db)):
    service = FilterService(db)
    films = await service.filter_films_by_country(country_name)
    return [FilmRead.model_validate(film) for film in films]


@router.get(
    "/years/{year}",
    response_model=List[FilmRead],
    summary="List Films By Year",
    description="Возвращает список всех фильмов, отфильтрованными по выбранному году выпуска",
)
async def read_films_by_year(year: int, db: AsyncSession = Depends(get_db)):
    service = FilterService(db)
    films = await service.filter_films_by_year(year)
    return [FilmRead.model_validate(film) for film in films]


@router.get(
    "/series",
    response_model=List[FilmRead],
    summary="List Films",
    description="Возвращает список всех сериалов с жанрами и странами",
)
async def list_series(db: AsyncSession = Depends(get_db)):
    service = FilmService(db)
    return await service.get_films_list(film_type="series")

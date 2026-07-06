from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.database import get_db
from movielibrary.schemas.film import FilmRead, FilmSearchResult
from movielibrary.services.film import FilmService

router = APIRouter()


@router.get(
    "",
    response_model=list[FilmRead],
    summary="List Films",
    description="Возвращает список всех фильмов с жанрами и странами",
)
async def list_films(db: AsyncSession = Depends(get_db)):
    service = FilmService(db)
    return await service.get_films_list()


@router.get(
    "/search",
    response_model=list[FilmSearchResult],
    summary="Search Films by Title",
    description="Позволяет искать фильмы по названию (частичное совпадение)",
)
async def search_films(
    q: str = Query(..., min_length=3, description="Название фильма"),
    db: AsyncSession = Depends(get_db),
):
    service = FilmService(db)
    return await service.search_films_by_title(q)


@router.get(
    "/statistics",
    response_model=dict[str, float],
    summary="Get films statistics",
    description="Показывает общую информацию о библиотеке фильмов",
)
async def get_films_statistics(db: AsyncSession = Depends(get_db)):
    service = FilmService(db)
    return await service.get_statistics()


@router.get(
    "/{film_id}",
    response_model=FilmRead,
    summary="Retrieve Film",
    description="Возвращает подробную информацию о фильме по его ID, включая жанры и страны",
)
async def retrieve_film(film_id: int, db: AsyncSession = Depends(get_db)):
    service = FilmService(db)
    return await service.get_film_by_id(film_id)

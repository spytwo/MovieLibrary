from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.database import get_db
from movielibrary.schemas.film import FilmRead
from movielibrary.services.film import FilmService

router = APIRouter()


@router.get(
    "",
    response_model=list[FilmRead],
    summary="List and Filter Films",
    description="Возвращает список фильмов с возможностью фильтрации по жанру, стране, году, рейтингу и поисковому запросу.",
)
async def list_films(
    q: str | None = Query(None, min_length=3, description="Поиск по названию"),
    film_type: str | None = Query(None, description="Тип (movie или series)"),
    genre: str | None = Query(None, description="Фильтр по названию жанра"),
    country: str | None = Query(None, description="Фильтр по названию страны"),
    year: int | None = Query(None, description="Фильтр по году выпуска"),
    rating: float | None = Query(None, description="Фильтр по рейтингу"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
):
    service = FilmService(db)

    offset = (page - 1) * page_size

    return await service.repo.get_multi(
        limit=page_size,
        offset=offset,
        q=q,
        film_type=film_type,
        genre_name=genre,
        country_name=country,
        year=year,
        rating=rating,
    )


@router.get(
    "/statistics",
    response_model=dict[str, float],
    summary="Get films statistics",
)
async def get_films_statistics(db: AsyncSession = Depends(get_db)):
    service = FilmService(db)
    return await service.get_statistics()


@router.get(
    "/{film_id}",
    response_model=FilmRead,
    summary="Retrieve Film",
)
async def retrieve_film(film_id: int, db: AsyncSession = Depends(get_db)):
    service = FilmService(db)
    return await service.get_film_by_id(film_id)

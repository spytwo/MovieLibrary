from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.database import get_db
from movielibrary.schemas.film import FilmRead
from movielibrary.services.film import FilmService

router = APIRouter()


@router.get(
    "",
    response_model=list[FilmRead],
    summary="List and Filter Films",
)
async def list_films(
    q: str | None = Query(None, min_length=3),
    film_type: str | None = Query(None),
    genre: str | None = Query(None),
    country: str | None = Query(None),
    year: int | None = Query(None),
    rating: float | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = FilmService(db)

    offset = (page - 1) * page_size

    return await service.get_films_list(
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
async def get_films_statistics(request: Request, db: AsyncSession = Depends(get_db)):
    service = FilmService(db)
    return await service.get_statistics()


@router.get(
    "/{film_id}",
    response_model=FilmRead,
    summary="Retrieve Film",
)
async def retrieve_film(
    request: Request, film_id: int, db: AsyncSession = Depends(get_db)
):
    service = FilmService(db)
    return await service.get_film_by_id(film_id)

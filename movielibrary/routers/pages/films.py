from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.auth_utils import get_current_user_optional
from movielibrary.database import get_db
from movielibrary.models import User
from movielibrary.repositories.genre import GenreRepository
from movielibrary.schemas.film import FilmRead
from movielibrary.services.film import FilmService
from movielibrary.settings import settings

router = APIRouter(tags=["Film Pages"])
templates = Jinja2Templates(directory="movielibrary/templates")


@router.get("/", response_class=HTMLResponse)
async def read_films(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    film_service = FilmService(db)
    genre_repo = GenreRepository(db)
    films = await film_service.get_latest_films_for_index(limit=5)
    genres_for_template = await genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": films,
            "genres": genres_for_template,
            "page": 1,
            "total_pages": 1,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get("/series")
async def list_series(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = 5,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    film_service = FilmService(db)
    genre_repo = GenreRepository(db)
    films, total_pages = await film_service.get_paginated_films(
        page=page, page_size=page_size, film_type="series"
    )
    genres_for_template = await genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": films,
            "genres": genres_for_template,
            "page": page,
            "total_pages": total_pages,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get("/search", response_class=HTMLResponse)
async def search_films(
    request: Request,
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = 5,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    film_service = FilmService(db)
    genre_repo = GenreRepository(db)
    films, total_pages = await film_service.get_paginated_films(
        page=page, page_size=page_size, q=q
    )
    genres_for_template = await genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": films,
            "genres": genres_for_template,
            "page": page,
            "total_pages": total_pages,
            "query": q or "",
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get("/rating/{rating}", response_class=HTMLResponse)
async def read_films_by_rating_page(
    rating: float,
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = 5,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    film_service = FilmService(db)
    genre_repo = GenreRepository(db)
    films, total_pages = await film_service.get_paginated_films(
        page=page, page_size=page_size, rating=rating
    )
    genres_for_template = await genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": films,
            "genres": genres_for_template,
            "page": page,
            "total_pages": total_pages,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get("/genres/{genre_name}", response_class=HTMLResponse)
async def read_films_by_genre(
    genre_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = 5,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    film_service = FilmService(db)
    genre_repo = GenreRepository(db)
    films, total_pages = await film_service.get_paginated_films(
        page=page, page_size=page_size, genre_name=genre_name
    )
    genres_for_template = await genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": films,
            "genres": genres_for_template,
            "page": page,
            "total_pages": total_pages,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get("/countries/{country_name}", response_class=HTMLResponse)
async def read_films_by_country(
    country_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = 5,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    film_service = FilmService(db)
    genre_repo = GenreRepository(db)
    films, total_pages = await film_service.get_paginated_films(
        page=page, page_size=page_size, country_name=country_name
    )
    genres_for_template = await genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": films,
            "genres": genres_for_template,
            "page": page,
            "total_pages": total_pages,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get("/years/{year}", response_class=HTMLResponse)
async def read_films_by_year(
    year: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = 5,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    film_service = FilmService(db)
    genre_repo = GenreRepository(db)
    films, total_pages = await film_service.get_paginated_films(
        page=page, page_size=page_size, year=year
    )
    genres_for_template = await genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": films,
            "genres": genres_for_template,
            "page": page,
            "total_pages": total_pages,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get("/film/{id}", response_class=HTMLResponse)
async def read_film(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    film_service = FilmService(db)
    genre_repo = GenreRepository(db)
    film_data = await film_service.get_film_by_id(id)

    film_schema = FilmRead(**film_data) if isinstance(film_data, dict) else film_data
    genres_for_template = await genre_repo.get_all()

    return templates.TemplateResponse(
        "film_details.html",
        {
            "request": request,
            "film": film_schema,
            "genres": genres_for_template,
            "page_title": film_schema.title,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )

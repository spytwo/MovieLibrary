from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.auth_utils import (
    get_current_user_required,
    get_or_create_csrf_token,
    set_csrf_cookie,
    verify_csrf_token,
)
from movielibrary.database import get_db
from movielibrary.models import User
from movielibrary.models.enums import MediaType
from movielibrary.repositories.country import CountryRepository
from movielibrary.repositories.genre import GenreRepository
from movielibrary.schemas.film import FilmCreate
from movielibrary.services.film import FilmService
from movielibrary.services.notification import NotificationService
from movielibrary.settings import settings

router = APIRouter(tags=["Admin Pages"])
templates = Jinja2Templates(directory="movielibrary/templates")


@router.get("/create", response_class=HTMLResponse)
async def show_create_film_form(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    genre_repo = GenreRepository(db)
    country_repo = CountryRepository(db)
    genre_list = await genre_repo.get_all()
    country_list = await country_repo.get_all()

    csrf_token = get_or_create_csrf_token(request)
    response = templates.TemplateResponse(
        "create.html",
        {
            "request": request,
            "genre_list": genre_list,
            "country_list": country_list,
            "user_email": current_user.email,
            "csrf_token": csrf_token,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


@router.post("/create")
async def create_film(
    request: Request,
    background_tasks: BackgroundTasks,
    title: str = Form(..., min_length=1),
    year: int = Form(..., ge=1895),
    rating: float = Form(..., ge=0, le=10),
    description: str = Form(""),
    photo: str = Form(""),
    code: str = Form(...),
    genres: List[int] = Form([]),
    countries: List[int] = Form([]),
    type: str = Form(...),
    csrf_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    verify_csrf_token(request, csrf_token)

    if code != settings.valid_code:
        raise HTTPException(status_code=400, detail="Неверный код доступа")

    try:
        media_type = MediaType(type)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Недопустимый тип контента"
        ) from None

    try:
        film_schema = FilmCreate(
            title=title,
            year=year,
            description=description,
            rating=rating,
            photo=photo,
            type=media_type,
        )
    except ValidationError:
        raise HTTPException(
            status_code=400, detail="Ошибка заполнения полей формы"
        ) from None

    film_service = FilmService(db)
    new_film = await film_service.create_new_film(film_schema, genres, countries)

    notification_service = NotificationService(db)
    background_tasks.add_task(
        notification_service.send_new_movie_notification,
        new_film.title,
    )
    return RedirectResponse(url="/", status_code=302)

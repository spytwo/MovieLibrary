from datetime import datetime
from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.auth_utils import (
    create_access_token,
    get_current_user_optional,
    get_current_user_required,
    get_password_hash,
    get_user_by_email,
    verify_password,
)
from movielibrary.database import get_db
from movielibrary.models import User
from movielibrary.models.enums import MediaType
from movielibrary.schemas.film import FilmCreate, FilmRead
from movielibrary.schemas.user import UserCreate
from movielibrary.send_email import send_email_async
from movielibrary.services.film import FilmService
from movielibrary.services.filter import FilterService
from settings import settings

router = APIRouter()
templates = Jinja2Templates(directory="movielibrary/templates")

MINUTE_IN_SECONDS = 60


@router.get("/", response_class=HTMLResponse, summary="Read Films")
async def read_films(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    film_service = FilmService(db)
    filter_service = FilterService(db)

    films = await film_service.get_latest_films_for_index(limit=5)
    genres_for_template = await filter_service.genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": [FilmRead.model_validate(film) for film in films],
            "genres": genres_for_template,
            "page": 1,
            "total_pages": 1,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get("/register", response_class=HTMLResponse, summary="Register Form")
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse, summary="Register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(..., min_length=6),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")

    try:
        user_schema = UserCreate(email=email, password=password)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from None

    existing_user = await get_user_by_email(db, user_schema.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    hashed_password = get_password_hash(user_schema.password)
    new_user = User(email=user_schema.email, password_hash=hashed_password)
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Ошибка при создании пользователя"
        ) from None

    token = create_access_token(email=new_user.email)
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=int(settings.access_token_expire_minutes) * MINUTE_IN_SECONDS,
        path="/",
    )
    return response


@router.get("/login", response_class=HTMLResponse, summary="Login Form")
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse, summary="Login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=400, detail="Пользователя не существует")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неправильный пароль")

    user.last_login = datetime.utcnow()
    await db.commit()

    token = create_access_token(email=user.email)
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=int(settings.access_token_expire_minutes) * MINUTE_IN_SECONDS,
        path="/",
    )
    return response


@router.get("/account", response_class=HTMLResponse, summary="Show Account")
async def account(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    return templates.TemplateResponse(
        "account.html",
        {
            "request": request,
            "user_email": current_user.email if current_user else None,
        },
    )


@router.post(
    "/account/change_password", response_class=HTMLResponse, summary="Change Password"
)
async def change_password(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    old_password: str = Form(...),
    new_password: str = Form(..., min_length=6),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный старый пароль")
    current_user.password_hash = get_password_hash(new_password)
    db.add(current_user)
    await db.commit()
    return templates.TemplateResponse(
        "account.html",
        {
            "request": request,
            "user_email": current_user.email if current_user else None,
            "message": "Пароль успешно изменён",
        },
    )


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token", path="/")
    return response


@router.get(
    "/series",
    summary="List Films with pagination",
    description="Возвращает список всех сериалов с жанрами и странами",
)
async def list_series(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = 5,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    film_service = FilmService(db)
    filter_service = FilterService(db)

    films, total_pages = await film_service.get_paginated_series(page, page_size)
    genres_for_template = await filter_service.genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": [FilmRead.model_validate(film) for film in films],
            "genres": genres_for_template,
            "page": page,
            "total_pages": total_pages,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get("/search", response_class=HTMLResponse, summary="Search Films by Title")
async def search_films(
    request: Request,
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(None, description="Название фильма"),
    page: int = Query(1, ge=1),
    page_size: int = 5,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    film_service = FilmService(db)
    filter_service = FilterService(db)

    films, total_pages = await film_service.get_paginated_search(q, page, page_size)
    genres_for_template = await filter_service.genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": [FilmRead.model_validate(film) for film in films],
            "genres": genres_for_template,
            "page": page,
            "total_pages": total_pages,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get(
    "/rating/{rating}", response_class=HTMLResponse, summary="Read Films By Rating"
)
async def read_films_by_rating_page(
    rating: float,
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = 5,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    filter_service = FilterService(db)

    films, total_pages = await filter_service.get_paginated_by_rating(
        rating, page, page_size
    )
    genres_for_template = await filter_service.genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": [FilmRead.model_validate(film) for film in films],
            "genres": genres_for_template,
            "page": page,
            "total_pages": total_pages,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get(
    "/genres/{genre_name}", response_class=HTMLResponse, summary="Read Films By Genre"
)
async def read_films_by_genre(
    genre_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = 5,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    filter_service = FilterService(db)

    films, total_pages = await filter_service.get_paginated_by_genre(
        genre_name, page, page_size
    )
    genres_for_template = await filter_service.genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": [FilmRead.model_validate(film) for film in films],
            "genres": genres_for_template,
            "page": page,
            "total_pages": total_pages,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get(
    "/countries/{country_name}",
    response_class=HTMLResponse,
    summary="Read Films By Country",
)
async def read_films_by_country(
    country_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = 5,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    filter_service = FilterService(db)

    films, total_pages = await filter_service.get_paginated_by_country(
        country_name, page, page_size
    )
    genres_for_template = await filter_service.genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": [FilmRead.model_validate(film) for film in films],
            "genres": genres_for_template,
            "page": page,
            "total_pages": total_pages,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get("/years/{year}", response_class=HTMLResponse, summary="Read Films By Year")
async def read_films_by_year(
    year: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = 5,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    filter_service = FilterService(db)

    films, total_pages = await filter_service.get_paginated_by_year(
        year, page, page_size
    )
    genres_for_template = await filter_service.genre_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "films": [FilmRead.model_validate(film) for film in films],
            "genres": genres_for_template,
            "page": page,
            "total_pages": total_pages,
            "user_email": current_user.email if current_user else None,
            "cdn": settings.cdn,
        },
    )


@router.get("/film/{id}", response_class=HTMLResponse, summary="Read Film By Id")
async def read_film(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    film_service = FilmService(db)
    filter_service = FilterService(db)

    film = await film_service.get_film_by_id(id)
    film_schema = FilmRead.model_validate(film)
    genres_for_template = await filter_service.genre_repo.get_all()

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


@router.get("/create", response_class=HTMLResponse, summary="Show Create Film Form")
async def show_create_film_form(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    filter_service = FilterService(db)

    genre_list = await filter_service.genre_repo.get_all()
    country_list = await filter_service.country_repo.get_all()

    return templates.TemplateResponse(
        "create.html",
        {
            "request": request,
            "genre_list": genre_list,
            "country_list": country_list,
            "user_email": current_user.email,
        },
    )


@router.post("/create", summary="Create Film")
async def create_film(
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
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
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from None

    film_service = FilmService(db)
    new_film = await film_service.create_new_film(film_schema, genres, countries)

    background_tasks.add_task(send_email_async, new_film.title)
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.auth_utils import (
    create_access_token,
    generate_temporary_password,
    get_current_user_optional,
    get_current_user_required,
    get_or_create_csrf_token,
    get_password_hash,
    get_user_by_email,
    set_csrf_cookie,
    verify_csrf_token,
    verify_password,
)
from movielibrary.database import get_db
from movielibrary.models import User
from movielibrary.schemas.user import UserCreate
from movielibrary.send_email import send_password_reset, send_welcome_email
from movielibrary.settings import settings

router = APIRouter(tags=["Auth Pages"])
templates = Jinja2Templates(directory="movielibrary/templates")
MINUTE_IN_SECONDS = 60


@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    csrf_token = get_or_create_csrf_token(request)
    response = templates.TemplateResponse(
        request, "register.html", {"csrf_token": csrf_token}
    )
    set_csrf_cookie(response, csrf_token)
    return response


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    csrf_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    verify_csrf_token(request, csrf_token)
    if len(password) < 6:
        raise HTTPException(
            status_code=400, detail="Пароль должен содержать минимум 6 символов"
        )
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")

    try:
        user_schema = UserCreate(email=email, password=password)
    except ValidationError:
        raise HTTPException(
            status_code=400, detail="Некорректный email или пароль"
        ) from None

    existing_user = await get_user_by_email(db, user_schema.email)
    if existing_user:
        raise HTTPException(
            status_code=400, detail="Пользователь с таким email уже существует"
        )

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

    background_tasks.add_task(send_welcome_email, new_user.email)
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


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    csrf_token = get_or_create_csrf_token(request)
    response = templates.TemplateResponse(
        request, "login.html", {"csrf_token": csrf_token}
    )
    set_csrf_cookie(response, csrf_token)
    return response


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    verify_csrf_token(request, csrf_token)
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный email или пароль")

    user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
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


@router.get("/forgot_password", response_class=HTMLResponse)
async def forgot_password_form(request: Request):
    csrf_token = get_or_create_csrf_token(request)
    response = templates.TemplateResponse(
        request, "forgot_password.html", {"csrf_token": csrf_token}
    )
    set_csrf_cookie(response, csrf_token)
    return response


@router.post("/forgot_password")
async def forgot_password(
    request: Request,
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    csrf_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    verify_csrf_token(request, csrf_token)
    user = await get_user_by_email(db, email)
    if user:
        new_password = generate_temporary_password()
        user.password_hash = get_password_hash(new_password)
        await db.commit()
        background_tasks.add_task(send_password_reset, email, new_password)

    msg = quote("Если email существует, новый пароль отправлен на почту")
    return RedirectResponse(
        url=f"/login?message={msg}", status_code=status.HTTP_302_FOUND
    )


@router.get("/account", response_class=HTMLResponse)
async def account(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    csrf_token = get_or_create_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "account.html",
        {
            "user_email": current_user.email if current_user else None,
            "csrf_token": csrf_token,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


@router.post("/account/change_password", response_class=HTMLResponse)
async def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    csrf_token: str = Form(...),
    current_user: User = Depends(get_current_user_required),
):
    verify_csrf_token(request, csrf_token)

    if len(new_password) < 6:
        raise HTTPException(
            status_code=400, detail="Новый пароль должен содержать минимум 6 символов"
        )

    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Новые пароли не совпадают")

    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")

    current_user.password_hash = get_password_hash(new_password)
    db.add(current_user)
    await db.commit()

    success_msg = quote("Пароль успешно изменён")
    return RedirectResponse(
        url=f"/account?message={success_msg}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/logout")
async def logout(request: Request, csrf_token: str = Form(...)):
    verify_csrf_token(request, csrf_token)
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("csrf_token", path="/")
    return response

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.database import get_db
from movielibrary.models import User
from settings import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.access_token_expire_minutes)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


def get_password_hash(password: str) -> str:
    """Хэширует пароль с использованием sha256_crypt.
    Args:
        password: Пароль в открытом виде
    Returns:
        Хэшированный пароль
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля хэшу.
    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хэшированный пароль
    Returns:
        True если пароль верный, False если неверный
    """
    return pwd_context.verify(plain_password, hashed_password)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Получает пользователя из базы данных по email.
    Args:
        db: Асинхронная сессия базы данных
        email: Email пользователя для поиска
    Returns:
        User объект если пользователь найден, иначе None
    """
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


def create_access_token(email: str) -> str:
    """
    Создает JWT токен доступа для пользователя.
    Args:
        email: Email пользователя
    Returns:
        Закодированный JWT токен
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data = {"sub": email, "exp": expire, "type": "access"}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """
    Декодирует JWT токен доступа и возвращает email пользователя.
    Args:
        token: JWT токен для декодирования
    Returns:
        Email пользователя из токена
    Raises:
        HTTPException: Если токен недействителен, просрочен или имеет неверный тип
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise JWTError("Invalid token type")
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise JWTError("Missing subject")
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Извлекает токен доступа из cookies запроса.
    Args:
        request: HTTP запрос
    Returns:
        Токен доступа, если найден в cookies, иначе None
    """
    cookie = request.cookies.get("access_token")
    if cookie:
        return cookie
    return None


async def get_current_user_required(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Зависимость, внедряется в маршруты, где нужна обязательная авторизация.
    Проверяет токен авторизации и возвращает объект пользователя.
    Выбрасывает HTTP 401 ошибку если пользователь не авторизован.
    Args:
        request: HTTP запрос
        db: Асинхронная сессия базы данных
    Returns:
        Объект User если авторизация успешна
    Raises:
        HTTPException: 401 если токен отсутствует, недействителен или пользователь не найден
    """
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    email = decode_access_token(token)
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Зависимость, внедряется в маршруты, где не нужна обязательная авторизация.
    Проверяет токен авторизации и возвращает объект пользователя если авторизация успешна.
    Возвращает None если токен отсутствует, недействителен или пользователь не найден.
    Args:
        request: HTTP запрос
        db: Асинхронная сессия базы данных
    Returns:
        Объект User если авторизация успешна, иначе None
    """
    token = get_token_from_request(request)
    if not token:
        return None
    try:
        email = decode_access_token(token)
    except HTTPException:
        return None
    user = await get_user_by_email(db, email)
    return user


def generate_temporary_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))

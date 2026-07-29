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
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


def create_access_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data = {"sub": email, "exp": expire, "type": "access"}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
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
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


def get_token_from_request(request: Request) -> Optional[str]:
    cookie = request.cookies.get("access_token")
    if cookie:
        return cookie
    return None


async def get_current_user_required(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization is required")
    email = decode_access_token(token)
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=401, detail="The user was not found")
    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
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

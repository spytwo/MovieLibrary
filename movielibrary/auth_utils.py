import hashlib
import hmac
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.database import get_db
from movielibrary.models import User
from movielibrary.settings import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.access_token_expire_minutes)
MINUTE_IN_SECONDS = 60

password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


def create_access_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    data = {
        "sub": email,
        "exp": expire,
        "type": "access",
    }

    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")

        email: Optional[str] = payload.get("sub")

        if email is None:
            raise InvalidTokenError("Missing subject")

        return email

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization is required",
        )

    email = decode_access_token(token)

    user = await get_user_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user was not found",
        )

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


def generate_temporary_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_csrf_token() -> str:
    token = secrets.token_urlsafe(32)
    signature = hmac.new(
        settings.secret_key.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()

    return f"{token}.{signature}"


def get_or_create_csrf_token(request: Request) -> str:
    csrf_token = request.cookies.get("csrf_token")

    if csrf_token and validate_csrf_token(csrf_token):
        return csrf_token

    return generate_csrf_token()


def validate_csrf_token(token: str) -> bool:
    try:
        value, signature = token.rsplit(".", 1)
    except ValueError:
        return False

    expected_signature = hmac.new(
        SECRET_KEY.encode(),
        value.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


def set_csrf_cookie(
    response: Response,
    csrf_token: str,
) -> None:
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=False,  # True в production при HTTPS
        samesite="lax",
        max_age=int(settings.access_token_expire_minutes) * MINUTE_IN_SECONDS,
        path="/",
    )


def verify_csrf_token(request: Request, csrf_token: str) -> None:
    cookie_token = request.cookies.get("csrf_token")

    if not cookie_token or not validate_csrf_token(csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )

    if not hmac.compare_digest(cookie_token, csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )

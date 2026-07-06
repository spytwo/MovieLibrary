from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.auth_utils import (
    get_password_hash,
    get_user_by_email,
    verify_password,
)
from movielibrary.models import User
from movielibrary.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, payload: UserCreate) -> User:
        existing_user = await get_user_by_email(self.db, payload.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь уже существует")

        hashed_password = get_password_hash(payload.password)
        new_user = User(email=payload.email, password_hash=hashed_password)

        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user
        except Exception:
            await self.db.rollback()
            raise HTTPException(
                status_code=500, detail="Ошибка при создании пользователя"
            ) from None

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await get_user_by_email(self.db, email)
        if not user:
            raise HTTPException(status_code=400, detail="Пользователя не существует")
        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=400, detail="Неправильный пароль")

        user.last_login = datetime.utcnow()
        await self.db.commit()
        return user

    async def change_user_password(
        self, user: User, old_password: str, new_password: str
    ) -> User:
        if not verify_password(old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Неверный старый пароль")

        user.password_hash = get_password_hash(new_password)
        self.db.add(user)
        await self.db.commit()
        return user

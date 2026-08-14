from datetime import UTC, datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from movielibrary.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    last_login: Mapped[Optional[datetime]] = mapped_column(nullable=True)

from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from movielibrary.models.associations import FilmGenre
from movielibrary.models.base import Base


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    films: Mapped[List["FilmGenre"]] = relationship(
        back_populates="genre", cascade="all, delete-orphan"
    )

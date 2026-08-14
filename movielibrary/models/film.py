from typing import List

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from movielibrary.models.associations import FilmCountry, FilmGenre
from movielibrary.models.base import Base


class Film(Base):
    __tablename__ = "films"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(
        SQLEnum("movie", "series", name="mediatype"), default="movie"
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    photo: Mapped[str] = mapped_column(String, nullable=False)

    genres: Mapped[List["FilmGenre"]] = relationship(
        back_populates="film", cascade="all, delete-orphan", passive_deletes=True
    )
    countries: Mapped[List["FilmCountry"]] = relationship(
        back_populates="film", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def genre_list(self):
        return [fg.genre for fg in self.genres]

    @property
    def country_list(self):
        return [fc.country for fc in self.countries]

    __table_args__ = (
        Index(
            "idx_films_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )

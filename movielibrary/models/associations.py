from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from movielibrary.models.base import Base

if TYPE_CHECKING:
    from .country import Country
    from .film import Film
    from .genre import Genre


class FilmGenre(Base):
    __tablename__ = "film_genre"

    film_id: Mapped[int] = mapped_column(
        ForeignKey("films.id"), primary_key=True
    )  # добавить ondelete="CASCADE", чтобы работало каскадное удаление
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="genres")
    genre: Mapped["Genre"] = relationship(back_populates="films")


class FilmCountry(Base):
    __tablename__ = "film_country"

    film_id: Mapped[int] = mapped_column(ForeignKey("films.id"), primary_key=True)
    country_id: Mapped[int] = mapped_column(
        ForeignKey("countries.id"), primary_key=True
    )

    film: Mapped["Film"] = relationship(back_populates="countries")
    country: Mapped["Country"] = relationship(back_populates="films")

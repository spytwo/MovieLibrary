from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from movielibrary.models.associations import FilmCountry
from movielibrary.models.base import Base


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    films: Mapped[List["FilmCountry"]] = relationship(
        back_populates="country", cascade="all, delete-orphan"
    )

from datetime import datetime

import pytest

from movielibrary.schemas.film import FilmBase


def test_film_rating_accepts_valid_value():
    film = FilmBase(
        title="Test Film",
        year=2020,
        rating=8.5,
    )

    assert film.rating == 8.5


def test_film_rating_rejects_value_above_10():
    with pytest.raises(ValueError):
        FilmBase(
            title="Test Film",
            year=2020,
            rating=11,
        )


def test_film_rating_rejects_value_below_0():
    with pytest.raises(ValueError):
        FilmBase(
            title="Test Film",
            year=2020,
            rating=-1,
        )


def test_film_rating_accepts_zero():
    film = FilmBase(
        title="Test Film",
        year=2020,
        rating=0,
    )

    assert film.rating == 0


def test_film_rating_accepts_ten():
    film = FilmBase(
        title="Test Film",
        year=2020,
        rating=10,
    )

    assert film.rating == 10


def test_film_year_accepts_valid_value():
    film = FilmBase(
        title="Test Film",
        year=2020,
        rating=8.5,
    )

    assert film.year == 2020


def test_film_year_accepts_1888():
    film = FilmBase(
        title="First Film",
        year=1888,
        rating=8.5,
    )

    assert film.year == 1888


def test_film_year_rejects_before_1888():
    with pytest.raises(ValueError):
        FilmBase(
            title="Test Film",
            year=1887,
            rating=8.5,
        )


def test_film_year_accepts_current_year():
    current_year = datetime.now().year
    film = FilmBase(
        title="Test Film",
        year=current_year,
        rating=8.5,
    )

    assert film.year == current_year


def test_film_year_rejects_future_year():
    current_year = datetime.now().year

    with pytest.raises(ValueError):
        FilmBase(
            title="Future Film",
            year=current_year + 1,
            rating=8.5,
        )

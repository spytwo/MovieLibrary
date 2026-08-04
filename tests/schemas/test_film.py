from datetime import datetime
from types import SimpleNamespace

import pytest

from movielibrary.models.enums import MediaType
from movielibrary.schemas.film import FilmBase, FilmCreate, FilmRead


@pytest.mark.parametrize("rating", [0, 5, 8.5, 10])
def test_film_rating_accepts_valid_values(rating):
    film = FilmBase(
        title="Test Film",
        year=2020,
        rating=rating,
    )

    assert film.rating == rating


@pytest.mark.parametrize("rating", [-1, 10.1, 11])
def test_film_rating_rejects_invalid_values(rating):
    with pytest.raises(
        ValueError,
        match="Рейтинг должен быть от 0 до 10",
    ):
        FilmBase(
            title="Test Film",
            year=2020,
            rating=rating,
        )


@pytest.mark.parametrize("year", [1888, 1900, 2020])
def test_film_year_accepts_valid_values(year):
    film = FilmBase(
        title="Test Film",
        year=year,
        rating=8.5,
    )

    assert film.year == year


def test_film_year_accepts_current_year():
    current_year = datetime.now().year

    film = FilmBase(
        title="Test Film",
        year=current_year,
        rating=8.5,
    )

    assert film.year == current_year


def test_film_year_rejects_before_1888():
    with pytest.raises(
        ValueError,
        match="Год не может быть меньше 1888",
    ):
        FilmBase(
            title="Test Film",
            year=1887,
            rating=8.5,
        )


def test_film_year_rejects_future_year():
    current_year = datetime.now().year

    with pytest.raises(
        ValueError,
        match=f"Год не может быть больше {current_year}",
    ):
        FilmBase(
            title="Future Film",
            year=current_year + 1,
            rating=8.5,
        )


def test_film_description_defaults_to_none():
    film = FilmBase(
        title="Test Film",
        year=2020,
        rating=8.5,
    )

    assert film.description is None


def test_film_description_accepts_string():
    film = FilmBase(
        title="Test Film",
        year=2020,
        rating=8.5,
        description="A test description",
    )

    assert film.description == "A test description"


def test_film_create_accepts_valid_data():
    film = FilmCreate(
        title="Test Film",
        year=2020,
        rating=8.5,
        photo="test.jpg",
        type=MediaType.movie,
    )

    assert film.title == "Test Film"
    assert film.year == 2020
    assert film.rating == 8.5
    assert film.photo == "test.jpg"
    assert film.type == MediaType.movie


def test_film_create_requires_photo():
    with pytest.raises(ValueError):
        FilmCreate(
            title="Test Film",
            year=2020,
            rating=8.5,
            type=MediaType.movie,
        )


def test_film_create_requires_type():
    with pytest.raises(ValueError):
        FilmCreate(
            title="Test Film",
            year=2020,
            rating=8.5,
            photo="test.jpg",
        )


def test_film_read_accepts_valid_data():
    film = FilmRead(
        id=1,
        title="Test Film",
        year=2020,
        rating=8.5,
        photo="test.jpg",
        genres=[],
        countries=[],
    )

    assert film.id == 1
    assert film.title == "Test Film"
    assert film.year == 2020
    assert film.rating == 8.5
    assert film.photo == "test.jpg"
    assert film.genres == []
    assert film.countries == []


@pytest.mark.parametrize(
    "field",
    ["id", "photo", "genres", "countries"],
)
def test_film_read_requires_fields(field):
    data = {
        "id": 1,
        "title": "Test Film",
        "year": 2020,
        "rating": 8.5,
        "photo": "test.jpg",
        "genres": [],
        "countries": [],
    }

    del data[field]

    with pytest.raises(ValueError):
        FilmRead(**data)


def test_film_read_supports_from_attributes():
    film_object = SimpleNamespace(
        id=1,
        title="Test Film",
        year=2020,
        rating=8.5,
        photo="test.jpg",
        genres=[],
        countries=[],
    )

    film = FilmRead.model_validate(film_object)

    assert film.id == 1
    assert film.title == "Test Film"
    assert film.year == 2020
    assert film.rating == 8.5
    assert film.photo == "test.jpg"
    assert film.genres == []
    assert film.countries == []


def test_film_read_accepts_genres_and_countries():
    film = FilmRead(
        id=1,
        title="Test Film",
        year=2020,
        rating=8.5,
        photo="test.jpg",
        genres=[
            {
                "id": 1,
                "name": "Thriller",
            }
        ],
        countries=[
            {
                "id": 1,
                "name": "USA",
            }
        ],
    )

    assert len(film.genres) == 1
    assert film.genres[0].id == 1
    assert film.genres[0].name == "Thriller"

    assert len(film.countries) == 1
    assert film.countries[0].id == 1
    assert film.countries[0].name == "USA"

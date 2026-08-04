from types import SimpleNamespace

import pytest

from movielibrary.schemas.genre import GenreBase, GenreCreate, GenreRead


def test_genre_base_accepts_valid_data():
    genre = GenreBase(
        name="Thriller",
    )

    assert genre.name == "Thriller"


def test_genre_base_requires_name():
    with pytest.raises(ValueError):
        GenreBase()


def test_genre_create_accepts_valid_data():
    genre = GenreCreate(
        name="Comedy",
    )

    assert genre.name == "Comedy"


def test_genre_create_requires_name():
    with pytest.raises(ValueError):
        GenreCreate()


def test_genre_read_accepts_valid_data():
    genre = GenreRead(
        id=1,
        name="Thriller",
    )

    assert genre.id == 1
    assert genre.name == "Thriller"


def test_genre_read_requires_id():
    with pytest.raises(ValueError):
        GenreRead(
            name="Thriller",
        )


def test_genre_read_requires_name():
    with pytest.raises(ValueError):
        GenreRead(
            id=1,
        )


def test_genre_read_supports_from_attributes():
    genre_object = SimpleNamespace(
        id=1,
        name="Thriller",
    )

    genre = GenreRead.model_validate(genre_object)

    assert genre.id == 1
    assert genre.name == "Thriller"

import pytest

from movielibrary.models import Genre
from movielibrary.repositories.genre import GenreRepository


def create_genre(name: str = "Horror") -> Genre:
    return Genre(name=name)


@pytest.mark.asyncio
async def test_get_all_returns_empty_list_when_no_genres(db_session):
    repository = GenreRepository(db_session)

    result = await repository.get_all()

    assert result == []


@pytest.mark.asyncio
async def test_get_all_returns_all_genres(db_session):
    genres = [
        create_genre(name="Horror"),
        create_genre(name="Comedy"),
        create_genre(name="Drama"),
    ]
    db_session.add_all(genres)
    await db_session.commit()

    repository = GenreRepository(db_session)

    result = await repository.get_all()

    assert len(result) == 3
    names = {genre.name for genre in result}
    assert names == {"Horror", "Comedy", "Drama"}


@pytest.mark.asyncio
async def test_get_all_names_returns_empty_list_when_no_genres(db_session):
    repository = GenreRepository(db_session)

    result = await repository.get_all_names()

    assert result == []


@pytest.mark.asyncio
async def test_get_all_names_returns_only_names(db_session):
    genres = [
        create_genre(name="Drama"),
        create_genre(name="Comedy"),
    ]
    db_session.add_all(genres)
    await db_session.commit()

    repository = GenreRepository(db_session)

    result = await repository.get_all_names()

    assert set(result) == {"Drama", "Comedy"}
    assert len(result) == 2

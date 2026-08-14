import pytest
from sqlalchemy import select

from movielibrary.models import Film, FilmCountry, FilmGenre
from movielibrary.repositories.film import FilmRepository
from tests.helpers import (
    create_country_in_db,
    create_film,
    create_film_with_relations,
    create_genre_in_db,
)


def test_apply_pagination_without_parameters_returns_same_statement():
    repository = FilmRepository(None)
    stmt = select(Film)

    result = repository._apply_pagination(stmt)

    assert result is stmt


def test_apply_pagination_with_limit():
    repository = FilmRepository(None)
    stmt = select(Film)

    result = repository._apply_pagination(stmt, limit=10)

    assert result is not stmt
    assert result._limit == 10
    assert result._offset is None


def test_apply_pagination_with_offset():
    repository = FilmRepository(None)
    stmt = select(Film)

    result = repository._apply_pagination(stmt, offset=20)

    assert result is not stmt
    assert result._offset == 20
    assert result._limit is None


def test_apply_pagination_with_limit_and_offset():
    repository = FilmRepository(None)
    stmt = select(Film)

    result = repository._apply_pagination(stmt, limit=10, offset=20)

    assert result is not stmt
    assert result._limit == 10
    assert result._offset == 20


@pytest.mark.asyncio
async def test_get_by_id_returns_film(db_session):
    film = create_film()
    db_session.add(film)

    await db_session.commit()
    await db_session.refresh(film)

    repository = FilmRepository(db_session)
    result = await repository.get_by_id(film.id)

    assert result is not None
    assert result.id == film.id
    assert result.title == "Test Film"
    assert result.year == 2026


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_not_found(db_session):
    repository = FilmRepository(db_session)
    result = await repository.get_by_id(99999)

    assert result is None


@pytest.mark.asyncio
async def test_get_global_statistics_when_no_films(db_session):
    repository = FilmRepository(db_session)
    result = await repository.get_global_statistics()

    assert result == {
        "total_films": 0,
        "average_rating": 0.0,
    }


@pytest.mark.asyncio
async def test_get_global_statistics_with_films(db_session):
    films = [
        create_film(title="Test A", rating=6),
        create_film(title="Test B", rating=7),
        create_film(title="Test C", rating=8),
    ]
    db_session.add_all(films)
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.get_global_statistics()

    assert result["total_films"] == 3
    assert result["average_rating"] == 7.0


@pytest.mark.asyncio
async def test_count_without_filters(db_session):
    films = [
        create_film(title="Film A"),
        create_film(title="Film B"),
        create_film(title="Film C"),
    ]
    db_session.add_all(films)
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.count()

    assert result == 3


@pytest.mark.asyncio
async def test_count_by_title(db_session):
    films = [
        create_film(title="First Blood"),
        create_film(title="The Bourne Identity"),
        create_film(title="The Terminator"),
    ]
    db_session.add_all(films)
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.count(q="Termi")

    assert result == 1


@pytest.mark.asyncio
async def test_count_by_type(db_session):
    films = [
        create_film(title="Movie 1", type="movie"),
        create_film(title="Movie 2", type="movie"),
        create_film(title="Series 1", type="series"),
    ]
    db_session.add_all(films)
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.count(film_type="series")

    assert result == 1


@pytest.mark.asyncio
async def test_count_by_year(db_session):
    films = [
        create_film(title="Film A", year=2010),
        create_film(title="Film B", year=2020),
        create_film(title="Film C", year=2020),
    ]
    db_session.add_all(films)
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.count(year=2010)

    assert result == 1


@pytest.mark.asyncio
async def test_count_by_rating_finds_film_in_range(db_session):
    films = [
        create_film(title="Film A", rating=8.4),
        create_film(title="Film A", rating=8.5),
        create_film(title="Film A", rating=8.4),
    ]
    db_session.add_all(films)
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.count(rating=8.4)

    assert result == 2


@pytest.mark.asyncio
async def test_count_by_rating_does_not_find_film_outside_range(db_session):
    film = create_film(title="Film", rating=7.0)
    db_session.add(film)
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.count(rating=8.5)

    assert result == 0


@pytest.mark.asyncio
async def test_count_by_genre(db_session):
    await create_film_with_relations(
        db_session,
        title="Film A",
        genre_names=["Horror"],
    )
    await create_film_with_relations(
        db_session,
        title="Film B",
        genre_names=["Comedy"],
    )
    await create_film_with_relations(
        db_session,
        title="Film C",
        genre_names=["Horror", "Thriller"],
    )

    repository = FilmRepository(db_session)
    result = await repository.count(genre_name="Horror")

    assert result == 2


@pytest.mark.asyncio
async def test_count_by_genre_not_found(db_session):
    await create_film_with_relations(
        db_session,
        title="Film A",
        genre_names=["Comedy"],
    )

    repository = FilmRepository(db_session)
    result = await repository.count(genre_name="Horror")

    assert result == 0


@pytest.mark.asyncio
async def test_count_by_country(db_session):
    await create_film_with_relations(
        db_session,
        title="Film A",
        country_names=["USA"],
    )
    await create_film_with_relations(
        db_session,
        title="Film B",
        country_names=["France"],
    )
    await create_film_with_relations(
        db_session,
        title="Film C",
        country_names=["USA", "UK"],
    )

    repository = FilmRepository(db_session)

    result = await repository.count(country_name="USA")

    assert result == 2


@pytest.mark.asyncio
async def test_count_by_country_not_found(db_session):
    await create_film_with_relations(
        db_session,
        title="Film A",
        country_names=["France"],
    )

    repository = FilmRepository(db_session)

    result = await repository.count(country_name="Russia")

    assert result == 0


@pytest.mark.asyncio
async def test_get_multi_returns_all_films(db_session):
    films = [
        create_film(title="Film A"),
        create_film(title="Film B"),
        create_film(title="Film C"),
    ]
    db_session.add_all(films)
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.get_multi()

    assert len(result) == 3
    titles = {film.title for film in result}
    assert titles == {"Film A", "Film B", "Film C"}


@pytest.mark.asyncio
async def test_get_multi_returns_empty_list_when_no_films(db_session):
    repository = FilmRepository(db_session)

    result = await repository.get_multi()

    assert result == []


@pytest.mark.asyncio
async def test_get_multi_orders_by_id_descending(db_session):
    film1 = create_film(title="First")
    film2 = create_film(title="Second")
    film3 = create_film(title="Third")

    db_session.add_all([film1, film2, film3])
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.get_multi()

    assert [film.title for film in result] == ["Third", "Second", "First"]


@pytest.mark.asyncio
async def test_get_multi_respects_limit(db_session):
    films = [create_film(title=f"Film {i}") for i in range(5)]
    db_session.add_all(films)
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.get_multi(limit=3)

    assert len(result) == 3


@pytest.mark.asyncio
async def test_get_multi_respects_offset(db_session):
    film1 = create_film(title="First")
    film2 = create_film(title="Second")
    film3 = create_film(title="Third")

    db_session.add_all([film1, film2, film3])
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.get_multi(offset=1)

    assert [film.title for film in result] == ["Second", "First"]


@pytest.mark.asyncio
async def test_get_multi_filter_by_title(db_session):
    films = [
        create_film(title="First Blood"),
        create_film(title="The Bourne Identity"),
        create_film(title="The Terminator"),
    ]
    db_session.add_all(films)
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.get_multi(q="Termi")

    assert len(result) == 1
    assert result[0].title == "The Terminator"


@pytest.mark.asyncio
async def test_get_multi_filter_by_type(db_session):
    films = [
        create_film(title="Movie 1", type="movie"),
        create_film(title="Series 1", type="series"),
        create_film(title="Movie 2", type="movie"),
    ]
    db_session.add_all(films)
    await db_session.commit()

    repository = FilmRepository(db_session)
    result = await repository.get_multi(film_type="series")

    assert len(result) == 1
    assert result[0].title == "Series 1"
    assert result[0].type == "series"


@pytest.mark.asyncio
async def test_get_multi_filter_by_genre(db_session):
    await create_film_with_relations(
        db_session,
        title="Film A",
        genre_names=["Horror"],
    )
    await create_film_with_relations(
        db_session,
        title="Film B",
        genre_names=["Comedy"],
    )
    await create_film_with_relations(
        db_session,
        title="Film C",
        genre_names=["Horror", "Comedy"],
    )

    repository = FilmRepository(db_session)

    result = await repository.get_multi(genre_name="Horror")

    assert len(result) == 2
    titles = {film.title for film in result}
    assert titles == {"Film A", "Film C"}


@pytest.mark.asyncio
async def test_get_multi_filter_by_country(db_session):
    await create_film_with_relations(
        db_session,
        title="Film A",
        country_names=["USA"],
    )
    await create_film_with_relations(
        db_session,
        title="Film B",
        country_names=["France"],
    )
    await create_film_with_relations(
        db_session,
        title="Film C",
        country_names=["USA", "UK"],
    )

    repository = FilmRepository(db_session)

    result = await repository.get_multi(country_name="USA")

    assert len(result) == 2
    titles = {film.title for film in result}
    assert titles == {"Film A", "Film C"}


@pytest.mark.asyncio
async def test_create_film_without_relations(db_session):
    film = create_film(title="Film", year=2021, rating=7.5)
    repository = FilmRepository(db_session)

    result = await repository.create(film, genre_ids=[], country_ids=[])

    assert result.id is not None
    assert result.title == "Film"
    assert result.year == 2021
    assert result.rating == 7.5


@pytest.mark.asyncio
async def test_create_film_with_genres(db_session):
    genre1 = await create_genre_in_db(db_session, name="Horror")
    genre2 = await create_genre_in_db(db_session, name="Comedy")

    film = create_film(title="Film")
    repository = FilmRepository(db_session)

    result = await repository.create(
        film,
        genre_ids=[genre1.id, genre2.id],
        country_ids=[],
    )

    stmt = select(FilmGenre).where(FilmGenre.film_id == result.id)
    relations = (await db_session.execute(stmt)).scalars().all()

    assert len(relations) == 2
    genre_ids = {rel.genre_id for rel in relations}
    assert genre_ids == {genre1.id, genre2.id}


@pytest.mark.asyncio
async def test_create_film_with_countries(db_session):
    country1 = await create_country_in_db(db_session, name="USA")
    country2 = await create_country_in_db(db_session, name="UK")

    film = create_film(title="Film")
    repository = FilmRepository(db_session)

    result = await repository.create(
        film,
        genre_ids=[],
        country_ids=[country1.id, country2.id],
    )

    stmt = select(FilmCountry).where(FilmCountry.film_id == result.id)
    relations = (await db_session.execute(stmt)).scalars().all()

    assert len(relations) == 2
    country_ids = {rel.country_id for rel in relations}
    assert country_ids == {country1.id, country2.id}


@pytest.mark.asyncio
async def test_create_film_with_genres_and_countries(db_session):
    genre = await create_genre_in_db(db_session, name="Drama")
    country = await create_country_in_db(db_session, name="France")

    film = create_film(title="Film")
    repository = FilmRepository(db_session)

    result = await repository.create(
        film,
        genre_ids=[genre.id],
        country_ids=[country.id],
    )

    genre_relations = (
        (
            await db_session.execute(
                select(FilmGenre).where(FilmGenre.film_id == result.id)
            )
        )
        .scalars()
        .all()
    )

    country_relations = (
        (
            await db_session.execute(
                select(FilmCountry).where(FilmCountry.film_id == result.id)
            )
        )
        .scalars()
        .all()
    )

    assert len(genre_relations) == 1
    assert genre_relations[0].genre_id == genre.id
    assert len(country_relations) == 1
    assert country_relations[0].country_id == country.id

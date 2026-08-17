import pytest
from fastapi import HTTPException
from sqlalchemy import select

from movielibrary.models import FilmCountry, FilmGenre
from movielibrary.models.enums import MediaType
from movielibrary.schemas.film import FilmCreate
from movielibrary.services.film import FilmService
from tests.helpers import (
    create_country_in_db,
    create_film,
    create_film_with_relations,
    create_genre_in_db,
)


@pytest.mark.asyncio
async def test_create_new_film_as_movie(db_session):
    payload = FilmCreate(
        title="Film A",
        year=2010,
        rating=8.8,
        photo="Film_A.jpg",
        type=MediaType.movie,
    )

    service = FilmService(db_session)
    result = await service.create_new_film(payload, genre_ids=[], country_ids=[])

    assert result.id is not None
    assert result.title == "Film A"
    assert result.type == "movie"
    assert result.year == 2010
    assert result.rating == 8.8


@pytest.mark.asyncio
async def test_create_new_film_as_series_adds_suffix(db_session):
    payload = FilmCreate(
        title="Series A",
        year=2008,
        rating=9.5,
        photo="Series_A.jpg",
        type=MediaType.series,
    )

    service = FilmService(db_session)
    result = await service.create_new_film(payload, genre_ids=[], country_ids=[])

    assert result.title == "Series A (Сериал)"
    assert result.type == "series"


@pytest.mark.asyncio
async def test_create_new_film_with_genres_and_countries(db_session):
    genre = await create_genre_in_db(db_session, name="Thriller")
    country = await create_country_in_db(db_session, name="USA")

    payload = FilmCreate(
        title="Film A",
        year=2014,
        rating=8.6,
        photo="Film_A.jpg",
        type=MediaType.movie,
    )

    service = FilmService(db_session)
    result = await service.create_new_film(
        payload,
        genre_ids=[genre.id],
        country_ids=[country.id],
    )

    assert result.title == "Film A"

    genre_links = (
        (
            await db_session.execute(
                select(FilmGenre).where(FilmGenre.film_id == result.id)
            )
        )
        .scalars()
        .all()
    )

    country_links = (
        (
            await db_session.execute(
                select(FilmCountry).where(FilmCountry.film_id == result.id)
            )
        )
        .scalars()
        .all()
    )

    assert len(genre_links) == 1
    assert genre_links[0].genre_id == genre.id
    assert len(country_links) == 1
    assert country_links[0].country_id == country.id


@pytest.mark.asyncio
async def test_get_paginated_films_rejects_short_query(db_session):
    film = create_film(title="Inception")
    db_session.add(film)
    await db_session.commit()

    service = FilmService(db_session)

    films, total_pages = await service.get_paginated_films(
        page=1,
        page_size=5,
        q="In",
    )

    assert films == []
    assert total_pages == 0


@pytest.mark.asyncio
async def test_get_paginated_films_returns_films_and_pages(db_session):
    films = [
        create_film(title="Film 1"),
        create_film(title="Film 2"),
        create_film(title="Film 3"),
        create_film(title="Film 4"),
        create_film(title="Film 5"),
        create_film(title="Film 6"),
    ]
    db_session.add_all(films)
    await db_session.commit()

    service = FilmService(db_session)

    result_films, total_pages = await service.get_paginated_films(
        page=1,
        page_size=5,
    )

    assert len(result_films) == 5
    assert total_pages == 2


@pytest.mark.asyncio
async def test_get_paginated_films_second_page(db_session):
    films = [create_film(title=f"Film {i}") for i in range(6)]
    db_session.add_all(films)
    await db_session.commit()

    service = FilmService(db_session)

    result_films, total_pages = await service.get_paginated_films(
        page=2,
        page_size=5,
    )

    assert len(result_films) == 1
    assert total_pages == 2


@pytest.mark.asyncio
async def test_get_film_by_id_returns_film(db_session):
    film = await create_film_with_relations(
        db_session,
        title="Film A",
        year=2010,
        rating=8.8,
        genre_names=["Drama"],
        country_names=["USA"],
    )

    service = FilmService(db_session)
    result = await service.get_film_by_id(film.id)

    assert result.id == film.id
    assert result.title == "Film A"
    assert result.year == 2010
    assert result.rating == 8.8
    assert len(result.genres) == 1
    assert result.genres[0].name == "Drama"
    assert len(result.countries) == 1
    assert result.countries[0].name == "USA"


@pytest.mark.asyncio
async def test_get_film_by_id_raises_404_when_not_found(db_session):
    service = FilmService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_film_by_id(99999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Фильм не найден"


@pytest.mark.asyncio
async def test_get_statistics(db_session):
    films = [
        create_film(title="A", rating=8.0),
        create_film(title="B", rating=9.0),
    ]
    db_session.add_all(films)
    await db_session.commit()

    service = FilmService(db_session)
    result = await service.get_statistics()

    assert result["total_films"] == 2
    assert result["average_rating"] == 8.5


@pytest.mark.asyncio
async def test_get_films_list(db_session):
    await create_film_with_relations(
        db_session,
        title="Inception",
        genre_names=["Sci-Fi"],
    )
    await create_film_with_relations(
        db_session,
        title="The Matrix",
        genre_names=["Action"],
    )

    service = FilmService(db_session)
    result = await service.get_films_list(q="Incep")

    assert len(result) == 1
    assert result[0].title == "Inception"
    assert result[0].genres[0].name == "Sci-Fi"


@pytest.mark.asyncio
async def test_get_latest_films_for_index(db_session):
    films = [create_film(title=f"Film {i}") for i in range(7)]
    db_session.add_all(films)
    await db_session.commit()

    service = FilmService(db_session)
    result = await service.get_latest_films_for_index(limit=5)

    assert len(result) == 5

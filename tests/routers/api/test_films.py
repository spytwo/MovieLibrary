import pytest

from tests.helpers import create_film, create_film_with_relations


@pytest.mark.asyncio
async def test_get_films_statistics_empty(client):
    response = await client.get("/api/films/statistics")

    assert response.status_code == 200
    assert response.json() == {
        "total_films": 0,
        "average_rating": 0.0,
    }


@pytest.mark.asyncio
async def test_get_films_statistics_with_data(client, db_session):
    db_session.add_all(
        [
            create_film(title="A", rating=8.0),
            create_film(title="B", rating=9.0),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/films/statistics")

    assert response.status_code == 200
    data = response.json()
    assert data["total_films"] == 2
    assert data["average_rating"] == 8.5


@pytest.mark.asyncio
async def test_retrieve_film_success(client, db_session):
    film = await create_film_with_relations(
        db_session,
        title="Inception",
        year=2010,
        rating=8.8,
        genre_names=["Sci-Fi"],
        country_names=["USA"],
    )

    response = await client.get(f"/api/films/{film.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == film.id
    assert data["title"] == "Inception"
    assert data["year"] == 2010
    assert data["rating"] == 8.8
    assert data["genres"][0]["name"] == "Sci-Fi"
    assert data["countries"][0]["name"] == "USA"


@pytest.mark.asyncio
async def test_retrieve_film_not_found(client):
    response = await client.get("/api/films/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Фильм не найден"


@pytest.mark.asyncio
async def test_list_films_empty(client):
    response = await client.get("/api/films")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_films_returns_films(client, db_session):
    await create_film_with_relations(
        db_session,
        title="Inception",
        year=2010,
        rating=8.8,
        genre_names=["Sci-Fi"],
    )
    await create_film_with_relations(
        db_session,
        title="The Matrix",
        year=1999,
        rating=8.7,
        genre_names=["Action"],
    )

    response = await client.get("/api/films")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    titles = {film["title"] for film in data}
    assert titles == {"Inception", "The Matrix"}


@pytest.mark.asyncio
async def test_list_films_filter_by_title(client, db_session):
    await create_film_with_relations(db_session, title="Inception")
    await create_film_with_relations(db_session, title="Interstellar")
    await create_film_with_relations(db_session, title="The Matrix")

    response = await client.get("/api/films", params={"q": "Inter"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Interstellar"


@pytest.mark.asyncio
async def test_list_films_rejects_short_query(client):
    response = await client.get("/api/films", params={"q": "In"})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_films_pagination(client, db_session):
    for i in range(5):
        await create_film_with_relations(db_session, title=f"Film {i}")

    response = await client.get(
        "/api/films",
        params={"page": 1, "page_size": 2},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2

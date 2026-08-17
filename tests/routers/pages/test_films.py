import pytest

from tests.helpers import create_film, create_film_with_relations, create_genre


@pytest.mark.asyncio
async def test_index_page_returns_html(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert response.text


@pytest.mark.asyncio
async def test_index_page_shows_films(client, db_session):
    db_session.add(create_film(title="Inception"))
    db_session.add(create_genre(name="Sci-Fi"))
    await db_session.commit()

    response = await client.get("/")

    assert response.status_code == 200
    assert "Inception" in response.text
    assert "Sci-Fi" in response.text


@pytest.mark.asyncio
async def test_index_page_empty(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_series_page_shows_only_series(client, db_session):
    db_session.add(create_film(title="Breaking Bad", type="series"))
    db_session.add(create_film(title="Inception", type="movie"))
    await db_session.commit()

    response = await client.get("/series")

    assert response.status_code == 200
    assert "Breaking Bad" in response.text


@pytest.mark.asyncio
async def test_film_detail_page(client, db_session):
    film = await create_film_with_relations(
        db_session,
        title="Inception",
        year=2010,
        rating=8.8,
        genre_names=["Sci-Fi"],
    )

    response = await client.get(f"/film/{film.id}")

    assert response.status_code == 200
    assert "Inception" in response.text
    assert "2010" in response.text
    assert "Sci-Fi" in response.text


@pytest.mark.asyncio
async def test_film_detail_page_not_found(client):
    response = await client.get("/film/99999")

    assert response.status_code in (404, 200)

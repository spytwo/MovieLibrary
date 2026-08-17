import pytest

from tests.helpers import create_genre


@pytest.mark.asyncio
async def test_list_genres_empty(client):
    response = await client.get("/api/genres")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_genres_returns_names(client, db_session):
    db_session.add_all(
        [
            create_genre(name="Action"),
            create_genre(name="Comedy"),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/genres")

    assert response.status_code == 200
    assert set(response.json()) == {"Action", "Comedy"}

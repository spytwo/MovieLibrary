import pytest

from tests.helpers import create_country


@pytest.mark.asyncio
async def test_list_countries_empty(client):
    response = await client.get("/api/countries")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_countries_returns_names(client, db_session):
    db_session.add_all(
        [
            create_country(name="USA"),
            create_country(name="France"),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/countries")

    assert response.status_code == 200
    assert set(response.json()) == {"USA", "France"}

import pytest

from movielibrary.repositories.country import CountryRepository
from tests.helpers import create_country


@pytest.mark.asyncio
async def test_get_all_returns_empty_list_when_no_countries(db_session):
    repository = CountryRepository(db_session)

    result = await repository.get_all()

    assert result == []


@pytest.mark.asyncio
async def test_get_all_returns_all_countries(db_session):
    countries = [
        create_country(name="USA"),
        create_country(name="France"),
        create_country(name="Japan"),
    ]
    db_session.add_all(countries)
    await db_session.commit()

    repository = CountryRepository(db_session)

    result = await repository.get_all()

    assert len(result) == 3
    names = {country.name for country in result}
    assert names == {"USA", "France", "Japan"}


@pytest.mark.asyncio
async def test_get_all_names_returns_empty_list_when_no_countries(db_session):
    repository = CountryRepository(db_session)

    result = await repository.get_all_names()

    assert result == []


@pytest.mark.asyncio
async def test_get_all_names_returns_only_names(db_session):
    countries = [
        create_country(name="USA"),
        create_country(name="France"),
    ]
    db_session.add_all(countries)
    await db_session.commit()

    repository = CountryRepository(db_session)

    result = await repository.get_all_names()

    assert set(result) == {"USA", "France"}
    assert len(result) == 2

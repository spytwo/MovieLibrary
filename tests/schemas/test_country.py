from types import SimpleNamespace

import pytest

from movielibrary.schemas.country import CountryBase, CountryCreate, CountryRead


def test_country_base_accepts_valid_data():
    country = CountryBase(
        name="USA",
    )

    assert country.name == "USA"


def test_country_base_requires_name():
    with pytest.raises(ValueError):
        CountryBase()


def test_country_create_accepts_valid_data():
    country = CountryCreate(
        name="Germany",
    )

    assert country.name == "Germany"


def test_country_create_requires_name():
    with pytest.raises(ValueError):
        CountryCreate()


def test_country_read_accepts_valid_data():
    country = CountryRead(
        id=1,
        name="USA",
    )

    assert country.id == 1
    assert country.name == "USA"


def test_country_read_requires_id():
    with pytest.raises(ValueError):
        CountryRead(
            name="USA",
        )


def test_country_read_requires_name():
    with pytest.raises(ValueError):
        CountryRead(
            id=1,
        )


def test_country_read_supports_from_attributes():
    country_object = SimpleNamespace(
        id=1,
        name="USA",
    )

    country = CountryRead.model_validate(country_object)

    assert country.id == 1
    assert country.name == "USA"

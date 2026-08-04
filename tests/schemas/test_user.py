import pytest

from movielibrary.schemas.user import UserCreate


def test_user_create_accepts_valid_data():
    user = UserCreate(
        email="test@example.com",
        password="123456",
    )

    assert user.email == "test@example.com"
    assert user.password == "123456"


def test_user_create_accepts_password_with_more_than_6_characters():
    user = UserCreate(
        email="test@example.com",
        password="secure_password",
    )

    assert user.password == "secure_password"


def test_user_create_accepts_password_with_exactly_6_characters():
    user = UserCreate(
        email="test@example.com",
        password="123456",
    )

    assert user.password == "123456"


def test_user_create_rejects_password_shorter_than_6_characters():
    with pytest.raises(
        ValueError,
        match="Пароль должен содержать минимум 6 символов",
    ):
        UserCreate(
            email="test@example.com",
            password="12345",
        )


def test_user_create_rejects_empty_password():
    with pytest.raises(
        ValueError,
        match="Пароль должен содержать минимум 6 символов",
    ):
        UserCreate(
            email="test@example.com",
            password="",
        )


@pytest.mark.parametrize(
    "email",
    [
        "test",
        "test@",
        "@example.com",
        "test@example",
        "test example@example.com",
    ],
)
def test_user_create_rejects_invalid_email(email):
    with pytest.raises(ValueError):
        UserCreate(
            email=email,
            password="123456",
        )


def test_user_create_requires_email():
    with pytest.raises(ValueError):
        UserCreate(
            password="123456",
        )


def test_user_create_requires_password():
    with pytest.raises(ValueError):
        UserCreate(
            email="test@example.com",
        )

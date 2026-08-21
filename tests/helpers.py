from sqlalchemy import select

from movielibrary.auth_utils import get_password_hash
from movielibrary.models import Country, Film, FilmCountry, FilmGenre, Genre, User


def create_user(
    email: str = "user@example.com",
    password_hash: str = "hashed_password",
) -> User:
    return User(
        email=email,
        password_hash=password_hash,
    )


def create_genre(name: str = "Thriller") -> Genre:
    return Genre(name=name)


async def create_genre_in_db(db_session, name: str = "Action") -> Genre:
    genre = create_genre(name=name)
    db_session.add(genre)
    await db_session.commit()
    await db_session.refresh(genre)
    return genre


def create_country(name: str = "USA") -> Country:
    return Country(name=name)


async def create_country_in_db(db_session, name: str = "USA") -> Country:
    country = create_country(name=name)
    db_session.add(country)
    await db_session.commit()
    await db_session.refresh(country)
    return country


def create_film(
    title: str = "Test Film",
    type: str = "movie",
    year: int = 2026,
    rating: float = 8.0,
    photo: str = "test.jpg",
    description: str | None = None,
) -> Film:
    return Film(
        title=title,
        type=type,
        year=year,
        rating=rating,
        photo=photo,
        description=description,
    )


async def create_film_with_relations(
    db_session,
    *,
    title: str = "Test Film",
    type: str = "movie",
    year: int = 2020,
    rating: float = 8.0,
    photo: str = "test.jpg",
    description: str | None = None,
    genre_names: list[str] | None = None,
    country_names: list[str] | None = None,
) -> Film:
    film = create_film(
        title=title,
        type=type,
        year=year,
        rating=rating,
        photo=photo,
        description=description,
    )
    db_session.add(film)
    await db_session.flush()

    if genre_names:
        for name in genre_names:
            result = await db_session.execute(select(Genre).where(Genre.name == name))
            genre = result.scalar_one_or_none()

            if genre is None:
                genre = create_genre(name=name)
                db_session.add(genre)
                await db_session.flush()

            db_session.add(FilmGenre(film_id=film.id, genre_id=genre.id))

    if country_names:
        for name in country_names:
            result = await db_session.execute(
                select(Country).where(Country.name == name)
            )
            country = result.scalar_one_or_none()

            if country is None:
                country = create_country(name=name)
                db_session.add(country)
                await db_session.flush()

            db_session.add(FilmCountry(film_id=film.id, country_id=country.id))

    await db_session.commit()
    await db_session.refresh(film)
    return film


async def login_user(
    client,
    db_session,
    email: str = "alice@example.com",
    password: str = "secret123",
):
    from sqlalchemy import select

    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = create_user(
            email=email,
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()
    else:
        user.password_hash = get_password_hash(password)
        await db_session.commit()

    form_response = await client.get("/login")
    csrf_token = form_response.cookies["csrf_token"]
    client.cookies.set("csrf_token", csrf_token)

    response = await client.post(
        "/login",
        data={
            "email": email,
            "password": password,
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    if "access_token" in response.cookies:
        client.cookies.set("access_token", response.cookies["access_token"])

    return user

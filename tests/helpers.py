from sqlalchemy import select

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

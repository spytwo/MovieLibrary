from movielibrary.models import Film
from movielibrary.schemas.country import CountryRead
from movielibrary.schemas.film import FilmRead
from movielibrary.schemas.genre import GenreRead


def film_to_read(film: Film) -> FilmRead:
    return FilmRead(
        id=film.id,
        title=film.title,
        year=film.year,
        description=film.description,
        rating=film.rating,
        photo=film.photo,
        genres=[GenreRead.model_validate(fg.genre) for fg in film.genres],
        countries=[CountryRead.model_validate(fc.country) for fc in film.countries],
    )


def films_to_read(films: list[Film]) -> list[FilmRead]:
    return [film_to_read(film) for film in films]

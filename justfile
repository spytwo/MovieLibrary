up:
    docker compose up --build -d

down:
    docker compose down

shell:
    docker exec -it filmsdb psql -U postgres -d films_db

app:
    docker exec -it movielibrary_app /bin/bash

fix:
    ruff format && ruff check --fix

logs:
    docker compose logs

redis:
    docker exec -it movielibrary_redis redis-cli

tests:
    docker compose exec web pytest -v

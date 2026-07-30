from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.sessions import SessionMiddleware

from movielibrary.redis import close_redis, redis_client
from movielibrary.routers import countries, films, genres, pages
from movielibrary.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.ping()

    FastAPICache.init(
        RedisBackend(redis_client),
        prefix="fastapi-cache",
    )

    yield

    await close_redis()


app = FastAPI(title="Movie Library API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
)
app.mount("/static", StaticFiles(directory="movielibrary/static"), name="static")

app.include_router(films.router, prefix="/api/films", tags=["Films"])
app.include_router(genres.router, prefix="/api/genres", tags=["Genres"])
app.include_router(countries.router, prefix="/api/countries", tags=["Countries"])

app.include_router(pages.router, tags=["Web Pages"], include_in_schema=False)

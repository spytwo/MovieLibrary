from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.sessions import SessionMiddleware

from movielibrary.exceptions import setup_exception_handlers
from movielibrary.redis import close_redis, redis_client
from movielibrary.routers.api import router as api_router
from movielibrary.routers.pages import router as pages_router
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

app.include_router(api_router)
app.include_router(pages_router)

setup_exception_handlers(app)

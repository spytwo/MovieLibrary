from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
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


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if request.method == "POST" and not request.url.path.startswith("/api"):
        referer = request.headers.get("referer", "/")

        error_msg = (
            exc.detail if isinstance(exc.detail, str) else "Ошибка валидации данных"
        )

        base_referer = referer.split("?")[0]
        encoded_error = quote(error_msg)
        redirect_url = f"{base_referer}?error={encoded_error}"

        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

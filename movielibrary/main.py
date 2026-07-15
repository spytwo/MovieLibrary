import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from movielibrary.routers import countries, films, genres, pages

app = FastAPI(title="Movie Library API", version="0.1.0")
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
app.mount("/static", StaticFiles(directory="movielibrary/static"), name="static")

app.include_router(films.router, prefix="/api/films", tags=["Films"])
app.include_router(genres.router, prefix="/api/genres", tags=["Genres"])
app.include_router(countries.router, prefix="/api/countries", tags=["Countries"])

app.include_router(pages.router, tags=["Web Pages"], include_in_schema=False)


if __name__ == "__main__":
    uvicorn.run("movielibrary.main:app", host="0.0.0.0", port=8002, reload=True)

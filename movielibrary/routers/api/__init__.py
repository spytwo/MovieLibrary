from fastapi import APIRouter

from movielibrary.routers.api.countries import router as countries_router
from movielibrary.routers.api.films import router as films_router
from movielibrary.routers.api.genres import router as genres_router

router = APIRouter(prefix="/api")

router.include_router(films_router, prefix="/films", tags=["Films"])
router.include_router(genres_router, prefix="/genres", tags=["Genres"])
router.include_router(countries_router, prefix="/countries", tags=["Countries"])

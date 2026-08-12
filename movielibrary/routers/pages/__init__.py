from fastapi import APIRouter

from movielibrary.routers.pages.admin import router as admin_router
from movielibrary.routers.pages.auth import router as auth_router
from movielibrary.routers.pages.films import router as films_router

router = APIRouter(include_in_schema=False)

router.include_router(admin_router)
router.include_router(auth_router)
router.include_router(films_router)

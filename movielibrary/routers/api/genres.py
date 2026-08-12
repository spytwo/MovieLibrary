from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.database import get_db
from movielibrary.repositories.genre import GenreRepository

router = APIRouter(tags=["Genres"])


@router.get("", response_model=list[str], summary="List Genres")
async def list_genres(db: AsyncSession = Depends(get_db)):
    repo = GenreRepository(db)
    return await repo.get_all_names()

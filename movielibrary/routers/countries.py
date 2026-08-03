from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from movielibrary.database import get_db
from movielibrary.repositories.country import CountryRepository

router = APIRouter(tags=["Countries"])


@router.get("", response_model=list[str], summary="List Countries")
async def list_countries(db: AsyncSession = Depends(get_db)):
    repo = CountryRepository(db)
    return await repo.get_all_names()

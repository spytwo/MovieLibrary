import pytest
import pytest_asyncio
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from movielibrary.database import get_db
from movielibrary.main import app
from movielibrary.models.base import Base


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(autouse=True)
def init_cache():
    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="test-cache")
    yield

    if hasattr(backend, "_store"):
        backend._store.clear()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

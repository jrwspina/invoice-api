import pytest

from alembic import command
from alembic.config import Config
from httpx import AsyncClient
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import get_db
from app.main import app
from app.settings import settings

engine = create_async_engine(f"{settings.test_postgres_url}")
async_session = async_sessionmaker(engine)


async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.test_postgres_url)

    command.upgrade(alembic_cfg, "head")
    yield
    command.downgrade(alembic_cfg, "base")


@pytest.fixture
def override_db():
    app.dependency_overrides[get_db] = get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(override_db):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

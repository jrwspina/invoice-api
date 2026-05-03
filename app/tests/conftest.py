import pytest

from alembic import command
from alembic.config import Config
from httpx import AsyncClient
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import get_db
from app.main import app
from app.models import User
from app.security import get_password_hash
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


@pytest.fixture
async def session():
    async with async_session() as session:
        yield session


@pytest.fixture
async def sample_user(session):
    user = User(
        firstname="name",
        lastname="lastname",
        email="test@test.com",
        password_hash=get_password_hash("password"),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    yield user
    await session.delete(user)
    await session.commit()


@pytest.fixture
async def auth_token(client, sample_user):
    response = await client.post(
        "auth/token",
        data={
            "username": sample_user.email,
            "password": "password",
        },
    )

    return response.json()["access_token"]


@pytest.fixture
async def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

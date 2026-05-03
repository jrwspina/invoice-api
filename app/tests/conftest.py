import pytest

from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import get_db
from app.main import app
from app.models import Base, User
from app.security import get_password_hash
from app.settings import settings


@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(settings.test_postgres_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    return async_sessionmaker(db_engine)


@pytest.fixture
async def session(db_session_factory):
    async with db_session_factory() as session:
        yield session


@pytest.fixture
def override_db(db_session_factory):
    async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
        async with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(override_db):
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        yield ac


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

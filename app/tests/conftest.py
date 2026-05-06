import pytest
import uuid

from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from sqlalchemy import false
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import get_db
from app.main import app
from app.models import Base, Client, User
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
    return async_sessionmaker(db_engine, expire_on_commit=False)


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
async def make_user(session: AsyncSession):
    users = []

    async def _make_user(**kwargs):
        data = {
            "firstname": "firstname",
            "lastname": "lastname",
            "email": f"user{uuid.uuid4()}@test.com",
            "password_hash": get_password_hash("password"),
        }
        data.update(kwargs)
        user = User(**data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        users.append(user)
        return user

    yield _make_user
    for user in users:
        try:
            await session.delete(user)
            await session.commit()
        except Exception:
            await session.rollback()


@pytest.fixture
async def make_client(session: AsyncSession):
    clients = []

    async def _make_client(user: User, **kwargs):
        data = {
            "firstname": "firstname",
            "lastname": "lastname",
            "email": f"client{uuid.uuid4()}@test.com",
        }
        data.update(kwargs)
        client = Client(**data, user_id=user.id)
        session.add(client)
        await session.commit()
        await session.refresh(client)
        clients.append(client)
        return client

    yield _make_client
    for client in clients:
        try:
            await session.delete(client)
            await session.commit()
        except Exception:
            await session.rollback()


@pytest.fixture
async def make_auth_headers(client: AsyncClient):
    async def _make_auth_headers(user: User):
        response = await client.post(
            "auth/token",
            data={
                "username": user.email,
                "password": "password",
            },
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make_auth_headers

import pytest
import uuid
import redis as sync_redis

from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator, Type
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
from unittest.mock import patch

from app.database import get_db
from app.main import app
from app.models import Base, Client, Invoice, LineItem, Payment, User
from app.security import create_access_token, get_password_hash
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


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    r = sync_redis.from_url(settings.redis_url)
    for key in r.scan_iter(match="LIMITER*"):
        r.delete(key)
    yield
    for key in r.scan_iter(match="LIMITER*"):
        r.delete(key)


@pytest.fixture
async def client(override_db):
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        yield ac


async def unmake_object(session: AsyncSession, model_class: Type[Base], id: int):
    obj = await session.get(model_class, id)

    if obj:
        await session.delete(obj)
        await session.commit()


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
        users.append(user.id)
        return user

    yield _make_user
    for user in users:
        try:
            await unmake_object(session, User, user)
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
        clients.append(client.id)
        return client

    yield _make_client
    for client in clients:
        try:
            await unmake_object(session, Client, client)
        except Exception:
            await session.rollback()


@pytest.fixture
async def make_invoice(session: AsyncSession):
    invoices = []

    async def _make_invoice(user: User, client: Client, **kwargs):
        data = {
            "issue_date": datetime.now(timezone.utc).replace(microsecond=0),
            "due_date": datetime.now(timezone.utc).replace(microsecond=0)
            + timedelta(days=1),
        }
        data.update(kwargs)
        invoice = Invoice(**data, user_id=user.id, client_id=client.id)
        session.add(invoice)
        await session.commit()
        await session.refresh(invoice)
        invoices.append(invoice.id)
        return invoice

    yield _make_invoice
    for invoice in invoices:
        try:
            await unmake_object(session, Invoice, invoice)
        except Exception:
            await session.rollback()


@pytest.fixture
async def make_lineitem(session: AsyncSession):
    lineitems = []

    async def _make_lineitem(invoice: Invoice, **kwargs):
        data = {
            "description": "item",
            "quantity": 1,
            "unit_price": 100,
        }
        data.update(kwargs)
        lineitem = LineItem(**data, invoice_id=invoice.id)
        session.add(lineitem)
        await session.commit()
        await session.refresh(lineitem)
        lineitems.append(lineitem.id)
        return lineitem

    yield _make_lineitem
    for lineitem in lineitems:
        try:
            await unmake_object(session, LineItem, lineitem)
        except Exception:
            await session.rollback()


@pytest.fixture
async def make_payment(session: AsyncSession):
    payments = []

    async def _make_payment(invoice: Invoice, **kwargs):
        data = {
            "paid_at": datetime.now(timezone.utc).replace(microsecond=0),
            "value": 100,
        }
        data.update(kwargs)
        payment = Payment(**data, invoice_id=invoice.id)
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        payments.append(payment.id)
        return payment

    yield _make_payment
    for payment in payments:
        try:
            await unmake_object(session, Payment, payment)
        except Exception:
            await session.rollback()


@pytest.fixture
async def make_auth_headers(client: AsyncClient):
    async def _make_auth_headers(user: User):
        token = create_access_token(data={"sub": user.email})
        return {"Authorization": f"Bearer {token}"}

    return _make_auth_headers


@pytest.fixture
def mock_send_invoice_email():
    with patch("app.routers.invoices.send_invoice_email") as mock_task:
        yield mock_task

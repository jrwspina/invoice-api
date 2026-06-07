from typing import Sequence
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Client
from app.schemas import ClientRead
from app.schemas import ClientCreate, ClientUpdate, ClientPatch


async def get_user_clients(
    user_id: int, session: AsyncSession, limit: int = 10, offset: int = 0
) -> Sequence[Client]:
    result = await session.execute(
        select(Client)
        .where(Client.user_id == user_id)
        .order_by(Client.id)
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


async def get_client(
    client_id: int, session: AsyncSession, redis: Redis
) -> Client | ClientRead | None:
    cached = await redis.get(f"client:{client_id}")
    if cached:
        return ClientRead.model_validate_json(cached)
    client = await session.get(Client, client_id)
    if client:
        await redis.set(
            f"client:{client_id}",
            ClientRead.model_validate(client).model_dump_json(),
            ex=300,
        )
    return client


async def get_client_nocache(client_id: int, session: AsyncSession) -> Client | None:
    return await session.get(Client, client_id)


async def create_client(
    client: ClientCreate, user_id: int, session: AsyncSession
) -> Client:
    db_client = Client(**client.model_dump())
    db_client.user_id = user_id
    session.add(db_client)
    await session.commit()
    await session.refresh(db_client)
    return db_client


async def update_client(
    client: Client, new_data: ClientUpdate, session: AsyncSession, redis: Redis
) -> Client:
    client.firstname = new_data.firstname
    client.lastname = new_data.lastname
    client.email = new_data.email
    client.phone = new_data.phone
    client.company = new_data.company
    client.billing_address = new_data.billing_address

    client_id = client.id

    await session.commit()
    await session.refresh(client)
    await redis.delete(f"client:{client_id}")
    return client


async def patch_client(
    client: Client, data: ClientPatch, session: AsyncSession, redis: Redis
) -> Client:
    new_data = data.model_dump(exclude_unset=True)
    client_id = client.id

    for key, value in new_data.items():
        setattr(client, key, value)

    await session.commit()
    await session.refresh(client)
    await redis.delete(f"client:{client_id}")
    return client


async def delete_client(client: Client, session: AsyncSession, redis: Redis):
    client_id = client.id
    await session.delete(client)
    await session.commit()
    await redis.delete(f"client:{client_id}")

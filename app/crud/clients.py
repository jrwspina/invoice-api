from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Client
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


async def get_clients(session: AsyncSession) -> Sequence[Client]:
    result = await session.execute(select(Client))
    return result.scalars().all()


async def get_client(client_id: int, session: AsyncSession) -> Client | None:
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
    client: Client, new_data: ClientUpdate, session: AsyncSession
) -> Client:
    client.firstname = new_data.firstname
    client.lastname = new_data.lastname
    client.email = new_data.email
    client.phone = new_data.phone
    client.company = new_data.company
    client.billing_address = new_data.billing_address

    await session.commit()
    await session.refresh(client)
    return client


async def patch_client(
    client: Client, data: ClientPatch, session: AsyncSession
) -> Client:
    new_data = data.model_dump(exclude_unset=True)

    for key, value in new_data.items():
        setattr(client, key, value)

    await session.commit()
    await session.refresh(client)
    return client


async def delete_client(client: Client, session: AsyncSession):
    await session.delete(client)
    await session.commit()

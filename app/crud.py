from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Client
from app.schemas import UserCreate, UserPatch, UserUpdate
from app.security import get_password_hash


async def get_users(session: AsyncSession) -> Sequence[User]:
    result = await session.execute(select(User))
    return result.scalars().all()


async def get_user(user_id: int, session: AsyncSession) -> User | None:
    return await session.get(User, user_id)


async def create_user(user: UserCreate, session: AsyncSession) -> User:
    db_user = User(**user.model_dump(exclude={"password"}))
    db_user.password_hash = get_password_hash(user.password)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def update_user(user: User, new_data: UserUpdate, session: AsyncSession) -> User:
    user.firstname = new_data.firstname
    user.lastname = new_data.lastname
    user.email = new_data.email

    await session.commit()
    await session.refresh(user)
    return user


async def patch_user(user: User, data: UserPatch, session: AsyncSession) -> User:
    new_data = data.model_dump(exclude_unset=True)

    for key, value in new_data.items():
        setattr(user, key, value)

    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(user: User, session: AsyncSession):
    await session.delete(user)
    await session.commit()


async def get_user_clients(user_id: int, session: AsyncSession) -> Sequence[Client]:
    result = await session.execute(select(Client).where(Client.user_id == user_id))
    return result.scalars().all()

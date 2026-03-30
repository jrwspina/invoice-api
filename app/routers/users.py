from fastapi import APIRouter, Depends, Response, HTTPException
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    get_users as db_get_users,
    get_user as db_get_user,
    create_user as db_create_user,
    update_user as db_update_user,
    patch_user as db_patch_user,
    delete_user as db_delete_user,
    get_user_clients as db_get_user_clients,
)
from app.database import get_db
from app.schemas import ClientRead, UserCreate, UserPatch, UserRead, UserUpdate


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/", response_model=list[UserRead])
async def get_users(session: Annotated[AsyncSession, Depends(get_db)]):
    return await db_get_users(session)


@router.get("/{user_id}/", response_model=UserRead)
async def get_user(user_id: int, session: Annotated[AsyncSession, Depends(get_db)]):
    result = await db_get_user(user_id, session)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.post("/", response_model=UserRead)
async def create_user(
    user: UserCreate, session: Annotated[AsyncSession, Depends(get_db)]
):
    return await db_create_user(user, session)


@router.put("/{user_id}/", response_model=UserRead)
async def update_user(
    user_id: int, payload: UserUpdate, session: Annotated[AsyncSession, Depends(get_db)]
):
    user = await db_get_user(user_id, session)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await db_update_user(user, payload, session)


@router.patch("/{user_id}/", response_model=UserRead)
async def patch_user(
    user_id: int, payload: UserPatch, session: Annotated[AsyncSession, Depends(get_db)]
):
    user = await db_get_user(user_id, session)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await db_patch_user(user, payload, session)


@router.delete("/{user_id}/")
async def delete_user(user_id: int, session: Annotated[AsyncSession, Depends(get_db)]):

    user = await db_get_user(user_id, session)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db_delete_user(user, session)

    return Response(status_code=204)


@router.get("/{user_id}/clients", response_model=list[ClientRead])
async def get_user_clients(
    user_id: int, session: Annotated[AsyncSession, Depends(get_db)]
):

    user = await db_get_user(user_id, session)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await db_get_user_clients(user_id, session)

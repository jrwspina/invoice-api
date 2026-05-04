from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Annotated
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    create_user as db_create_user,
    update_user as db_update_user,
    patch_user as db_patch_user,
    delete_user as db_delete_user,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import UserCreate, UserPatch, UserRead, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/me", response_model=UserRead)
async def get_user_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.post("/", response_model=UserRead, status_code=201)
async def create_user(
    user: UserCreate, session: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        db_user = await db_create_user(user, session)
        await session.commit()
        await session.refresh(db_user)
        return db_user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")


@router.put("/", response_model=UserRead)
async def update_user(
    payload: UserUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await db_update_user(user, payload, session)


@router.patch("/", response_model=UserRead)
async def patch_user(
    payload: UserPatch,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await db_patch_user(user, payload, session)


@router.delete("/")
async def delete_user(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    await db_delete_user(user, session)

    return Response(status_code=204)

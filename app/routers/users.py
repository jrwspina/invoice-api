from fastapi import APIRouter, Depends, HTTPException, Response, Request
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
from app.limiter import limiter, get_user_key
from app.models import User
from app.schemas import UserCreate, UserPatch, UserRead, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/me", response_model=UserRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def get_user_me(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.post("", response_model=UserRead, status_code=201)
@limiter.limit("5/minute")
async def create_user(
    request: Request,
    user: UserCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        db_user = await db_create_user(user, session)
        await session.commit()
        await session.refresh(db_user)
        return db_user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")


@router.put("", response_model=UserRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def update_user(
    request: Request,
    payload: UserUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await db_update_user(user, payload, session)


@router.patch("", response_model=UserRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def patch_user(
    request: Request,
    payload: UserPatch,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await db_patch_user(user, payload, session)


@router.delete("")
@limiter.limit("60/minute", key_func=get_user_key)
async def delete_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    await db_delete_user(user, session)

    return Response(status_code=204)

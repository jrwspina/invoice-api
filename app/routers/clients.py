from app.redis import get_redis
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from typing import Annotated
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    get_user_clients as db_get_user_clients,
    get_client as db_get_client,
    get_client_nocache as db_get_client_nocache,
    create_client as db_create_client,
    update_client as db_update_client,
    patch_client as db_patch_client,
    delete_client as db_delete_client,
)
from app.database import get_db
from app.dependencies import PaginationParams, get_current_user
from app.limiter import limiter, get_user_key
from app.models import User
from app.schemas import ClientCreate, ClientPatch, ClientRead, ClientUpdate

router = APIRouter(
    prefix="/clients",
    tags=["clients"],
)


@router.get("", response_model=list[ClientRead])
@limiter.limit("60/minute", key_func=get_user_key)
async def get_clients(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    return await db_get_user_clients(
        user.id, session, pagination.limit, pagination.offset
    )


@router.get("/{client_id}", response_model=ClientRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def get_client(
    request: Request,
    client_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    client = await db_get_client(client_id, session, redis)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return client


@router.post("", response_model=ClientRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def create_client(
    request: Request,
    client: ClientCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await db_create_client(client, user.id, session)


@router.put("/{client_id}", response_model=ClientRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def update_client(
    request: Request,
    client_id: int,
    payload: ClientUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    client = await db_get_client_nocache(client_id, session)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return await db_update_client(client, payload, session, redis)


@router.patch("/{client_id}", response_model=ClientRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def patch_client(
    request: Request,
    client_id: int,
    payload: ClientPatch,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    client = await db_get_client_nocache(client_id, session)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return await db_patch_client(client, payload, session, redis)


@router.delete("/{client_id}")
@limiter.limit("60/minute", key_func=get_user_key)
async def delete_client(
    request: Request,
    client_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    client = await db_get_client_nocache(client_id, session)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    await db_delete_client(client, session, redis)

    return Response(status_code=204)

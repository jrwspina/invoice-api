from fastapi import APIRouter, Depends, Response, HTTPException
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    get_user_clients as db_get_user_clients,
    get_client as db_get_client,
    create_client as db_create_client,
    update_client as db_update_client,
    patch_client as db_patch_client,
    delete_client as db_delete_client,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import ClientCreate, ClientPatch, ClientRead, ClientUpdate

router = APIRouter(
    prefix="/clients",
    tags=["clients"],
)


@router.get("", response_model=list[ClientRead])
async def get_clients(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await db_get_user_clients(user.id, session)


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    client = await db_get_client(client_id, session)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.user_id != user.id:
        raise HTTPException(status_code=403)

    return client


@router.post("", response_model=ClientRead)
async def create_client(
    client: ClientCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await db_create_client(client, user.id, session)


@router.put("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: int,
    payload: ClientUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    client = await db_get_client(client_id, session)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.user_id != user.id:
        raise HTTPException(status_code=403)

    return await db_update_client(client, payload, session)


@router.patch("/{client_id}", response_model=ClientRead)
async def patch_client(
    client_id: int,
    payload: ClientPatch,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    client = await db_get_client(client_id, session)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.user_id != user.id:
        raise HTTPException(status_code=403)

    return await db_patch_client(client, payload, session)


@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    client = await db_get_client(client_id, session)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.user_id != user.id:
        raise HTTPException(status_code=403)

    await db_delete_client(client, session)

    return Response(status_code=204)

from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    get_invoice as db_get_invoice,
    get_lineitems as db_get_lineitems,
    get_lineitem as db_get_lineitem,
    create_lineitem as db_create_lineitem,
    delete_lineitem as db_delete_lineitem,
)
from app.database import get_db
from app.dependencies import PaginationParams, get_current_user
from app.models import User
from app.schemas import LineItemRead, LineItemCreate

router = APIRouter(
    prefix="/invoices/{invoice_id}/lineitems",
    tags=["lineitems"],
)


@router.get("", response_model=list[LineItemRead])
async def get_lineitems(
    invoice_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return await db_get_lineitems(invoice, session, pagination.limit, pagination.offset)


@router.post("", response_model=LineItemRead)
async def create_lineitem(
    invoice_id: int,
    payload: LineItemCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return await db_create_lineitem(invoice, payload, session)


@router.delete("/{lineitem_id}")
async def delete_lineitem(
    lineitem_id: int,
    invoice_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    lineitem = await db_get_lineitem(lineitem_id, session)

    if not lineitem:
        raise HTTPException(status_code=404, detail="LineItem not found")

    if invoice.id != lineitem.invoice_id:
        raise HTTPException(
            status_code=403, detail="Invoice id does not match lineitem's invoice id"
        )

    await db_delete_lineitem(lineitem, session)
    return Response(status_code=204)

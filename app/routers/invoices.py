from app.crud.users import get_user
from app.tasks import send_invoice_email
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    get_invoices as db_get_invoices,
    get_invoice as db_get_invoice,
    create_invoice as db_create_invoice,
    update_invoice as db_update_invoice,
    patch_invoice as db_patch_invoice,
    delete_invoice as db_delete_invoice,
    get_client as db_get_client,
    to_invoice_read,
    send_drafted_invoice as db_send_drafted_invoice,
)
from app.database import get_db
from app.dependencies import PaginationParams, get_current_user
from app.limiter import limiter, get_user_key
from app.models import User
from app.schemas import InvoiceRead, InvoiceCreate, InvoicePatch, InvoiceUpdate

router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
)


@router.get("", response_model=list[InvoiceRead])
@limiter.limit("60/minute", key_func=get_user_key)
async def get_invoices(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    result = await db_get_invoices(
        user.id, session, pagination.limit, pagination.offset
    )

    invoices = [to_invoice_read(invoice) for invoice in result]

    return invoices


@router.get("/{invoice_id}", response_model=InvoiceRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def get_invoice(
    request: Request,
    invoice_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return to_invoice_read(invoice)


@router.post("", response_model=InvoiceRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def create_invoice(
    request: Request,
    invoice: InvoiceCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    client = await db_get_client(invoice.client_id, session)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    result = await db_create_invoice(invoice, user.id, session)

    return to_invoice_read(result)


@router.post("/{invoice_id}/send", response_model=InvoiceRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def send_drafted_invoice(
    request: Request,
    invoice_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    client = await db_get_client(invoice.client_id, session)

    if not client:
        raise HTTPException(status_code=400, detail="Invoice has no client")

    if not client.billing_address:
        raise HTTPException(status_code=400, detail="Client has no billing address")

    sent = await db_send_drafted_invoice(invoice, session)

    if not sent:
        raise HTTPException(status_code=400, detail="Invoice not in draft status")

    await session.refresh(invoice)

    send_invoice_email.delay(invoice.id)

    return to_invoice_read(invoice)


@router.put("/{invoice_id}", response_model=InvoiceRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def update_invoice(
    request: Request,
    invoice_id: int,
    payload: InvoiceUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    result = await db_update_invoice(invoice, payload, session)
    return to_invoice_read(result)


@router.patch("/{invoice_id}", response_model=InvoiceRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def patch_invoice(
    request: Request,
    invoice_id: int,
    payload: InvoicePatch,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    effective_due_date = payload.due_date or invoice.due_date
    effective_issue_date = payload.issue_date or invoice.issue_date

    if effective_due_date <= effective_issue_date:
        raise HTTPException(status_code=422, detail="due_date must be after issue_date")

    result = await db_patch_invoice(invoice, payload, session)

    return to_invoice_read(result)


@router.delete("/{invoice_id}")
@limiter.limit("60/minute", key_func=get_user_key)
async def delete_invoice(
    request: Request,
    invoice_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    await db_delete_invoice(invoice, session)

    return Response(status_code=204)

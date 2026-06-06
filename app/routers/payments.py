from app.enums import InvoiceStatus
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.dependencies import PaginationParams, get_current_user
from app.limiter import limiter, get_user_key
from app.models import User
from app.schemas import PaymentRead, PaymentCreate

from app.crud import (
    get_invoice as db_get_invoice,
    get_payment as db_get_payment,
    get_invoice_payments as db_get_invoice_payments,
    create_payment as db_create_payment,
    delete_payment as db_delete_payment,
    update_invoice_status as db_update_invoice_status,
)

router = APIRouter(
    prefix="/invoices/{invoice_id}/payments",
    tags=["payments"],
)


@router.get("", response_model=list[PaymentRead])
@limiter.limit("60/minute", key_func=get_user_key)
async def get_invoice_payments(
    request: Request,
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

    return await db_get_invoice_payments(
        invoice, session, pagination.limit, pagination.offset
    )


@router.get("/{payment_id}", response_model=PaymentRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def get_payment(
    request: Request,
    invoice_id: int,
    payment_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    payment = await db_get_payment(payment_id, session)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.invoice_id != invoice_id:
        raise HTTPException(status_code=400)

    invoice = await db_get_invoice(payment.invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if user.id != invoice.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return payment


@router.post("", response_model=PaymentRead)
@limiter.limit("60/minute", key_func=get_user_key)
async def create_payment(
    request: Request,
    invoice_id: int,
    payload: PaymentCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if user.id != invoice.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if invoice.status == InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Cannot add payment to a draft invoice",
        )

    payment = await db_create_payment(invoice_id, payload, session)

    await session.flush()

    await db_update_invoice_status(invoice_id, session)

    await session.commit()
    await session.refresh(payment)

    return PaymentRead.model_validate(payment)


@router.delete("/{payment_id}")
@limiter.limit("60/minute", key_func=get_user_key)
async def delete_payment(
    request: Request,
    payment_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    payment = await db_get_payment(payment_id, session)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    invoice = await db_get_invoice(payment.invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    await db_delete_payment(payment, session)

    await session.flush()

    await db_update_invoice_status(invoice.id, session)

    await session.commit()

    return Response(status_code=204)

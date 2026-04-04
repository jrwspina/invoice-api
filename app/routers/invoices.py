from fastapi import APIRouter, Depends, Response, HTTPException
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    get_invoices as db_get_invoices,
    get_invoice as db_get_invoice,
    create_invoice as db_create_invoice,
    update_invoice as db_update_invoice,
    patch_invoice as db_patch_invoice,
    delete_invoice as db_delete_invoice,
    to_invoice_read,
)
from app.database import get_db
from app.schemas import InvoiceRead, InvoiceCreate, InvoicePatch, InvoiceUpdate

router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
)


@router.get("/", response_model=list[InvoiceRead])
async def get_invoices(session: Annotated[AsyncSession, Depends(get_db)]):
    result = await db_get_invoices(session)

    invoices = [to_invoice_read(invoice) for invoice in result]

    return invoices


@router.get("/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: int, session: Annotated[AsyncSession, Depends(get_db)]
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return to_invoice_read(invoice)


@router.post("/", response_model=InvoiceRead)
async def create_invoice(
    invoice: InvoiceCreate, session: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db_create_invoice(invoice, session)

    return to_invoice_read(result)


@router.put("/{invoice_id}", response_model=InvoiceRead)
async def update_invoice(
    invoice_id: int,
    payload: InvoiceUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    result = await db_update_invoice(invoice, payload, session)
    return to_invoice_read(result)


@router.patch("/{invoice_id}", response_model=InvoiceRead)
async def patch_invoice(
    invoice_id: int,
    payload: InvoicePatch,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    result = await db_patch_invoice(invoice, payload, session)

    return to_invoice_read(result)


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    invoice = await db_get_invoice(invoice_id, session)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    await db_delete_invoice(invoice, session)

    return Response(status_code=204)

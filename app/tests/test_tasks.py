from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from app.email import build_invoice_email_body, send_overdue_invoice_email
from app.crud import (
    get_invoice as db_get_invoice,
    calculate_total as db_calculate_total,
)
from app.enums import InvoiceStatus
from app.tasks import _send_invoice_email, _update_overdue_invoices


async def test_build_invoice_email_body_returns_correct_body(
    make_user, make_client, make_invoice, make_lineitem, session
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    sample_lineitem_1 = await make_lineitem(sample_invoice)
    sample_lineitem_2 = await make_lineitem(sample_invoice)

    invoice = await db_get_invoice(sample_invoice.id, session)
    assert invoice is not None

    body = build_invoice_email_body(invoice, db_calculate_total(invoice))

    assert f"Invoice #{sample_invoice.id}" in body
    assert sample_lineitem_1.description in body
    assert str(sample_lineitem_1.quantity) in body
    assert str(sample_lineitem_1.unit_price) in body
    assert sample_lineitem_2.description in body
    assert str(sample_lineitem_2.quantity) in body
    assert str(sample_lineitem_2.unit_price) in body


async def test_build_invoice_email_body_with_no_lineitems(
    make_user, make_client, make_invoice, session
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)

    invoice = await db_get_invoice(sample_invoice.id, session)
    assert invoice is not None

    body = build_invoice_email_body(invoice, db_calculate_total(invoice))

    assert f"Invoice #{sample_invoice.id}" in body
    assert "Items:" in body


async def test_send_invoice_email_sends_email_with_correct_subject_and_address(
    session, make_user, make_client, make_invoice
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)

    with patch("app.tasks.send_email") as mock_email:
        await _send_invoice_email(sample_invoice.id, session)
        mock_email.assert_called_once()
        to_addr, subject, body = mock_email.call_args.args

        assert sample_client.email == to_addr
        assert f"Invoice #{sample_invoice.id}" in subject
        assert f"{sample_user.firstname}" in subject
        assert f"{sample_user.lastname}" in subject


async def test_invoice_send_email_not_called_when_invoice_nonexistent(session):
    with patch("app.tasks.send_email") as mock_email:
        await _send_invoice_email(999999, session)
        mock_email.assert_not_called()


async def test_send_overdue_invoice_email(
    session, make_user, make_client, make_invoice
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)

    invoice = await db_get_invoice(sample_invoice.id, session)

    assert invoice is not None

    with patch("app.email.send_email") as mock_email:
        send_overdue_invoice_email(invoice)
        mock_email.assert_called_once()
        to_addr, subject, body = mock_email.call_args.args

        assert sample_client.email == to_addr
        assert f"OVERDUE: Invoice #{sample_invoice.id}" in subject
        assert f"{sample_user.firstname}" in subject
        assert f"{sample_user.lastname}" in subject


async def test_update_invoice_status_with_overdue_status_and_send_email(
    session, make_user, make_client, make_invoice
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(
        sample_user,
        sample_client,
        status=InvoiceStatus.SENT,
        due_date=(datetime.now(timezone.utc) - timedelta(days=1)),
    )

    with patch("app.tasks.send_overdue_invoice_email") as mock_email:
        await _update_overdue_invoices(session)
        await session.refresh(sample_invoice)
        assert sample_invoice.status == InvoiceStatus.OVERDUE
        mock_email.assert_called_once()


async def test_overdue_invoice_email_not_sent_again_when_previously_sent(
    session, make_user, make_client, make_invoice
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(
        sample_user,
        sample_client,
        status=InvoiceStatus.SENT,
        due_date=(datetime.now(timezone.utc) - timedelta(days=1)),
        reminder_sent_at=(datetime.now(timezone.utc)),
    )

    with patch("app.tasks.send_overdue_invoice_email") as mock_email:
        await _update_overdue_invoices(session)
        await session.refresh(sample_invoice)
        assert sample_invoice.status == InvoiceStatus.OVERDUE
        mock_email.assert_not_called()

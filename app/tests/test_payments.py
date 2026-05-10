from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.enums import InvoiceStatus
from app.models import Invoice, Payment


async def test_get_payments_returns_200_and_includes_payments(
    client, make_user, make_client, make_invoice, make_payment, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    sample_payment_1 = await make_payment(sample_invoice)
    sample_payment_2 = await make_payment(sample_invoice)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        f"/invoices/{sample_invoice.id}/payments/",
        headers=auth_headers,
    )

    assert response.status_code == 200

    payment_ids = [p["id"] for p in response.json()]

    assert sample_payment_1.id in payment_ids
    assert sample_payment_2.id in payment_ids


async def test_get_payments_from_other_users_invoice_returns_403(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()
    sample_client = await make_client(sample_user_2)
    sample_invoice = await make_invoice(sample_user_2, sample_client)
    auth_headers = await make_auth_headers(sample_user_1)

    response = await client.get(
        f"/invoices/{sample_invoice.id}/payments/",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_get_payment_returns_200_and_payment(
    client, make_user, make_client, make_invoice, make_payment, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    sample_payment = await make_payment(sample_invoice)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        f"invoices/{sample_invoice.id}/payments/{sample_payment.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["id"] == sample_payment.id
    assert response_data["invoice_id"] == sample_payment.invoice_id
    assert response_data["paid_at"] == sample_payment.paid_at.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    assert Decimal(response_data["value"]) == Decimal(sample_payment.value)


async def test_get_payment_nonexistent_returns_404(
    client, make_user, make_client, make_invoice, make_payment, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        f"invoices/{sample_invoice.id}/payments/9999999",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


async def test_get_payment_from_other_user_returns_403(
    client, make_user, make_client, make_invoice, make_payment, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()
    sample_client = await make_client(sample_user_2)
    sample_invoice = await make_invoice(sample_user_2, sample_client)
    sample_payment = await make_payment(sample_invoice)
    auth_headers = await make_auth_headers(sample_user_1)

    response = await client.get(
        f"invoices/{sample_invoice.id}/payments/{sample_payment.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_post_payment_returns_200_and_payment(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(
        sample_user, sample_client, status=InvoiceStatus.SENT
    )
    auth_headers = await make_auth_headers(sample_user)

    payment = {
        "paid_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "value": 100,
    }

    response = await client.post(
        f"/invoices/{sample_invoice.id}/payments/",
        json=payment,
        headers=auth_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert "id" in response_data
    assert response_data["id"] is not None
    assert response_data["invoice_id"] == sample_invoice.id
    assert response_data["paid_at"] == payment["paid_at"]
    assert Decimal(response_data["value"]) == Decimal(payment["value"])


async def test_post_payment_invoice_nonexistent_returns_404(
    client, make_user, make_auth_headers
):
    sample_user = await make_user()
    auth_headers = await make_auth_headers(sample_user)

    payment = {
        "paid_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "value": 100,
    }

    response = await client.post(
        "/invoices/999999/payments/",
        json=payment,
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_post_payment_invoice_from_other_user_returns_403(
    client, make_user, make_client, make_invoice, make_payment, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()
    sample_client = await make_client(sample_user_2)
    sample_invoice = await make_invoice(sample_user_2, sample_client)
    auth_headers = await make_auth_headers(sample_user_1)

    payment = {
        "paid_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "value": 100,
    }

    response = await client.post(
        f"/invoices/{sample_invoice.id}/payments/",
        json=payment,
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_delete_payment_returns_204_and_payment_is_deleted_from_db(
    client,
    make_user,
    make_client,
    make_invoice,
    make_payment,
    make_auth_headers,
    session,
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    sample_payment = await make_payment(sample_invoice)
    auth_headers = await make_auth_headers(sample_user)

    payment_id = sample_payment.id

    response = await client.delete(
        f"/invoices/{sample_invoice.id}/payments/{sample_payment.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = await client.get(
        f"/invoices/{sample_invoice.id}/payments/{sample_payment.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404

    session.expire_all()

    result = await session.get(Payment, payment_id)

    assert result is None


async def test_delete_payment_nonexistent_returns_404(
    client, make_user, make_client, make_invoice, make_payment, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.delete(
        f"/invoices/{sample_invoice.id}/payments/9999999",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_delete_payment_from_other_user_returns_403(
    client, make_user, make_client, make_invoice, make_payment, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()
    sample_client = await make_client(sample_user_2)
    sample_invoice = await make_invoice(sample_user_2, sample_client)
    sample_payment = await make_payment(sample_invoice)
    auth_headers = await make_auth_headers(sample_user_1)

    response = await client.delete(
        f"/invoices/{sample_invoice.id}/payments/{sample_payment.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_post_payment_on_draft_invoice_returns_400(
    client, make_user, make_client, make_invoice, make_lineitem, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    sample_lineitem = await make_lineitem(sample_invoice)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "draft"

    payment = {
        "paid_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "value": float(sample_lineitem.unit_price * sample_lineitem.quantity) / 2,
    }

    response = await client.post(
        f"/invoices/{sample_invoice.id}/payments/",
        json=payment,
        headers=auth_headers,
    )

    assert response.status_code == 400


async def test_post_payment_partial_value_status_becomes_partially_paid(
    client, make_user, make_client, make_invoice, make_lineitem, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(
        sample_user, sample_client, status=InvoiceStatus.SENT
    )
    sample_lineitem = await make_lineitem(sample_invoice)
    auth_headers = await make_auth_headers(sample_user)

    payment = {
        "paid_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "value": float(sample_lineitem.unit_price * sample_lineitem.quantity) / 2,
    }

    response = await client.post(
        f"/invoices/{sample_invoice.id}/payments/",
        json=payment,
        headers=auth_headers,
    )

    assert response.status_code == 200

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == InvoiceStatus.PARTIALLY_PAID.value


async def test_post_payment_full_value_status_becomes_paid(
    client, make_user, make_client, make_invoice, make_lineitem, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(
        sample_user, sample_client, status=InvoiceStatus.SENT
    )
    sample_lineitem = await make_lineitem(sample_invoice)
    auth_headers = await make_auth_headers(sample_user)

    payment = {
        "paid_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "value": float(sample_lineitem.unit_price * sample_lineitem.quantity),
    }

    response = await client.post(
        f"/invoices/{sample_invoice.id}/payments/",
        json=payment,
        headers=auth_headers,
    )

    assert response.status_code == 200

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == InvoiceStatus.PAID.value


async def test_delete_payment_brings_total_paid_below_total_changes_status_to_partially_paid(
    client,
    make_user,
    make_client,
    make_invoice,
    make_lineitem,
    make_payment,
    make_auth_headers,
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(
        sample_user, sample_client, status=InvoiceStatus.SENT
    )
    sample_lineitem = await make_lineitem(sample_invoice)
    sample_payment = await make_payment(
        sample_invoice,
        value=float(sample_lineitem.unit_price * sample_lineitem.quantity) / 2,
    )
    auth_headers = await make_auth_headers(sample_user)

    payment = {
        "paid_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "value": float(sample_lineitem.unit_price * sample_lineitem.quantity) / 2,
    }

    response = await client.post(
        f"/invoices/{sample_invoice.id}/payments/",
        json=payment,
        headers=auth_headers,
    )

    assert response.status_code == 200

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == InvoiceStatus.PAID.value

    response = await client.delete(
        f"/invoices/{sample_invoice.id}/payments/{sample_payment.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == InvoiceStatus.PARTIALLY_PAID.value


async def test_delete_payment_brings_total_paid_to_zero_changes_status_to_sent(
    client,
    make_user,
    make_client,
    make_invoice,
    make_lineitem,
    make_auth_headers,
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(
        sample_user, sample_client, status=InvoiceStatus.SENT
    )
    sample_lineitem = await make_lineitem(sample_invoice)
    auth_headers = await make_auth_headers(sample_user)

    payment = {
        "paid_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "value": float(sample_lineitem.unit_price * sample_lineitem.quantity),
    }

    response = await client.post(
        f"/invoices/{sample_invoice.id}/payments/",
        json=payment,
        headers=auth_headers,
    )

    assert response.status_code == 200
    payment_id = response.json()["id"]

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == InvoiceStatus.PAID.value

    response = await client.delete(
        f"/invoices/{sample_invoice.id}/payments/{payment_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == InvoiceStatus.SENT.value


async def test_post_payment_increases_total_paid(
    client,
    make_user,
    make_client,
    make_invoice,
    make_lineitem,
    make_auth_headers,
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(
        sample_user, sample_client, status=InvoiceStatus.SENT
    )
    sample_lineitem = await make_lineitem(sample_invoice)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert Decimal(response.json()["total_paid"]) == Decimal(0)

    payment = {
        "paid_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "value": float(sample_lineitem.unit_price * sample_lineitem.quantity),
    }

    response = await client.post(
        f"/invoices/{sample_invoice.id}/payments/",
        json=payment,
        headers=auth_headers,
    )

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert Decimal(response.json()["total_paid"]) == Decimal(payment["value"])


async def test_delete_payment_decreases_total_paid(
    client,
    make_user,
    make_client,
    make_invoice,
    make_lineitem,
    make_payment,
    make_auth_headers,
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(
        sample_user, sample_client, status=InvoiceStatus.SENT
    )
    sample_lineitem = await make_lineitem(sample_invoice)
    sample_payment = await make_payment(sample_invoice)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert Decimal(response.json()["total_paid"]) == Decimal(sample_payment.value)

    response = await client.delete(
        f"/invoices/{sample_invoice.id}/payments/{sample_payment.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert Decimal(response.json()["total_paid"]) == Decimal(0)

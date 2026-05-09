from datetime import datetime, timedelta, timezone

from app.enums import InvoiceStatus
from app.models import Invoice


async def test_get_invoices_return_200_and_list_invoices(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice_1 = await make_invoice(sample_user, sample_client)
    sample_invoice_2 = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        "/invoices/",
        headers=auth_headers,
    )

    assert response.status_code == 200

    invoice_ids = [i["id"] for i in response.json()]

    assert sample_invoice_1.id in invoice_ids
    assert sample_invoice_2.id in invoice_ids


async def test_get_invoice_by_id_returns_200_and_invoice(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert "id" in response_data
    assert response_data["id"] == sample_invoice.id
    assert response_data["user_id"] == sample_user.id
    assert response_data["client_id"] == sample_client.id
    assert response_data["status"] == sample_invoice.status.value
    assert "total" in response_data
    assert response_data["total"] == "0"
    assert "total_paid" in response_data
    assert response_data["total_paid"] == "0"


async def test_get_invoice_nonexistent_returns_404(
    client, make_user, make_auth_headers
):
    sample_user = await make_user()
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        "/invoices/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_get_invoice_from_other_user_returns_403(
    client,
    make_user,
    make_client,
    make_invoice,
    make_auth_headers,
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()
    sample_client = await make_client(sample_user_2)
    sample_invoice = await make_invoice(sample_user_2, sample_client)
    auth_headers = await make_auth_headers(sample_user_1)

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_post_invoice_returns_200_and_invoice(
    client, make_user, make_client, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    auth_headers = await make_auth_headers(sample_user)

    now = datetime.now(timezone.utc).replace(microsecond=0)
    dt = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    due_dt = (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    response = await client.post(
        "/invoices/",
        json={
            "issue_date": dt,
            "due_date": due_dt,
            "client_id": sample_client.id,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["issue_date"] == dt
    assert response_data["due_date"] == due_dt
    assert response_data["user_id"] == sample_user.id
    assert response_data["client_id"] == sample_client.id
    assert response_data["status"] == "draft"
    assert response_data["total"] == "0"
    assert response_data["total_paid"] == "0"


async def test_put_invoice_replaces_fields_returns_200_and_invoice(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    now = datetime.now(timezone.utc).replace(microsecond=0)
    dt = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    due_dt = (now + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

    response = await client.put(
        f"/invoices/{sample_invoice.id}",
        json={
            "issue_date": dt,
            "due_date": due_dt,
            "notes": "notes",
            "status": "draft",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["id"] == sample_invoice.id
    assert response_data["user_id"] == sample_invoice.user_id
    assert response_data["client_id"] == sample_invoice.client_id
    assert response_data["issue_date"] == dt
    assert response_data["due_date"] == due_dt
    assert response_data["notes"] == "notes"
    assert response_data["status"] == "draft"


async def test_put_invoice_from_other_user_returns_403(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()
    sample_client = await make_client(sample_user_2)
    sample_invoice = await make_invoice(sample_user_2, sample_client)
    auth_headers = await make_auth_headers(sample_user_1)

    now = datetime.now(timezone.utc).replace(microsecond=0)
    dt = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    due_dt = (now + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

    response = await client.put(
        f"/invoices/{sample_invoice.id}",
        json={
            "issue_date": dt,
            "due_date": due_dt,
            "notes": "notes",
            "status": InvoiceStatus.SENT.value,
        },
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_patch_invoice_replaces_specified_fields_returns_200_and_invoice(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    now = datetime.now(timezone.utc).replace(microsecond=0)
    due_dt = (now + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

    response = await client.patch(
        f"/invoices/{sample_invoice.id}",
        json={
            "due_date": due_dt,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["id"] == sample_invoice.id
    assert response_data["issue_date"] == sample_invoice.issue_date.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    assert response_data["due_date"] == due_dt
    assert response_data["notes"] == sample_invoice.notes
    assert response_data["status"] == sample_invoice.status.value


async def test_patch_invoice_from_other_user_returns_403(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()
    sample_client = await make_client(sample_user_2)
    sample_invoice = await make_invoice(sample_user_2, sample_client)
    auth_headers = await make_auth_headers(sample_user_1)

    now = datetime.now(timezone.utc).replace(microsecond=0)
    due_dt = (now + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

    response = await client.patch(
        f"/invoices/{sample_invoice.id}",
        json={
            "due_date": due_dt,
            "status": InvoiceStatus.SENT.value,
        },
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_delete_invoice_returns_204_and_invoice_deleted_from_db(
    client, make_user, make_client, make_invoice, make_auth_headers, session
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    invoice_id = sample_invoice.id

    response = await client.delete(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = await client.delete(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404

    session.expire_all()

    result = await session.get(Invoice, invoice_id)

    assert result is None


async def test_delete_invoice_nonexistent_returns_404(
    client, make_user, make_auth_headers
):
    sample_user = await make_user()
    auth_headers = await make_auth_headers(sample_user)

    response = await client.delete(
        "/invoices/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_delete_invoice_from_other_user_returns_403(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()
    sample_client = await make_client(sample_user_2)
    sample_invoice = await make_invoice(sample_user_2, sample_client)
    auth_headers = await make_auth_headers(sample_user_1)

    response = await client.delete(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_send_draft_invoice_with_client_without_field_billing_address_returns_400(
    client,
    make_user,
    make_client,
    make_invoice,
    make_auth_headers,
    mock_send_invoice_email,
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    assert sample_client.billing_address is None

    response = await client.post(
        f"/invoices/{sample_invoice.id}/send",
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Client has no billing address"


async def test_send_draft_invoice_with_valid_client_returns_200_and_status_is_sent(
    client,
    make_user,
    make_client,
    make_invoice,
    make_auth_headers,
    mock_send_invoice_email,
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user, billing_address="address")
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    assert sample_client.billing_address is not None

    response = await client.post(
        f"/invoices/{sample_invoice.id}/send",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == InvoiceStatus.SENT.value


async def test_send_sent_invoice_returns_400(
    client,
    make_user,
    make_client,
    make_invoice,
    make_auth_headers,
    mock_send_invoice_email,
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user, billing_address="address")
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    assert sample_client.billing_address is not None

    response = await client.post(
        f"/invoices/{sample_invoice.id}/send",
        headers=auth_headers,
    )

    assert response.json()["status"] == InvoiceStatus.SENT.value

    response = await client.post(
        f"/invoices/{sample_invoice.id}/send",
        headers=auth_headers,
    )

    assert response.status_code == 400

    assert response.json()["detail"] == "Invoice not in draft status"


async def test_send_invoice_from_other_user_returns_403(
    client,
    make_user,
    make_client,
    make_invoice,
    make_auth_headers,
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()
    sample_client = await make_client(sample_user_2, billing_address="address")
    sample_invoice = await make_invoice(sample_user_2, sample_client)
    auth_headers = await make_auth_headers(sample_user_1)

    response = await client.post(
        f"/invoices/{sample_invoice.id}/send",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_invoice_total_without_lineitems_is_zero(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.json()["total"] == str(0)


async def test_invoice_total_reflects_lineitems_correctly(
    client, make_user, make_client, make_invoice, make_lineitem, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    sample_lineitem_1 = await make_lineitem(sample_invoice)

    expected_total = sample_lineitem_1.unit_price * sample_lineitem_1.quantity

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.json()["total"] == str(expected_total)

    sample_lineitem_2 = await make_lineitem(sample_invoice, quantity=2, unit_price=300)

    expected_total += sample_lineitem_2.unit_price * sample_lineitem_2.quantity

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.json()["total"] == str(expected_total)


async def test_invoice_total_paid_without_payments_is_zero(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.json()["total_paid"] == str(0)


async def test_invoice_total_paid_reflects_payments_correctly(
    client, make_user, make_client, make_invoice, make_payment, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    sample_payment_1 = await make_payment(sample_invoice)

    expected_total = sample_payment_1.value

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.json()["total_paid"] == str(expected_total)

    sample_payment_2 = await make_payment(sample_invoice, value=200)

    expected_total += sample_payment_2.value

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.json()["total_paid"] == str(expected_total)

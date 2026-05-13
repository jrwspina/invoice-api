from decimal import Decimal
from app.models import LineItem


async def test_get_lineitems_returns_200_and_list_lineitems(
    client, make_user, make_client, make_invoice, make_lineitem, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    sample_lineitem_1 = await make_lineitem(sample_invoice)
    sample_lineitem_2 = await make_lineitem(sample_invoice)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        f"/invoices/{sample_invoice.id}/lineitems",
        headers=auth_headers,
    )

    assert response.status_code == 200

    lineitem_ids = [i["id"] for i in response.json()]

    assert sample_lineitem_1.id in lineitem_ids
    assert sample_lineitem_2.id in lineitem_ids


async def test_get_lineitems_returns_200_and_lineitems_fields_correct(
    client, make_user, make_client, make_invoice, make_lineitem, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    sample_lineitem_1 = await make_lineitem(sample_invoice)
    sample_lineitem_2 = await make_lineitem(sample_invoice)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        f"/invoices/{sample_invoice.id}/lineitems",
        headers=auth_headers,
    )

    assert response.status_code == 200

    lineitems = {li["id"]: li for li in response.json()}

    for sample_lineitem in [sample_lineitem_1, sample_lineitem_2]:
        assert sample_lineitem.id in lineitems
        item = lineitems[sample_lineitem.id]
        assert item["id"] == sample_lineitem.id
        assert item["invoice_id"] == sample_lineitem.invoice_id
        assert item["description"] == sample_lineitem.description
        assert item["quantity"] == str(sample_lineitem.quantity)
        assert item["unit_price"] == str(sample_lineitem.unit_price)


async def test_get_lineitems_from_other_user_returns_403(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()
    sample_client = await make_client(sample_user_2)
    sample_invoice = await make_invoice(sample_user_2, sample_client)
    auth_headers = await make_auth_headers(sample_user_1)

    response = await client.get(
        f"/invoices/{sample_invoice.id}/lineitems",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_post_lineitem_returns_200_and_lineitem(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.post(
        f"/invoices/{sample_invoice.id}/lineitems",
        json={
            "description": "item",
            "quantity": 1,
            "unit_price": 100,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["description"] == "item"
    assert response_data["quantity"] == f"{1:.2f}"
    assert response_data["unit_price"] == f"{100:.2f}"


async def test_post_lineitem_to_other_users_invoice_returns_403(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()
    sample_client = await make_client(sample_user_2)
    sample_invoice = await make_invoice(sample_user_2, sample_client)
    auth_headers = await make_auth_headers(sample_user_1)

    response = await client.post(
        f"/invoices/{sample_invoice.id}/lineitems",
        json={
            "description": "item",
            "quantity": 1,
            "unit_price": 100,
        },
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_post_lineitem_to_nonexistent_invoice_returns_404(
    client, make_user, make_auth_headers
):
    sample_user = await make_user()
    auth_headers = await make_auth_headers(sample_user)

    response = await client.post(
        "/invoices/9999999/lineitems",
        json={
            "description": "item",
            "quantity": 1,
            "unit_price": 100,
        },
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_delete_lineitem_returns_204_and_lineitem_is_gone_from_db(
    client,
    make_user,
    make_client,
    make_invoice,
    make_lineitem,
    make_auth_headers,
    session,
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    sample_lineitem = await make_lineitem(sample_invoice)
    auth_headers = await make_auth_headers(sample_user)

    lineitem_id = sample_lineitem.id

    response = await client.delete(
        f"/invoices/{sample_invoice.id}/lineitems/{sample_lineitem.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = await client.delete(
        f"/invoices/{sample_invoice.id}/lineitems/{sample_lineitem.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404

    session.expire_all()

    result = await session.get(LineItem, lineitem_id)

    assert result is None


async def test_delete_lineitem_nonexistent_returns_404(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    response = await client.delete(
        f"/invoices/{sample_invoice.id}/lineitems/99999999",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_delete_lineitem_from_other_user_returns_403(
    client, make_user, make_client, make_invoice, make_lineitem, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()
    sample_client = await make_client(sample_user_2)
    sample_invoice = await make_invoice(sample_user_2, sample_client)
    sample_lineitem = await make_lineitem(sample_invoice)
    auth_headers = await make_auth_headers(sample_user_1)

    response = await client.delete(
        f"/invoices/{sample_invoice.id}/lineitems/{sample_lineitem.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_post_lineitem_increases_invoice_total(
    client, make_user, make_client, make_invoice, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)
    auth_headers = await make_auth_headers(sample_user)

    lineitem_1 = {
        "description": "item",
        "quantity": 1,
        "unit_price": 100,
    }

    response = await client.post(
        f"/invoices/{sample_invoice.id}/lineitems",
        json=lineitem_1,
        headers=auth_headers,
    )

    assert response.status_code == 200
    expected_total = Decimal(lineitem_1["quantity"]) * Decimal(lineitem_1["unit_price"])

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert Decimal(response.json()["total"]) == expected_total

    lineitem_2 = {
        "description": "item",
        "quantity": 2,
        "unit_price": 300,
    }

    response = await client.post(
        f"/invoices/{sample_invoice.id}/lineitems",
        json=lineitem_2,
        headers=auth_headers,
    )

    assert response.status_code == 200
    expected_total += Decimal(lineitem_2["quantity"]) * Decimal(
        lineitem_2["unit_price"]
    )

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert Decimal(response.json()["total"]) == expected_total


async def test_delete_lineitem_decreases_invoice_total(
    client, make_user, make_client, make_invoice, make_lineitem, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    sample_invoice = await make_invoice(sample_user, sample_client)

    auth_headers = await make_auth_headers(sample_user)

    sample_lineitem_1 = await make_lineitem(sample_invoice)

    expected_total = sample_lineitem_1.quantity * sample_lineitem_1.unit_price

    sample_lineitem_2 = await make_lineitem(sample_invoice)

    expected_total += sample_lineitem_2.quantity * sample_lineitem_2.unit_price

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert Decimal(response.json()["total"]) == expected_total

    response = await client.delete(
        f"/invoices/{sample_invoice.id}/lineitems/{sample_lineitem_1.id}",
        headers=auth_headers,
    )

    expected_total -= sample_lineitem_1.quantity * sample_lineitem_1.unit_price

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert Decimal(response.json()["total"]) == expected_total

    response = await client.delete(
        f"/invoices/{sample_invoice.id}/lineitems/{sample_lineitem_2.id}",
        headers=auth_headers,
    )

    expected_total -= sample_lineitem_2.quantity * sample_lineitem_2.unit_price

    response = await client.get(
        f"/invoices/{sample_invoice.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert Decimal(response.json()["total"]) == expected_total

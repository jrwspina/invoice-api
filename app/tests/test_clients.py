import uuid


async def test_get_clients_for_authenticated_user_returns_200_and_list_clients(
    client,
    make_user,
    make_auth_headers,
    make_client,
):
    sample_user = await make_user()
    auth_headers = await make_auth_headers(sample_user)
    sample_client = await make_client(sample_user)

    response = await client.get(
        "/clients/",
        headers=auth_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert isinstance(response_data, list)
    assert any(c["email"] == sample_client.email for c in response_data)


async def test_get_clients_without_token_return_401(client):
    response = await client.get(
        "/clients/",
    )

    assert response.status_code == 401


async def test_get_client_by_id_for_existing_client_returns_200_and_client(
    client,
    make_user,
    make_client,
    make_auth_headers,
):
    sample_user = await make_user()
    auth_headers = await make_auth_headers(sample_user)
    sample_client = await make_client(sample_user)

    response = await client.get(
        f"/clients/{sample_client.id}/",
        headers=auth_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["id"] == sample_client.id
    assert response_data["user_id"] == sample_client.user_id
    assert response_data["email"] == sample_client.email
    assert response_data["firstname"] == sample_client.firstname
    assert response_data["lastname"] == sample_client.lastname
    assert response_data["phone"] == sample_client.phone
    assert response_data["company"] == sample_client.company
    assert response_data["billing_address"] == sample_client.billing_address


async def test_get_client_nonexisting_returns_404(client, make_user, make_auth_headers):
    sample_user = await make_user()
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        "/clients/99999/",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_get_client_from_other_user_returns_403(
    client, make_user, make_client, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()

    sample_client = await make_client(sample_user_2)

    auth_headers = await make_auth_headers(sample_user_1)

    response = await client.get(
        f"/clients/{sample_client.id}/",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_get_client_without_token_returns_401(client, make_user, make_client):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)

    response = await client.get(
        f"/clients/{sample_client.id}/",
    )

    assert response.status_code == 401


async def test_post_client_with_required_field_returns_200_and_client(
    client, make_user, make_auth_headers
):
    sample_user = await make_user()
    auth_headers = await make_auth_headers(sample_user)
    sample_email = f"{uuid.uuid4()}@test.com"

    response = await client.post(
        "/clients/",
        json={
            "firstname": "firstname",
            "lastname": "lastname",
            "email": sample_email,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert "id" in response_data
    assert response_data["id"] is not None
    assert response_data["firstname"] == "firstname"
    assert response_data["lastname"] == "lastname"
    assert response_data["email"] == sample_email
    assert response_data["phone"] is None
    assert response_data["company"] is None
    assert response_data["billing_address"] is None


async def test_post_client_with_all_field_returns_200_and_client(
    client, make_user, make_auth_headers
):
    sample_user = await make_user()
    auth_headers = await make_auth_headers(sample_user)
    sample_email = f"{uuid.uuid4()}@test.com"

    response = await client.post(
        "/clients/",
        json={
            "firstname": "firstname",
            "lastname": "lastname",
            "email": sample_email,
            "phone": "123456789",
            "company": "company",
            "billing_address": "address",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert "id" in response_data
    assert response_data["id"] is not None
    assert response_data["firstname"] == "firstname"
    assert response_data["lastname"] == "lastname"
    assert response_data["email"] == sample_email
    assert response_data["phone"] == "123456789"
    assert response_data["company"] == "company"
    assert response_data["billing_address"] == "address"


async def test_put_client_returns_200_and_updated_client(
    client, make_user, make_client, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    auth_headers = await make_auth_headers(sample_user)
    sample_email = f"{uuid.uuid4()}@test.com"

    response = await client.put(
        f"/clients/{sample_client.id}/",
        json={
            "firstname": "new firstname",
            "lastname": "new lastname",
            "email": sample_email,
            "phone": "987654321",
            "company": "new company",
            "billing_address": "new address",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert "id" in response_data
    assert response_data["id"] is not None
    assert response_data["firstname"] == "new firstname"
    assert response_data["lastname"] == "new lastname"
    assert response_data["email"] == sample_email
    assert response_data["phone"] == "987654321"
    assert response_data["company"] == "new company"
    assert response_data["billing_address"] == "new address"


async def test_put_client_nonexistent_returns_404(client, make_user, make_auth_headers):
    sample_user = await make_user()
    auth_headers = await make_auth_headers(sample_user)
    sample_email = f"{uuid.uuid4()}@test.com"

    response = await client.put(
        "/clients/9999/",
        json={
            "firstname": "new firstname",
            "lastname": "new lastname",
            "email": sample_email,
            "phone": "987654321",
            "company": "new company",
            "billing_address": "new address",
        },
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_put_client_from_other_user_returns_403(
    client, make_user, make_client, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()

    sample_client = await make_client(sample_user_2)
    auth_headers = await make_auth_headers(sample_user_1)

    sample_email = f"{uuid.uuid4()}@test.com"

    response = await client.put(
        f"/clients/{sample_client.id}/",
        json={
            "firstname": "new firstname",
            "lastname": "new lastname",
            "email": sample_email,
            "phone": "987654321",
            "company": "new company",
            "billing_address": "new address",
        },
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_patch_client_only_updates_specified_fields_returns_200_and_client(
    client, make_user, make_client, make_auth_headers
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    auth_headers = await make_auth_headers(sample_user)

    sample_email = f"{uuid.uuid4()}@test.com"

    response = await client.patch(
        f"/clients/{sample_client.id}/",
        json={
            "firstname": "new firstname",
            "email": sample_email,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["id"] == sample_client.id
    assert response_data["firstname"] == "new firstname"
    assert response_data["lastname"] == sample_client.lastname
    assert response_data["email"] == sample_email
    assert response_data["phone"] == sample_client.phone
    assert response_data["company"] == sample_client.company
    assert response_data["billing_address"] == sample_client.billing_address


async def test_patch_client_from_other_user_returns_403(
    client, make_user, make_client, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()

    sample_client = await make_client(sample_user_2)
    auth_headers = await make_auth_headers(sample_user_1)

    sample_email = f"{uuid.uuid4()}@test.com"

    response = await client.patch(
        f"/clients/{sample_client.id}/",
        json={
            "firstname": "new firstname",
            "email": sample_email,
        },
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_delete_client_returns_204_and_client_deleted_from_db(
    client, make_user, make_client, make_auth_headers, session
):
    sample_user = await make_user()
    sample_client = await make_client(sample_user)
    auth_headers = await make_auth_headers(sample_user)

    client_id = sample_client.id

    response = await client.delete(
        f"/clients/{sample_client.id}/",
        headers=auth_headers,
    )

    assert response.status_code == 204

    session.expire_all()

    from app.models import Client

    result = await session.get(Client, client_id)
    assert result is None

    response = await client.get(
        f"/clients/{client_id}/",
        headers=auth_headers,
    )

    assert response.status_code == 404

    response = await client.delete(
        f"/clients/{client_id}/",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_delete_client_nonexistent_returns_404(
    client, make_user, make_client, make_auth_headers
):
    sample_user = await make_user()
    auth_headers = await make_auth_headers(sample_user)

    response = await client.delete("/clients/9999/", headers=auth_headers)

    assert response.status_code == 404


async def test_delete_client_from_other_user_returns_403(
    client, make_user, make_client, make_auth_headers
):
    sample_user_1 = await make_user()
    sample_user_2 = await make_user()

    sample_client = await make_client(sample_user_2)
    auth_headers = await make_auth_headers(sample_user_1)

    response = await client.delete(
        f"/clients/{sample_client.id}/",
        headers=auth_headers,
    )

    assert response.status_code == 403

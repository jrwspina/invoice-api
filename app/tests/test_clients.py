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

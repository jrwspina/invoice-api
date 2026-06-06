async def test_login_correct_password_returns_200_and_token(client, make_user):
    sample_user = await make_user()

    response = await client.post(
        "auth/token",
        data={
            "username": sample_user.email,
            "password": "password",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


async def test_login_incorrect_password_returns_401(client, make_user):
    sample_user = await make_user()

    response = await client.post(
        "auth/token",
        data={
            "username": sample_user.email,
            "password": "passssssword",
        },
    )

    assert response.status_code == 401


async def test_login_non_registered_email_returns_401(client):
    response = await client.post(
        "/auth/token",
        data={
            "username": "email@email.email",
            "password": "password",
        },
    )

    assert response.status_code == 401


async def test_access_protected_endpoint_without_token_returns_401(client):
    response = await client.get("/clients")

    assert response.status_code == 401


async def test_access_protected_endpoint_with_token_returns_200(
    client, make_user, make_auth_headers
):
    sample_user = await make_user()
    auth_headers = await make_auth_headers(sample_user)

    response = await client.get(
        "/clients",
        headers=auth_headers,
    )

    assert response.status_code == 200


async def test_limiting_on_login_endpoint_returns_429_after_limit_exceeded(client):
    responses = []
    for _ in range(6):
        response = await client.post(
            "/auth/token",
            data={"username": "idontexist@email.com", "password": "password"},
        )
        responses.append(response.status_code)

    assert responses.pop() == 429

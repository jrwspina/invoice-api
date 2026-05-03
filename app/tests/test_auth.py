async def test_login_correct_password(client, sample_user):
    """
    Login with correct credentials returns a token
    """
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


async def test_login_incorrect_password(client, sample_user):
    """
    Login with wrong password returns 401
    """

    response = await client.post(
        "auth/token",
        data={
            "username": sample_user.email,
            "password": "passssssword",
        },
    )

    assert response.status_code == 401


async def test_login_non_registered_email(client):
    """
    Login with nonexistent email returns 401
    """
    response = await client.post(
        "/auth/token",
        data={
            "username": "email@email.email",
            "password": "password",
        },
    )

    assert response.status_code == 401


async def test_access_protected_endpoint_without_token(client):
    """
    Accessing a protected endpoint without a token returns 401
    """
    response = await client.get("/clients/")

    assert response.status_code == 401


async def test_access_protected_endpoint_with_token(client, auth_headers):
    """
    Accessing a protected endpoint with a valid token returns 200
    """

    response = await client.get(
        "/clients/",
        headers=auth_headers,
    )

    assert response.status_code == 200

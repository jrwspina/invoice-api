from app.models import User


async def test_create_new_user_returns_201_and_user_data(client):
    response = await client.post(
        "/users/",
        json={
            "firstname": "name",
            "lastname": "lastname",
            "email": "test@email.com",
            "password": "password",
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert "id" in response_data
    assert response_data["id"] is not None

    assert "password" not in response_data

    assert response_data["firstname"] == "name"
    assert response_data["lastname"] == "lastname"
    assert response_data["email"] == "test@email.com"


async def test_create_user_with_duplicate_email_returns_error(
    client,
    sample_user,
):
    response = await client.post(
        "/users/",
        json={
            "firstname": "name",
            "lastname": "lastname",
            "email": sample_user.email,
            "password": "password",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


async def test_get_current_user_returns_authenticated_user_data(
    auth_headers,
    client,
):
    response = await client.get(
        "/users/me",
        headers=auth_headers,
    )

    assert response.status_code == 200
    response_data = response.json()

    assert "id" in response_data
    assert response_data["id"] is not None
    assert "password" not in response_data
    assert response_data["firstname"] == "name"
    assert response_data["lastname"] == "lastname"
    assert response_data["email"] == "test@test.com"


async def test_get_current_user_without_auth_returns_401(client):
    response = await client.get("/users/me")

    assert response.status_code == 401


async def test_update_user_replaces_fields_and_returns_updated_user(
    auth_headers,
    client,
):
    new_data = {
        "firstname": "new name",
        "lastname": "new lastname",
        "email": "new@test.com",
    }

    response = await client.put(
        "/users/",
        json=new_data,
        headers=auth_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert "id" in response_data
    assert response_data["id"] is not None
    assert "password" not in response_data
    assert response_data["firstname"] == new_data["firstname"]
    assert response_data["lastname"] == new_data["lastname"]
    assert response_data["email"] == new_data["email"]


async def test_patch_user_updates_only_specified_fields(
    auth_headers,
    client,
):
    new_data = {
        "firstname": "new name",
        "lastname": "new lastname",
    }

    response = await client.patch(
        "/users/",
        json=new_data,
        headers=auth_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert "id" in response_data
    assert response_data["id"] is not None
    assert "password" not in response_data
    assert response_data["firstname"] == "new name"
    assert response_data["lastname"] == "new lastname"
    assert response_data["email"] == "test@test.com"


async def test_delete_user_removes_user_and_subsequent_requests_return_401_or_404(
    auth_headers,
    client,
    sample_user,
    session,
):
    user_id = sample_user.id

    response = await client.delete("/users/", headers=auth_headers)
    assert response.status_code == 204

    session.expire_all()

    result = await session.get(User, user_id)
    assert result is None

    response = await client.get("/users/me", headers=auth_headers)
    assert response.status_code in (401, 404)

    response = await client.delete("/users/", headers=auth_headers)
    assert response.status_code in (401, 404)

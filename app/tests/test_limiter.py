from unittest.mock import MagicMock
from app.limiter import get_user_key
from app.security import create_access_token


def test_request_with_invalid_token_fallsback_to_address():
    request = MagicMock()
    request.headers = {"Authorization": "Bearer <sometoken>"}
    request.client.host = "127.0.0.1"

    assert get_user_key(request) == request.client.host


def test_request_without_authorization_header_fallsback_to_address():
    request = MagicMock()
    request.headers = {}
    request.client.host = "127.0.0.1"

    assert get_user_key(request) == request.client.host


def test_request_with_valid_token_returns_username():
    data = {"username": "test@email.com", "password": "password"}
    token = create_access_token(data={"sub": data["username"]})
    request = MagicMock()
    request.headers = {"Authorization": f"Bearer {token}"}
    request.client.host = "127.0.0.1"

    assert get_user_key(request) == data["username"]

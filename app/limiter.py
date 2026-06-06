from fastapi import Request

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.settings import settings
from app.security import decode_access_token

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)


def get_user_key(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return get_remote_address(request)
    try:
        token = auth_header.replace("Bearer ", "")
        return decode_access_token(token).username
    except Exception:
        return get_remote_address(request)

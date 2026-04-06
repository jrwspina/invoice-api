from fastapi import Depends, HTTPException

from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated


from app.crud import get_user_by_email
from app.database import get_db
from app.models import User
from app.security import decode_access_token, oauth2_scheme


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_data = decode_access_token(token)
    except (InvalidTokenError, ValueError):
        raise credentials_exception
    user = await get_user_by_email(user_email=token_data.username, session=session)
    if user is None:
        raise credentials_exception
    return user

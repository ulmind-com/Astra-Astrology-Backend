"""Reusable FastAPI dependencies."""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False, description="JWT access token")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Missing bearer token.", error_code="missing_token")

    payload = decode_token(credentials.credentials, expected_type="access")
    subject = payload.get("sub")
    if not subject or not PydanticObjectId.is_valid(subject):
        raise UnauthorizedError("Malformed token subject.", error_code="invalid_token")

    user = await User.get(PydanticObjectId(subject))
    if user is None:
        raise UnauthorizedError("This account no longer exists.", error_code="user_not_found")
    if not user.is_active:
        raise ForbiddenError(
            f"This account is {user.status.value}.", error_code="account_not_active"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


class ClientContext:
    """Client IP and user agent, recorded against OTPs and sign-ups."""

    def __init__(self, request: Request) -> None:
        forwarded = request.headers.get("x-forwarded-for")
        self.ip = (
            forwarded.split(",")[0].strip()
            if forwarded
            else (request.client.host if request.client else None)
        )
        self.user_agent = request.headers.get("user-agent")


Client = Annotated[ClientContext, Depends(ClientContext)]

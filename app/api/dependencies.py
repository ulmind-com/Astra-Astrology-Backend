"""Reusable FastAPI dependencies."""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import decode_token
from app.models.astrologer import Astrologer
from app.models.enums import UserRole
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


def require_roles(*roles: UserRole):
    """Builds a dependency that only lets the given roles through."""

    async def guard(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise ForbiddenError(
                "This action requires one of these roles: "
                + ", ".join(role.value for role in roles),
                error_code="insufficient_role",
            )
        return user

    return guard


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))]
SuperAdminUser = Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN))]
AstrologerUser = Annotated[User, Depends(require_roles(UserRole.ASTROLOGER))]


async def get_current_astrologer(user: AstrologerUser) -> Astrologer:
    """The astrologer profile belonging to the signed-in astrologer."""
    profile = await Astrologer.find_one(Astrologer.user_id == user.id)
    if profile is None:
        # Should not happen: the profile is created with the account.
        raise NotFoundError(
            "Your astrologer profile is missing. Please contact support.",
            error_code="astrologer_profile_missing",
        )
    return profile


CurrentAstrologer = Annotated[Astrologer, Depends(get_current_astrologer)]


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

"""Shared auth primitives, and password sign-in.

Token issuing and the account-status guard live here because both registration
and login need them.
"""

from datetime import UTC, datetime

from loguru import logger

from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.enums import AccountStatus, AuthProvider
from app.models.pending_registration import PendingRegistration
from app.models.user import User
from app.schemas.auth import AuthResult, TokenPair, UserPublic


def issue_tokens(user: User) -> TokenPair:
    claims = {"role": user.role.value, "email": user.email}
    access_token, access_expires = create_access_token(str(user.id), claims)
    refresh_token, refresh_expires = create_refresh_token(str(user.id), claims)
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=access_expires,
        refresh_expires_at=refresh_expires,
    )


def build_auth_result(user: User, *, is_new_user: bool) -> AuthResult:
    return AuthResult(
        user=UserPublic.model_validate(user), tokens=issue_tokens(user), is_new_user=is_new_user
    )


def guard_account_status(user: User) -> None:
    if user.status is AccountStatus.SUSPENDED:
        raise ForbiddenError("This account has been suspended.", error_code="account_suspended")
    if user.status is AccountStatus.DELETED:
        raise ForbiddenError("This account has been deleted.", error_code="account_deleted")
    if not user.is_active:
        raise ForbiddenError(
            f"This account is {user.status.value}.", error_code="account_not_active"
        )


async def login_with_password(email: str, password: str) -> AuthResult:
    """Signs in an existing account with its email and password."""
    email = email.lower().strip()
    user = await User.find_one(User.email == email)

    # ------------------------------------------------- no account yet
    if user is None:
        # Distinguish "you started signing up but never finished" from
        # "you have no account at all" — they need different next steps.
        pending = await PendingRegistration.find_one(PendingRegistration.email == email)
        if pending is not None and not pending.is_expired:
            raise NotFoundError(
                "You haven't finished signing up. Enter the code we emailed you, or start again.",
                error_code="registration_incomplete",
            )
        raise NotFoundError(
            "No account found for this email. Please register first.",
            error_code="user_not_found",
        )

    # ----------------------------------------- account has no password
    if not user.has_password:
        providers = ", ".join(p.value for p in user.auth_providers) or "another method"
        raise UnauthorizedError(
            f"This account signs in with {providers}. Use that instead, or set a password first.",
            error_code="password_not_set",
            details={"providers": [p.value for p in user.auth_providers]},
        )

    # ------------------------------------------------- wrong password
    if not verify_password(password, user.hashed_password or ""):
        raise UnauthorizedError("Incorrect password.", error_code="invalid_password")

    guard_account_status(user)

    user.add_provider(AuthProvider.PASSWORD)
    user.last_login_at = datetime.now(UTC)
    await user.save()

    logger.info("User signed in with password: {}", email)
    return build_auth_result(user, is_new_user=False)

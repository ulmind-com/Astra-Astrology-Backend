"""Shared auth primitives, and password sign-in.

Token issuing and the account-status guard live here because both registration
and login need them.
"""

from datetime import UTC, datetime

from loguru import logger

from app.core.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.enums import AccountStatus, AuthProvider, OtpPurpose
from app.models.otp import OtpCode
from app.models.pending_registration import PendingRegistration
from app.models.user import User
from app.schemas.auth import AuthResult, TokenPair, UserPublic
from app.services import firebase
from app.services import otp as otp_service


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


# ----------------------------------------------------------- password reset
async def request_password_reset(
    email: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[OtpCode, str]:
    """Checks the email belongs to an account, then emails a reset code.

    Returns the OTP record plus the plaintext code; only expose the code when
    `OTP_DEV_MODE` is on.
    """
    email = email.lower().strip()
    user = await User.find_one(User.email == email)

    if user is None:
        raise NotFoundError(
            "No account found for this email.",
            error_code="user_not_found",
        )

    guard_account_status(user)

    return await otp_service.create_and_send_otp(
        identifier=email,
        purpose=OtpPurpose.PASSWORD_RESET,
        name=user.first_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def reset_password(email: str, code: str, new_password: str) -> User:
    """Verifies the code, then sets the new password in MongoDB and Firebase.

    MongoDB is written first on purpose. Sign-in checks the bcrypt hash there,
    so if the Firebase mirror fails the user can still get in; the other order
    would lock them out of both passwords. A failed mirror is logged loudly and
    corrects itself on the next successful reset.
    """
    email = email.lower().strip()
    user = await User.find_one(User.email == email)

    if user is None:
        raise NotFoundError(
            "No account found for this email.",
            error_code="user_not_found",
        )

    guard_account_status(user)

    # Verifying consumes the code, so it cannot be replayed.
    await otp_service.verify_otp(email, code, OtpPurpose.PASSWORD_RESET)

    # --- MongoDB: the source of truth for sign-in ---------------------------
    user.hashed_password = hash_password(new_password)
    user.add_provider(AuthProvider.PASSWORD)
    user.is_email_verified = True  # the code proved they own the address
    await user.save()

    # --- Firebase: the mirror ----------------------------------------------
    try:
        firebase_uid = user.firebase_uid
        if firebase_uid is None:
            twin = await firebase.get_user_by_email(email)
            if twin is not None:
                firebase_uid = twin.uid
                user.firebase_uid = firebase_uid
                await user.save()

        if firebase_uid is not None:
            await firebase.update_user(firebase_uid, password=new_password, email_verified=True)
        else:
            logger.warning(
                "No Firebase user for {} — the password was reset in MongoDB only.", email
            )
    except Exception as exc:  # noqa: BLE001 - MongoDB is already updated
        logger.opt(exception=exc).error(
            "Password reset for {} did not reach Firebase. Sign-in still works, but "
            "the Firebase mirror now holds the old password.",
            email,
        )

    logger.success("Password reset completed for {}", email)
    return user


async def change_password(user: User, current_password: str | None, new_password: str) -> User:
    """Changes the password of the signed-in user, in MongoDB and in Firebase.

    An account that has no password yet (Google-only, or one that was reset) can
    set one without proving an old password it never had.
    """
    if user.has_password:
        if not current_password:
            raise BadRequestError(
                "Your current password is required.",
                error_code="current_password_required",
            )
        if not verify_password(current_password, user.hashed_password or ""):
            raise UnauthorizedError("Current password is incorrect.", error_code="invalid_password")
        if verify_password(new_password, user.hashed_password or ""):
            raise BadRequestError(
                "The new password must be different from the current one.",
                error_code="password_unchanged",
            )

    # MongoDB first: sign-in reads the hash from here, so if the Firebase mirror
    # fails the user can still get in.
    user.hashed_password = hash_password(new_password)
    user.add_provider(AuthProvider.PASSWORD)
    user.must_change_password = False
    await user.save()

    try:
        if user.firebase_uid and firebase.is_enabled():
            await firebase.update_user(user.firebase_uid, password=new_password)
    except Exception as exc:  # noqa: BLE001 - MongoDB is already updated
        logger.opt(exception=exc).error(
            "Password change for {} did not reach Firebase. Sign-in still works, but "
            "the Firebase mirror now holds the old password.",
            user.email,
        )

    logger.success("Password changed for {}", user.email)
    return user

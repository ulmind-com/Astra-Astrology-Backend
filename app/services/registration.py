"""Registration: keeping MongoDB and Firebase Auth in step.

The rule the whole module is built around: **an account exists in both stores or
in neither.** Firebase is written first, MongoDB second, and if the MongoDB
insert fails the Firebase user we just created is deleted again.

Three shapes of "already exists" are handled differently:

* in MongoDB            -> the account is real; tell them to sign in.
* in Firebase only      -> a previous attempt died halfway. The OTP proves the
                           person owns the email, so adopt that Firebase user
                           instead of refusing them forever.
* in neither            -> a fresh sign-up.
"""

from datetime import UTC, datetime

from loguru import logger
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import BadRequestError, ConflictError
from app.core.security import hash_password
from app.models.enums import AuthProvider, OtpPurpose
from app.models.otp import OtpCode
from app.models.pending_registration import PendingRegistration
from app.models.user import User
from app.schemas.auth import AuthResult
from app.services import firebase
from app.services import otp as otp_service
from app.services.auth import build_auth_result, guard_account_status
from app.services.email import send_welcome_email


# --------------------------------------------------------------------- utils
def split_display_name(display_name: str | None) -> tuple[str, str | None, str | None]:
    """ "Ravi Shankar Sharma" -> ("Ravi", "Shankar", "Sharma")."""
    parts = (display_name or "").split()
    if not parts:
        return "User", None, None
    if len(parts) == 1:
        return parts[0], None, None
    if len(parts) == 2:
        return parts[0], None, parts[1]
    return parts[0], " ".join(parts[1:-1]), parts[-1]


async def _send_welcome(email: str, name: str) -> None:
    """A welcome email must never fail the registration that triggered it."""
    try:
        await send_welcome_email(to=email, name=name)
    except Exception as exc:  # noqa: BLE001 - the account is already created
        logger.warning("Welcome email failed for {}: {}", email, exc)


# ----------------------------------------------------------- existence check
async def find_existing(email: str) -> tuple[User | None, firebase.FirebaseUser | None]:
    """Looks the email up in MongoDB and in Firebase."""
    email = email.lower().strip()
    mongo_user = await User.find_one(User.email == email)
    firebase_user = await firebase.get_user_by_email(email)
    return mongo_user, firebase_user


async def check_email_available(email: str) -> tuple[bool, list[str]]:
    mongo_user, firebase_user = await find_existing(email)
    found_in = []
    if mongo_user is not None:
        found_in.append("mongodb")
    if firebase_user is not None:
        found_in.append("firebase")
    # Firebase-only is a broken half-registration, not a taken email.
    return mongo_user is None, found_in


# ------------------------------------------------ manual sign-up, step 1 / 2
async def start_email_registration(
    *,
    email: str,
    password: str,
    first_name: str,
    middle_name: str | None,
    last_name: str | None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[OtpCode, str]:
    """Checks both stores, parks the details and emails an OTP."""
    email = email.lower().strip()

    # Fail fast if Firebase is down, rather than emailing a code for a
    # registration that cannot complete.
    firebase.require_enabled()

    mongo_user, firebase_user = await find_existing(email)
    if mongo_user is not None:
        raise ConflictError(
            "An account with this email already exists. Please sign in instead.",
            error_code="email_already_registered",
            details={"providers": [p.value for p in mongo_user.auth_providers]},
        )
    if firebase_user is not None:
        logger.warning(
            "{} exists in Firebase but not MongoDB — a previous sign-up did not finish. "
            "It will be adopted once the OTP is verified.",
            email,
        )

    pending = PendingRegistration.build(
        email=email,
        password=password,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    # Replace any earlier half-finished attempt for this email.
    await PendingRegistration.find(PendingRegistration.email == email).delete()
    await pending.insert()

    return await otp_service.create_and_send_otp(
        identifier=email,
        purpose=OtpPurpose.SIGNUP,
        name=first_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def resend_email_registration_otp(
    email: str, *, ip_address: str | None = None, user_agent: str | None = None
) -> tuple[OtpCode, str]:
    """Re-sends the sign-up OTP for a registration already in progress."""
    email = email.lower().strip()

    pending = await PendingRegistration.find_one(PendingRegistration.email == email)
    if pending is None or pending.is_expired:
        raise BadRequestError(
            "This sign-up has expired. Please start again.",
            error_code="pending_registration_not_found",
        )

    return await otp_service.create_and_send_otp(
        identifier=email,
        purpose=OtpPurpose.SIGNUP,
        name=pending.first_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def complete_email_registration(email: str, code: str) -> AuthResult:
    """Verifies the OTP, then creates the account in Firebase **and** MongoDB."""
    email = email.lower().strip()

    pending = await PendingRegistration.find_one(PendingRegistration.email == email)
    if pending is None or pending.is_expired:
        raise BadRequestError(
            "This sign-up has expired. Please start again.",
            error_code="pending_registration_not_found",
        )

    # Verify before touching either store; this also consumes the code.
    await otp_service.verify_otp(email, code, OtpPurpose.SIGNUP)

    # Someone could have completed the same sign-up in another tab.
    if await User.find_one(User.email == email) is not None:
        await pending.delete()
        raise ConflictError(
            "An account with this email already exists. Please sign in instead.",
            error_code="email_already_registered",
        )

    # Raises when FIREBASE_REQUIRED is on and Firebase is unavailable; otherwise
    # only warns, and the account is created in MongoDB alone.
    firebase.require_enabled()

    password = pending.password
    full_name = pending.full_name

    firebase_uid: str | None = None
    created_in_firebase = False

    try:
        # --- Firebase first -------------------------------------------------
        if firebase.is_enabled():
            existing = await firebase.get_user_by_email(email)
            if existing is not None:
                # Adopt the orphan: the OTP just proved the person owns this email.
                await firebase.update_user(
                    existing.uid,
                    password=password,
                    display_name=full_name,
                    email_verified=True,
                )
                firebase_uid = existing.uid
                logger.info("Adopted orphaned Firebase user {} for {}", existing.uid, email)
            else:
                record = await firebase.create_user(
                    email=email,
                    password=password,
                    display_name=full_name,
                    email_verified=True,
                )
                firebase_uid = record.uid
                created_in_firebase = True

        # --- MongoDB second -------------------------------------------------
        user = User(
            email=email,
            first_name=pending.first_name,
            middle_name=pending.middle_name,
            last_name=pending.last_name,
            hashed_password=hash_password(password),
            firebase_uid=firebase_uid,
            auth_providers=[AuthProvider.PASSWORD],
            is_email_verified=True,
            last_login_at=datetime.now(UTC),
        )
        await user.insert()

    except DuplicateKeyError:
        if created_in_firebase and firebase_uid:
            await firebase.delete_user(firebase_uid)
        raise ConflictError(
            "An account with this email already exists. Please sign in instead.",
            error_code="email_already_registered",
        )
    except Exception:
        # Roll back so we never leave a Firebase user without a MongoDB twin.
        if created_in_firebase and firebase_uid:
            await firebase.delete_user(firebase_uid)
        raise

    await pending.delete()
    logger.success("User registered (email+password): {} -> {}", email, user.id)

    await _send_welcome(email, user.first_name)
    return build_auth_result(user, is_new_user=True)


# ------------------------------------------------------------- google sign-in
async def authenticate_with_google(id_token: str) -> AuthResult:
    """Verifies the Firebase ID token, then signs the user in or registers them."""
    claims = await firebase.verify_id_token(id_token)

    uid: str | None = claims.get("uid") or claims.get("sub")
    email: str | None = (claims.get("email") or "").lower().strip() or None
    if not uid or not email:
        raise BadRequestError(
            "This Google account did not share an email address, so it cannot be used to sign in.",
            error_code="google_email_missing",
        )

    display_name: str | None = claims.get("name")
    picture: str | None = claims.get("picture")
    email_verified = bool(claims.get("email_verified", True))

    # Match on the Firebase uid first, then fall back to the email.
    user = await User.find_one(User.firebase_uid == uid)
    if user is None:
        user = await User.find_one(User.email == email)

    # ------------------------------------------------------- existing account
    if user is not None:
        guard_account_status(user)

        changed = False
        if user.firebase_uid != uid:
            # Links a manually-registered account to its Google identity.
            logger.info("Linking Firebase uid {} to existing user {}", uid, user.email)
            user.firebase_uid = uid
            changed = True
        if AuthProvider.GOOGLE not in user.auth_providers:
            user.add_provider(AuthProvider.GOOGLE)
            changed = True
        if email_verified and not user.is_email_verified:
            user.is_email_verified = True
            changed = True
        if picture and not user.avatar_url:
            user.avatar_url = picture
            changed = True

        user.last_login_at = datetime.now(UTC)
        await user.save()
        if changed:
            logger.info("Google sign-in updated existing user {}", user.email)

        return build_auth_result(user, is_new_user=False)

    # ------------------------------------------------------------ new account
    # The Firebase user already exists (the client created it during sign-in),
    # so there is nothing to create there and nothing to roll back.
    first_name, middle_name, last_name = split_display_name(display_name)
    user = User(
        email=email,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        hashed_password=None,
        firebase_uid=uid,
        auth_providers=[AuthProvider.GOOGLE],
        is_email_verified=email_verified,
        avatar_url=picture,
        last_login_at=datetime.now(UTC),
    )
    try:
        await user.insert()
    except DuplicateKeyError:
        # Two sign-ins raced; whichever landed first wins.
        existing = await User.find_one(User.email == email)
        if existing is None:
            raise
        guard_account_status(existing)
        return build_auth_result(existing, is_new_user=False)

    # Drop any half-finished manual sign-up for the same email.
    await PendingRegistration.find(PendingRegistration.email == email).delete()

    logger.success("User registered (google): {} -> {}", email, user.id)
    await _send_welcome(email, user.first_name)
    return build_auth_result(user, is_new_user=True)

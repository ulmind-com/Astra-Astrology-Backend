"""WebAuthn / Passkey service for passwordless biometric authentication."""

from datetime import UTC, datetime
import json
import urllib.parse
from typing import Any, Optional

from beanie import PydanticObjectId
from loguru import logger
import webauthn
from webauthn.helpers import (
    base64url_to_bytes,
    bytes_to_base64url,
    generate_challenge,
    options_to_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    AuthenticatorAttachment,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.core.exceptions import (
    BadRequestError,
    NotFoundError,
    UnauthorizedError,
)
from app.models.passkey import PasskeyChallenge, PasskeyCredential
from app.models.user import User
from app.schemas.auth import AuthResult
from app.services import auth as auth_service

RP_NAME = "Astra Astrology"


def resolve_rp_info(request_origin: Optional[str], request_host: Optional[str]) -> tuple[str, str]:
    """Resolves (expected_origin, rp_id) dynamically from request context.

    Ensures passkeys work on localhost:3000, localhost:3001, vercel deployments, and production domains.
    """
    if request_origin:
        clean_origin = request_origin.rstrip("/")
        parsed = urllib.parse.urlparse(clean_origin)
        hostname = parsed.hostname or "localhost"
        return clean_origin, hostname

    if request_host:
        host_no_port = request_host.split(":")[0]
        scheme = "https" if not ("localhost" in host_no_port or "127.0.0.1" in host_no_port) else "http"
        return f"{scheme}://{request_host}", host_no_port

    return "http://localhost:3000", "localhost"


async def generate_registration_options_for_user(
    user: User,
    rp_id: str,
) -> dict[str, Any]:
    """Generates options for registering a new biometric passkey for an authenticated user."""
    challenge_bytes = generate_challenge()
    challenge_str = bytes_to_base64url(challenge_bytes)

    # Fetch existing passkeys to exclude re-registering the same authenticator
    existing_creds = await PasskeyCredential.find(PasskeyCredential.user_id == user.id).to_list()
    exclude_list = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id))
        for c in existing_creds
    ]

    user_name = user.email
    display_name = f"{user.first_name} {user.last_name or ''}".strip() or user.email

    options = webauthn.generate_registration_options(
        rp_id=rp_id,
        rp_name=RP_NAME,
        user_id=str(user.id).encode("utf-8"),
        user_name=user_name,
        user_display_name=display_name,
        challenge=challenge_bytes,
        exclude_credentials=exclude_list,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )

    # Save challenge with TTL
    await PasskeyChallenge(
        challenge=challenge_str,
        user_id=user.id,
        ceremony="registration",
        rp_id=rp_id,
    ).insert()

    return json.loads(options_to_json(options))


async def verify_and_save_registration(
    user: User,
    credential: dict[str, Any],
    device_name: Optional[str],
    origin: str,
    rp_id: str,
) -> PasskeyCredential:
    """Verifies client attestation response and stores the registered public key."""
    # Extract challenge from clientDataJSON
    response_data = credential.get("response", {})
    client_data_raw = response_data.get("clientDataJSON", "")

    try:
        client_data_bytes = base64url_to_bytes(client_data_raw)
        client_data_json = json.loads(client_data_bytes.decode("utf-8"))
        challenge_str = client_data_json.get("challenge", "")
    except Exception as exc:
        raise BadRequestError("Malformed clientDataJSON in passkey credential") from exc

    challenge_doc = await PasskeyChallenge.find_one(
        PasskeyChallenge.challenge == challenge_str,
        PasskeyChallenge.user_id == user.id,
        PasskeyChallenge.ceremony == "registration",
    )
    if not challenge_doc:
        raise BadRequestError("Passkey registration challenge expired or invalid. Please try again.")

    await challenge_doc.delete()

    try:
        verification = webauthn.verify_registration_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(challenge_str),
            expected_origin=origin,
            expected_rp_id=rp_id,
            require_user_verification=False,
        )
    except Exception as exc:
        logger.warning("Passkey registration verification failed: {}", exc)
        raise BadRequestError(f"Biometric verification failed: {exc}") from exc

    cred_id_str = bytes_to_base64url(verification.credential_id)
    pub_key_str = bytes_to_base64url(verification.credential_public_key)

    # Check if this credential already exists
    existing = await PasskeyCredential.find_one(PasskeyCredential.credential_id == cred_id_str)
    if existing:
        existing.public_key = pub_key_str
        existing.sign_count = verification.sign_count
        existing.device_name = device_name or existing.device_name
        await existing.save()
        return existing

    new_cred = PasskeyCredential(
        user_id=user.id,
        credential_id=cred_id_str,
        public_key=pub_key_str,
        sign_count=verification.sign_count,
        device_name=device_name or "Biometric Device / Touch ID",
        transports=credential.get("response", {}).get("transports", []),
    )
    await new_cred.insert()
    logger.success("User {} successfully registered passkey: {}", user.email, new_cred.device_name)
    return new_cred


async def generate_authentication_options_for_login(
    email: Optional[str],
    rp_id: str,
) -> dict[str, Any]:
    """Generates options for biometric sign-in."""
    challenge_bytes = generate_challenge()
    challenge_str = bytes_to_base64url(challenge_bytes)

    allow_list: list[PublicKeyCredentialDescriptor] = []
    user_id: Optional[PydanticObjectId] = None

    if email:
        user = await User.find_one(User.email == email.strip().lower())
        if user:
            user_id = user.id
            user_creds = await PasskeyCredential.find(PasskeyCredential.user_id == user.id).to_list()
            allow_list = [
                PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id))
                for c in user_creds
            ]

    options = webauthn.generate_authentication_options(
        rp_id=rp_id,
        challenge=challenge_bytes,
        allow_credentials=allow_list if allow_list else None,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    await PasskeyChallenge(
        challenge=challenge_str,
        user_id=user_id,
        ceremony="authentication",
        rp_id=rp_id,
    ).insert()

    return json.loads(options_to_json(options))


async def verify_authentication_and_login(
    credential: dict[str, Any],
    origin: str,
    rp_id: str,
) -> AuthResult:
    """Verifies assertion signature from device sensor and issues standard JWT login token."""
    cred_id_raw = credential.get("id") or credential.get("rawId")
    if not cred_id_raw:
        raise BadRequestError("Missing credential ID in passkey assertion")

    passkey = await PasskeyCredential.find_one(PasskeyCredential.credential_id == cred_id_raw)
    if not passkey:
        raise UnauthorizedError("Unrecognized passkey. Please sign in with password and add your device.")

    user = await User.get(passkey.user_id)
    if not user:
        raise UnauthorizedError("User associated with this passkey no longer exists.")

    auth_service.guard_account_status(user)

    # Extract challenge from clientDataJSON
    response_data = credential.get("response", {})
    client_data_raw = response_data.get("clientDataJSON", "")

    try:
        client_data_bytes = base64url_to_bytes(client_data_raw)
        client_data_json = json.loads(client_data_bytes.decode("utf-8"))
        challenge_str = client_data_json.get("challenge", "")
    except Exception as exc:
        raise BadRequestError("Malformed clientDataJSON in passkey assertion") from exc

    challenge_doc = await PasskeyChallenge.find_one(
        PasskeyChallenge.challenge == challenge_str,
        PasskeyChallenge.ceremony == "authentication",
    )
    if not challenge_doc:
        raise BadRequestError("Passkey login session expired. Please click sign in again.")

    await challenge_doc.delete()

    try:
        verification = webauthn.verify_authentication_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(challenge_str),
            expected_origin=origin,
            expected_rp_id=rp_id,
            credential_public_key=base64url_to_bytes(passkey.public_key),
            credential_current_sign_count=passkey.sign_count,
            require_user_verification=False,
        )
    except Exception as exc:
        logger.warning("Passkey authentication failed for {}: {}", user.email, exc)
        raise UnauthorizedError(f"Biometric authentication failed: {exc}") from exc

    # Update sign count and last used
    passkey.sign_count = verification.new_sign_count
    passkey.last_used_at = datetime.now(UTC)
    await passkey.save()

    user.last_login_at = datetime.now(UTC)
    await user.save()

    logger.success("User {} logged in with Passkey biometric: {}", user.email, passkey.device_name)
    return auth_service.build_auth_result(user, is_new_user=False)


async def list_user_passkeys(user_id: PydanticObjectId) -> list[PasskeyCredential]:
    return await PasskeyCredential.find(PasskeyCredential.user_id == user_id).sort(-PasskeyCredential.created_at).to_list()


async def delete_user_passkey(user_id: PydanticObjectId, passkey_id: PydanticObjectId) -> bool:
    cred = await PasskeyCredential.find_one(PasskeyCredential.id == passkey_id, PasskeyCredential.user_id == user_id)
    if not cred:
        raise NotFoundError("Passkey not found.")
    await cred.delete()
    return True

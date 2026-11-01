"""WebAuthn / Passkey biometric login API routes."""

from typing import Any
from beanie import PydanticObjectId
from fastapi import APIRouter, Request

from app.api.dependencies import CurrentUser
from app.schemas.auth import AuthResult
from app.schemas.common import ApiResponse
from app.schemas.passkey import (
    PasskeyAuthenticationOptionsIn,
    PasskeyAuthenticationVerifyIn,
    PasskeyInfoOut,
    PasskeyRegistrationVerifyIn,
)
from app.services import passkey as passkey_service

router = APIRouter(prefix="/auth/passkey", tags=["passkeys"])


# ─────────────────────────────────────────────────────────── REGISTRATION (AUTHENTICATED)

@router.post(
    "/register/options",
    response_model=ApiResponse[dict[str, Any]],
    summary="Generate options to register a new biometric passkey",
)
async def passkey_register_options(
    request: Request,
    user: CurrentUser,
) -> ApiResponse[dict[str, Any]]:
    """Generates WebAuthn PublicKeyCredentialCreationOptions for the current authenticated user."""
    origin, rp_id = passkey_service.resolve_rp_info(
        request.headers.get("origin"),
        request.headers.get("host"),
    )
    options = await passkey_service.generate_registration_options_for_user(user, rp_id)
    return ApiResponse(
        success=True,
        message="Registration options generated",
        data=options,
    )


@router.post(
    "/register/verify",
    response_model=ApiResponse[PasskeyInfoOut],
    summary="Verify and store new biometric passkey",
)
async def passkey_register_verify(
    request: Request,
    payload: PasskeyRegistrationVerifyIn,
    user: CurrentUser,
) -> ApiResponse[PasskeyInfoOut]:
    """Verifies fingerprint / passkey attestation and saves credential."""
    origin, rp_id = passkey_service.resolve_rp_info(
        request.headers.get("origin"),
        request.headers.get("host"),
    )
    cred = await passkey_service.verify_and_save_registration(
        user=user,
        credential=payload.credential,
        device_name=payload.device_name,
        origin=origin,
        rp_id=rp_id,
    )
    return ApiResponse(
        success=True,
        message="Passkey registered successfully! You can now log in with your fingerprint.",
        data=PasskeyInfoOut(
            id=str(cred.id),
            credential_id=cred.credential_id,
            device_name=cred.device_name,
            transports=cred.transports,
            created_at=cred.created_at,
            last_used_at=cred.last_used_at,
        ),
    )


@router.get(
    "/mine",
    response_model=ApiResponse[list[PasskeyInfoOut]],
    summary="List all registered passkeys for current user",
)
async def list_my_passkeys(user: CurrentUser) -> ApiResponse[list[PasskeyInfoOut]]:
    creds = await passkey_service.list_user_passkeys(user.id)
    return ApiResponse(
        success=True,
        message="Passkeys retrieved",
        data=[
            PasskeyInfoOut(
                id=str(c.id),
                credential_id=c.credential_id,
                device_name=c.device_name,
                transports=c.transports,
                created_at=c.created_at,
                last_used_at=c.last_used_at,
            )
            for c in creds
        ],
    )


@router.delete(
    "/{passkey_id}",
    response_model=ApiResponse[dict[str, bool]],
    summary="Delete a registered passkey",
)
async def delete_passkey(
    passkey_id: PydanticObjectId,
    user: CurrentUser,
) -> ApiResponse[dict[str, bool]]:
    await passkey_service.delete_user_passkey(user.id, passkey_id)
    return ApiResponse(
        success=True,
        message="Passkey deleted successfully.",
        data={"deleted": True},
    )


# ────────────────────────────────────────────────────────── AUTHENTICATION (PUBLIC)

@router.post(
    "/login/options",
    response_model=ApiResponse[dict[str, Any]],
    summary="Generate options for biometric passkey sign-in",
)
async def passkey_login_options(
    request: Request,
    payload: PasskeyAuthenticationOptionsIn = PasskeyAuthenticationOptionsIn(),
) -> ApiResponse[dict[str, Any]]:
    """Generates WebAuthn PublicKeyCredentialRequestOptions for sign in."""
    origin, rp_id = passkey_service.resolve_rp_info(
        request.headers.get("origin"),
        request.headers.get("host"),
    )
    options = await passkey_service.generate_authentication_options_for_login(payload.email, rp_id)
    return ApiResponse(
        success=True,
        message="Authentication options generated",
        data=options,
    )


@router.post(
    "/login/verify",
    response_model=ApiResponse[AuthResult],
    summary="Verify passkey biometric assertion and log in",
)
async def passkey_login_verify(
    request: Request,
    payload: PasskeyAuthenticationVerifyIn,
) -> ApiResponse[AuthResult]:
    """Validates device fingerprint signature and returns standard JWT tokens."""
    origin, rp_id = passkey_service.resolve_rp_info(
        request.headers.get("origin"),
        request.headers.get("host"),
    )
    result = await passkey_service.verify_authentication_and_login(
        credential=payload.credential,
        origin=origin,
        rp_id=rp_id,
    )
    return ApiResponse(
        success=True,
        message="Biometric authentication successful. Welcome!",
        data=result,
    )

"""Registration — manual email+password (OTP verified) and Google sign-in."""

from fastapi import APIRouter, Query, status

from app.api.dependencies import Client, CurrentUser
from app.core.config import settings
from app.schemas.auth import (
    AuthResult,
    EmailAvailability,
    EmailRegisterRequest,
    EmailRegisterVerify,
    GoogleAuthRequest,
    OtpSentResult,
    PasswordLogin,
    ResendOtpRequest,
    UserPublic,
)
from app.schemas.common import ApiResponse
from app.services import auth as auth_service
from app.services import registration

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get(
    "/email/available",
    response_model=ApiResponse[EmailAvailability],
    summary="Check whether an email is free (checks MongoDB and Firebase)",
)
async def email_available(
    email: str = Query(description="Email address to check"),
) -> ApiResponse[EmailAvailability]:
    available, found_in = await registration.check_email_available(email)
    return ApiResponse(
        message="Email is available." if available else "Email is already registered.",
        data=EmailAvailability(email=email.lower(), available=available, exists_in=found_in),
    )


@router.post(
    "/register/email",
    response_model=ApiResponse[OtpSentResult],
    summary="Start sign-up — checks both stores, then emails an OTP",
)
async def register_with_email(
    payload: EmailRegisterRequest, client: Client
) -> ApiResponse[OtpSentResult]:
    otp, code = await registration.start_email_registration(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        ip_address=client.ip,
        user_agent=client.user_agent,
    )

    return ApiResponse(
        message=f"We sent a verification code to {otp.identifier}.",
        data=OtpSentResult(
            email=otp.identifier,
            expires_at=otp.expires_at,
            resend_available_at=otp.resend_available_at,
            dev_code=code if settings.OTP_DEV_MODE else None,
        ),
    )


@router.post(
    "/register/email/resend",
    response_model=ApiResponse[OtpSentResult],
    summary="Re-send the sign-up code",
)
async def resend_registration_otp(
    payload: ResendOtpRequest, client: Client
) -> ApiResponse[OtpSentResult]:
    otp, code = await registration.resend_email_registration_otp(
        payload.email, ip_address=client.ip, user_agent=client.user_agent
    )
    return ApiResponse(
        message=f"We sent a new verification code to {payload.email.lower()}.",
        data=OtpSentResult(
            email=payload.email.lower(),
            expires_at=otp.expires_at,
            resend_available_at=otp.resend_available_at,
            dev_code=code if settings.OTP_DEV_MODE else None,
        ),
    )


@router.post(
    "/register/email/verify",
    response_model=ApiResponse[AuthResult],
    status_code=status.HTTP_201_CREATED,
    summary="Verify the code and create the account in Firebase + MongoDB",
)
async def verify_email_registration(payload: EmailRegisterVerify) -> ApiResponse[AuthResult]:
    result = await registration.complete_email_registration(payload.email, payload.code)
    return ApiResponse(message="Your account is ready. Welcome!", data=result)


@router.post(
    "/login",
    response_model=ApiResponse[AuthResult],
    summary="Sign in with email and password",
)
async def login(payload: PasswordLogin) -> ApiResponse[AuthResult]:
    result = await auth_service.login_with_password(payload.email, payload.password)
    return ApiResponse(message="Signed in.", data=result)


@router.post(
    "/google",
    response_model=ApiResponse[AuthResult],
    summary="Google sign-in — registers on first use, signs in after that",
)
async def google_auth(payload: GoogleAuthRequest) -> ApiResponse[AuthResult]:
    result = await registration.authenticate_with_google(payload.id_token)
    return ApiResponse(
        message="Your account is ready. Welcome!" if result.is_new_user else "Signed in.",
        data=result,
    )


@router.get("/me", response_model=ApiResponse[UserPublic], summary="The signed-in user")
async def me(user: CurrentUser) -> ApiResponse[UserPublic]:
    return ApiResponse(message="Current user.", data=UserPublic.model_validate(user))

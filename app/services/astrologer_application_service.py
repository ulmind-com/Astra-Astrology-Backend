"""Astrologer Self-Application and Verification Service."""

from __future__ import annotations

import secrets
import string
from datetime import UTC, datetime
from typing import Any

from beanie import PydanticObjectId
from bson import ObjectId
from loguru import logger
from slugify import slugify

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password, safe_regex_pattern
from app.models.astrologer import (
    AppointmentCard,
    Astrologer,
    Availability,
    BankDetails,
    RateCard,
)
from app.models.astrologer_application import AstrologerApplication
from app.models.enums import AuthProvider, OtpPurpose, Skill, UserRole
from app.models.user import User
from app.schemas.astrologer_application import (
    AstrologerApplicationCreateIn,
    AstrologerApplicationOut,
)
from app.services import email as email_service, firebase, otp as otp_service


def _generate_temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def _unique_slug(display_name: str) -> str:
    base = slugify(display_name, max_length=120) or "astrologer"
    candidate, suffix = base, 2
    while await Astrologer.find_one(Astrologer.slug == candidate) is not None:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _parse_skills(raw_skills: list[str]) -> list[Skill]:
    """Maps arbitrary incoming skill strings to supported Skill enums."""
    valid_skills: list[Skill] = []
    for s in raw_skills:
        clean = s.strip().lower().replace(" ", "_").replace("-", "_")
        for enum_member in Skill:
            if enum_member.value == clean or enum_member.name.lower() == clean:
                if enum_member not in valid_skills:
                    valid_skills.append(enum_member)
                break
    if not valid_skills:
        valid_skills.append(Skill.VEDIC_ASTROLOGY)
    return valid_skills


async def send_application_otp(email: str) -> None:
    """Sends a verification code to applicant's email before registration submission."""
    email_clean = email.lower().strip()

    # Check if this email is already an active Astrologer
    existing_user = await User.find_one(User.email == email_clean)
    if existing_user and existing_user.role == UserRole.ASTROLOGER:
        raise ConflictError(
            "An active Astrologer account is already registered with this email.",
            error_code="astrologer_already_registered",
        )

    await otp_service.create_and_send_otp(
        identifier=email_clean,
        purpose=OtpPurpose.ASTROLOGER_APPLICATION,
        name="Astrologer Applicant",
    )


async def verify_application_otp(email: str, code: str) -> bool:
    """Verifies the email OTP."""
    await otp_service.verify_otp(
        identifier=email.lower().strip(),
        code=code.strip(),
        purpose=OtpPurpose.ASTROLOGER_APPLICATION,
    )
    return True


async def submit_application(payload: AstrologerApplicationCreateIn) -> AstrologerApplication:
    """Validates the email OTP and registers a new AstrologerApplication in pending state."""
    email_clean = payload.email.lower().strip()

    # 1. Verify OTP code
    await verify_application_otp(email_clean, payload.otp_code)

    # 2. Check if already an active astrologer
    existing_user = await User.find_one(User.email == email_clean)
    if existing_user and existing_user.role == UserRole.ASTROLOGER:
        raise ConflictError(
            "An active Astrologer account is already registered with this email.",
            error_code="astrologer_already_registered",
        )

    # 3. Generate unique application number
    current_year = datetime.now(UTC).year
    count_today = await AstrologerApplication.count()
    app_number = f"DIVIN-ASTRO-{current_year}-{(count_today + 1):04d}"

    # 4. Check if an application is already pending for this email
    existing_app = await AstrologerApplication.find_one({
        "email": email_clean,
        "status": "pending",
    })
    if existing_app:
        existing_app.full_name = payload.full_name.strip()
        existing_app.phone = payload.phone.strip()
        existing_app.gender = payload.gender
        existing_app.age = payload.age
        existing_app.address = payload.address
        existing_app.city = payload.city.strip()
        existing_app.state = payload.state.strip()
        existing_app.pincode = payload.pincode
        existing_app.skills = payload.skills
        existing_app.specialisations = payload.specialisations
        existing_app.experience_years = payload.experience_years
        existing_app.languages = payload.languages or ["Bengali", "English"]
        existing_app.qualifications = payload.qualifications
        existing_app.bio = payload.bio
        existing_app.avatar_url = payload.avatar_url
        existing_app.identity_proof_url = payload.identity_proof_url
        existing_app.bank_account_number = payload.bank_account_number
        existing_app.bank_ifsc = payload.bank_ifsc
        existing_app.bank_account_holder = payload.bank_account_holder
        existing_app.bank_name = payload.bank_name
        existing_app.upi_id = payload.upi_id
        existing_app.pan_card = payload.pan_card
        existing_app.updated_at = datetime.now(UTC)
        await existing_app.save()
        logger.info(
            "Updated existing pending astrologer application {} for {}",
            existing_app.application_number,
            email_clean,
        )
        return existing_app

    # 5. Create new application
    new_app = AstrologerApplication(
        application_number=app_number,
        full_name=payload.full_name.strip(),
        email=email_clean,
        phone=payload.phone.strip(),
        gender=payload.gender,
        age=payload.age,
        address=payload.address,
        city=payload.city.strip(),
        state=payload.state.strip(),
        pincode=payload.pincode,
        skills=payload.skills,
        specialisations=payload.specialisations,
        experience_years=payload.experience_years,
        languages=payload.languages or ["Bengali", "English"],
        qualifications=payload.qualifications,
        bio=payload.bio,
        avatar_url=payload.avatar_url,
        identity_proof_url=payload.identity_proof_url,
        bank_account_number=payload.bank_account_number,
        bank_ifsc=payload.bank_ifsc,
        bank_account_holder=payload.bank_account_holder,
        bank_name=payload.bank_name,
        upi_id=payload.upi_id,
        pan_card=payload.pan_card,
        status="pending",
    )
    await new_app.insert()
    logger.info("Created new Astrologer application: {} for {}", app_number, email_clean)
    return new_app


async def list_applications(
    status: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AstrologerApplication], int]:
    """Lists applications with optional status and text filters."""
    query: dict[str, Any] = {}
    if status and status.lower() != "all":
        query["status"] = status.lower()

    if search and search.strip():
        q_regex = safe_regex_pattern(search)
        query["$or"] = [
            {"full_name": q_regex},
            {"email": q_regex},
            {"phone": q_regex},
            {"city": q_regex},
            {"application_number": q_regex},
        ]

    cap_limit = min(max(1, limit), 100)
    total = await AstrologerApplication.find(query).count()
    items = (
        await AstrologerApplication.find(query)
        .sort("-created_at")
        .skip(max(0, offset))
        .limit(cap_limit)
        .to_list()
    )
    return items, total


async def get_application(app_id: str) -> AstrologerApplication:
    """Finds application by ID."""
    if not ObjectId.is_valid(app_id):
        raise BadRequestError("Invalid application ID.")
    app = await AstrologerApplication.get(PydanticObjectId(app_id))
    if not app:
        raise NotFoundError("Astrologer application not found.")
    return app


async def approve_application(
    app_id: str,
    admin_user: User,
) -> tuple[User, Astrologer, str, bool, str]:
    """Approves a pending application, creates Firebase & Mongo User,

    creates live verified Astrologer profile, sets default rates & appointment settings,
    and sends official credentials email.
    """
    app = await get_application(app_id)
    if app.status == "approved" and app.approved_user_id and app.approved_astrologer_id:
        raise BadRequestError("This application has already been approved.")

    email = app.email.lower().strip()
    display_name = app.full_name
    password = _generate_temp_password()

    # Split name into first and last
    name_parts = display_name.split()
    first_name = name_parts[0] if name_parts else "Astrologer"
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    # 1. Create or link User
    existing_user = await User.find_one(User.email == email)
    if existing_user:
        user = existing_user
        user.role = UserRole.ASTROLOGER
        user.hashed_password = hash_password(password)
        user.must_change_password = True
        await user.save()
    else:
        firebase_uid: str | None = None
        if firebase.is_enabled():
            fb_record = await firebase.get_user_by_email(email)
            if fb_record:
                await firebase.update_user(
                    fb_record.uid,
                    password=password,
                    display_name=display_name,
                    email_verified=True,
                )
                firebase_uid = fb_record.uid
            else:
                new_rec = await firebase.create_user(
                    email=email,
                    password=password,
                    display_name=display_name,
                    email_verified=True,
                )
                firebase_uid = new_rec.uid

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=app.phone,
            hashed_password=hash_password(password),
            firebase_uid=firebase_uid,
            auth_providers=[AuthProvider.PASSWORD],
            role=UserRole.ASTROLOGER,
            is_email_verified=True,
            must_change_password=True,
        )
        await user.insert()

    # 2. Create Astrologer Profile
    parsed_skills = _parse_skills(app.skills)
    primary_skill_title = parsed_skills[0].value.replace("_", " ").title() if parsed_skills else "Vedic Astrology"
    tagline = f"{app.experience_years}+ Years Experience in {primary_skill_title}"

    bank_details = BankDetails(
        account_holder_name=app.bank_account_holder or display_name,
        account_number=app.bank_account_number,
        account_number_last4=(
            app.bank_account_number[-4:]
            if app.bank_account_number and len(app.bank_account_number) >= 4
            else None
        ),
        ifsc=app.bank_ifsc,
        bank_name=app.bank_name,
        upi_id=app.upi_id,
        pan_card=app.pan_card,
    )

    profile = Astrologer(
        user_id=user.id,
        display_name=display_name,
        slug=await _unique_slug(display_name),
        tagline=tagline,
        bio=app.bio,
        profile_image_url=app.avatar_url,
        skills=parsed_skills,
        languages=app.languages or ["Bengali", "English"],
        specialisations=app.specialisations,
        qualifications=app.qualifications,
        experience_years=app.experience_years,
        rates=RateCard(
            chat_coins_per_minute=20,
            call_coins_per_minute=25,
            video_coins_per_minute=30,
        ),
        bank=bank_details,
        appointment=AppointmentCard(
            enabled=True,
            price_paise=50000,  # ₹500
            block_minutes=30,
        ),
        availability=Availability(
            is_online=True,
            is_available_for_chat=True,
            is_available_for_call=True,
            is_available_for_video=True,
        ),
        is_listed=True,
        is_featured=False,
    )
    await profile.insert()

    # 3. Update application status
    app.status = "approved"
    app.reviewed_by = admin_user.id
    app.reviewed_at = datetime.now(UTC)
    app.approved_user_id = user.id
    app.approved_astrologer_id = profile.id
    app.updated_at = datetime.now(UTC)
    await app.save()

    # 4. Send official welcome email with credentials
    dashboard_url = "https://admin.divinlink.com/login"
    email_sent = False
    try:
        email_sent = await email_service.send_astrologer_welcome_email(
            to=email, name=display_name, password=password
        )
    except Exception as exc:
        logger.warning("Could not send welcome email to approved Astrologer {}: {}", email, exc)

    logger.info("Astrologer Application #{} approved successfully for {}", app.application_number, email)
    return user, profile, password, email_sent, dashboard_url


async def reject_application(
    app_id: str,
    reason: str | None,
    admin_user: User,
) -> AstrologerApplication:
    """Marks an application as rejected with an optional explanation."""
    app = await get_application(app_id)
    app.status = "rejected"
    app.rejection_reason = reason.strip() if reason else None
    app.reviewed_by = admin_user.id
    app.reviewed_at = datetime.now(UTC)
    app.updated_at = datetime.now(UTC)
    await app.save()
    logger.info(
        "Astrologer Application #{} rejected by admin {}: {}",
        app.application_number,
        admin_user.email,
        reason,
    )
    return app

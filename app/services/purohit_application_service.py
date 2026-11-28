"""Purohit (Vedic Priest) Self-Application and Verification Service."""

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
from app.models.enums import AuthProvider, OtpPurpose, UserRole
from app.models.purohit import Purohit, PurohitPujaItem
from app.models.purohit_application import PurohitApplication
from app.models.user import User
from app.schemas.purohit_application import (
    PurohitApplicationCreateIn,
    PurohitApplicationOut,
)
from app.services import email as email_service, firebase, otp as otp_service


def _generate_temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def _unique_slug(display_name: str) -> str:
    base = slugify(display_name, max_length=120) or "purohit"
    candidate, suffix = base, 2
    while await Purohit.find_one(Purohit.slug == candidate) is not None:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _build_default_pujas(specializations: list[str]) -> list[PurohitPujaItem]:
    """Pre-populates an initial puja catalog based on the Purohit's claimed specializations."""
    catalog: list[PurohitPujaItem] = []
    specs_lower = [s.lower() for s in specializations]

    if any("রুদ্র" in s or "শিব" in s or "rudra" in s for s in specs_lower):
        catalog.append(
            PurohitPujaItem(
                puja_name="শ্রী রুদ্রাভিষেক ও মহাদেব অভিষেক",
                description="কাশী ও বৈদিক শাস্ত্রমতে রুদ্রাভিষেক, পঞ্চামৃত অভিষেক ও মহাদেব পূজা।",
                duration_minutes=45,
                price_inr=501.0,
                samagri_notes="কাঁচা দুধ, গঙ্গাজল, বেলপাতা, ধুতুরা, মধু, ঘি ও ফল।",
                is_active=True,
            )
        )

    if any("সত্যনারায়ণ" in s or "satyanarayan" in s or "কথা" in s for s in specs_lower):
        catalog.append(
            PurohitPujaItem(
                puja_name="শ্রী সত্যনারায়ণ ব্রতকথা ও পূজা",
                description="পারিবারিক শান্তি ও সমৃদ্ধির জন্য শ্রী সত্যনারায়ণ কথা ও আরতি।",
                duration_minutes=60,
                price_inr=501.0,
                samagri_notes="সিন্নি প্রসাদ (আটা, দুধ, চিনি, কলা), পঞ্চামৃত, ফুল ও তুলসীপাতা।",
                is_active=True,
            )
        )

    if any("বাস্তু" in s or "গৃহপ্রবেশ" in s or "vastu" in s for s in specs_lower):
        catalog.append(
            PurohitPujaItem(
                puja_name="গৃহপ্রবেশ ও বাস্তু শান্তি যজ্ঞ",
                description="নতুন গৃহ বা ফ্ল্যাটের বাস্তুদোষ নিবারণ ও গৃহপ্রবেশ হোম।",
                duration_minutes=90,
                price_inr=1100.0,
                samagri_notes="নবগ্রহ সমিধ, ঘৃত, পঞ্চগব্য ও পূর্ণাহুতি সামগ্রী।",
                is_active=True,
            )
        )

    if any("কালসর্প" in s or "রাহু" in s or "kalsarp" in s or "দোষ" in s for s in specs_lower):
        catalog.append(
            PurohitPujaItem(
                puja_name="কালসর্প ও নবগ্রহ দোষ শান্তি পূজা",
                description="কুষ্ঠির কালসর্প দোষের প্রভাব প্রশমিত করতে বিশেষ শান্তি পূজা ও জপ।",
                duration_minutes=60,
                price_inr=1501.0,
                samagri_notes="তামার নাগ প্রতিমা, তিল, যব, কালো তিল ও দুধ।",
                is_active=True,
            )
        )

    # Always ensure at least 2 foundational pujas
    if len(catalog) < 2:
        catalog.append(
            PurohitPujaItem(
                puja_name="লক্ষ্মী পূজা ও সৌভাগ্য শান্তি",
                description="মা লক্ষ্মীর আশীর্বাদ ও আর্থিক সমৃদ্ধির জন্য বিশেষ বৈদিক পূজা।",
                duration_minutes=40,
                price_inr=301.0,
                samagri_notes="পদ্মফুল, ক্ষীর প্রসাদ, প্রদীপ, ধূপ ও চন্দন।",
                is_active=True,
            )
        )
        catalog.append(
            PurohitPujaItem(
                puja_name="সংকটমোচন হনুমান পূজা ও আরতি",
                description="গ্রহপীড়া ও সংকট দূরীকরণার্থে শ্রী হনুমান চালীসা পাঠ ও বিশেষ মঙ্গল আরতি।",
                duration_minutes=30,
                price_inr=251.0,
                samagri_notes="সিঁদুর, জুঁই তেলের প্রদীপ, লাড্ডু ও তুলসীমালা।",
                is_active=True,
            )
        )

    return catalog


async def send_application_otp(email: str) -> None:
    """Sends a verification code to applicant's email before registration submission."""
    email_clean = email.lower().strip()

    # Check if this email is already a verified Purohit
    existing_purohit = await Purohit.find_one(Purohit.email == email_clean)
    if existing_purohit:
        raise ConflictError(
            "An active Purohit profile is already registered with this email.",
            error_code="purohit_already_registered",
        )

    await otp_service.create_and_send_otp(
        identifier=email_clean,
        purpose=OtpPurpose.PUROHIT_APPLICATION,
        name="Vedic Acharya",
    )


async def verify_application_otp(email: str, code: str) -> bool:
    """Verifies the email OTP."""
    await otp_service.verify_otp(
        identifier=email.lower().strip(),
        code=code.strip(),
        purpose=OtpPurpose.PUROHIT_APPLICATION,
    )
    return True


async def submit_application(payload: PurohitApplicationCreateIn) -> PurohitApplication:
    """Validates the email OTP and registers a new PurohitApplication in pending state."""
    email_clean = payload.email.lower().strip()

    # 1. Verify OTP code
    await verify_application_otp(email_clean, payload.otp_code)

    # 2. Check if already registered
    existing_purohit = await Purohit.find_one(Purohit.email == email_clean)
    if existing_purohit:
        raise ConflictError(
            "An active Purohit profile is already registered with this email.",
            error_code="purohit_already_registered",
        )

    # 3. Generate unique application number
    current_year = datetime.now(UTC).year
    count_today = await PurohitApplication.count()
    app_number = f"DIVIN-PA-{current_year}-{(count_today + 1):04d}"

    # 4. Check if an application is already pending for this email
    existing_app = await PurohitApplication.find_one({
        "email": email_clean,
        "status": "pending",
    })
    if existing_app:
        # Update existing pending application
        existing_app.full_name = payload.full_name.strip()
        existing_app.phone = payload.phone.strip()
        existing_app.age = payload.age
        existing_app.address = payload.address
        existing_app.city = payload.city.strip()
        existing_app.state = payload.state.strip()
        existing_app.pincode = payload.pincode
        existing_app.vedic_shakha = payload.vedic_shakha.strip()
        existing_app.specializations = payload.specializations
        existing_app.experience_years = payload.experience_years
        existing_app.languages = payload.languages
        existing_app.bio = payload.bio
        existing_app.avatar_url = payload.avatar_url
        existing_app.identity_proof_url = payload.identity_proof_url
        existing_app.bank_account_number = payload.bank_account_number
        existing_app.bank_ifsc = payload.bank_ifsc
        existing_app.bank_account_holder = payload.bank_account_holder
        existing_app.upi_id = payload.upi_id
        existing_app.updated_at = datetime.now(UTC)
        await existing_app.save()
        logger.info("Updated existing pending application {} for {}", existing_app.application_number, email_clean)
        return existing_app

    # 5. Create new application
    new_app = PurohitApplication(
        application_number=app_number,
        full_name=payload.full_name.strip(),
        email=email_clean,
        phone=payload.phone.strip(),
        age=payload.age,
        address=payload.address,
        city=payload.city.strip(),
        state=payload.state.strip(),
        pincode=payload.pincode,
        vedic_shakha=payload.vedic_shakha.strip(),
        specializations=payload.specializations,
        experience_years=payload.experience_years,
        languages=payload.languages or ["Bengali", "Sanskrit"],
        bio=payload.bio,
        avatar_url=payload.avatar_url,
        identity_proof_url=payload.identity_proof_url,
        bank_account_number=payload.bank_account_number,
        bank_ifsc=payload.bank_ifsc,
        bank_account_holder=payload.bank_account_holder,
        upi_id=payload.upi_id,
        status="pending",
    )
    await new_app.insert()
    logger.info("Created new Purohit application: {} for {}", app_number, email_clean)
    return new_app


async def list_applications(
    status: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[PurohitApplication], int]:
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
    total = await PurohitApplication.find(query).count()
    items = (
        await PurohitApplication.find(query)
        .sort("-created_at")
        .skip(max(0, offset))
        .limit(cap_limit)
        .to_list()
    )
    return items, total


async def get_application(app_id: str) -> PurohitApplication:
    """Finds application by ID."""
    if not ObjectId.is_valid(app_id):
        raise BadRequestError("Invalid application ID.")
    app = await PurohitApplication.get(PydanticObjectId(app_id))
    if not app:
        raise NotFoundError("Purohit application not found.")
    return app


async def approve_application(
    app_id: str,
    admin_user: User,
) -> tuple[User, Purohit, str, bool, str]:
    """Approves a pending application, creates Firebase & Mongo User,

    creates live verified Purohit profile, pre-populates catalog,
    and sends official credentials email.
    """
    app = await get_application(app_id)
    if app.status == "approved" and app.approved_user_id and app.approved_purohit_id:
        raise BadRequestError("This application has already been approved.")

    email = app.email.lower().strip()
    display_name = app.full_name
    password = _generate_temp_password()

    # Split name into first and last
    name_parts = display_name.split()
    first_name = name_parts[0] if name_parts else "Pandit"
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "Acharya"

    # 1. Create or link User
    existing_user = await User.find_one(User.email == email)
    if existing_user:
        user = existing_user
        user.role = UserRole.PUROHIT
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
            role=UserRole.PUROHIT,
            is_email_verified=True,
            must_change_password=True,
        )
        await user.insert()

    # 2. Create Purohit Profile
    catalog = _build_default_pujas(app.specializations)
    title = f"{app.vedic_shakha} আচার্য" if app.vedic_shakha else "Vedic Acharya"

    profile = Purohit(
        user_id=user.id,
        display_name=display_name,
        slug=await _unique_slug(display_name),
        title=title,
        bio=app.bio,
        avatar_url=app.avatar_url,
        phone=app.phone,
        email=email,
        address=app.address,
        city=app.city,
        state=app.state,
        pincode=app.pincode,
        experience_years=app.experience_years,
        languages=app.languages or ["Bengali", "Sanskrit"],
        is_online=True,
        is_verified=True,
        pujas=catalog,
        rating=5.0,
        total_pujas_performed=0,
    )
    await profile.insert()

    # 3. Update application status
    app.status = "approved"
    app.reviewed_by = admin_user.id
    app.reviewed_at = datetime.now(UTC)
    app.approved_user_id = user.id
    app.approved_purohit_id = profile.id
    app.updated_at = datetime.now(UTC)
    await app.save()

    # 4. Send official welcome email with credentials
    dashboard_url = "https://admin.divinlink.com/purohit-dashboard"
    email_sent = False
    try:
        email_sent = await email_service.send_purohit_welcome_email(
            to=email, name=display_name, password=password
        )
    except Exception as exc:
        logger.warning("Could not send welcome email to approved Purohit {}: {}", email, exc)

    logger.info("Purohit Application #{} approved successfully for {}", app.application_number, email)
    return user, profile, password, email_sent, dashboard_url


async def reject_application(
    app_id: str,
    reason: str | None,
    admin_user: User,
) -> PurohitApplication:
    """Marks an application as rejected with an optional explanation."""
    app = await get_application(app_id)
    app.status = "rejected"
    app.rejection_reason = reason.strip() if reason else None
    app.reviewed_by = admin_user.id
    app.reviewed_at = datetime.now(UTC)
    app.updated_at = datetime.now(UTC)
    await app.save()
    logger.info("Purohit Application #{} rejected by admin {}: {}", app.application_number, admin_user.email, reason)
    return app

"""Tests for Astra Gurukul Course document models, schemas and service layer."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from beanie import PydanticObjectId, init_beanie

from app.models.course import (
    Course,
    CourseEnrollment,
    CourseLesson,
    CourseLessonProgress,
    CourseOrder,
    CourseQuestion,
    CourseQuestionAnswer,
    CourseSection,
)
from app.models.user import User
from app.services.course_service import CourseService


@pytest.fixture(autouse=True)
async def init_mock_beanie():
    """Initializes Beanie DocumentSettings in memory for standalone unit testing."""
    mock_db = MagicMock()
    mock_db.command = AsyncMock(return_value={"version": "6.0.0", "versionArray": [6, 0, 0]})
    mock_db.list_collection_names = AsyncMock(return_value=[])

    mock_coll = MagicMock()
    mock_coll.create_index = AsyncMock()
    mock_coll.create_indexes = AsyncMock()
    mock_coll.index_information = AsyncMock(return_value={})
    mock_coll.insert_one = AsyncMock(
        side_effect=lambda *args, **kwargs: MagicMock(inserted_id=PydanticObjectId())
    )
    mock_coll.find.return_value.to_list = AsyncMock(return_value=[])
    mock_db.__getitem__.return_value = mock_coll

    await init_beanie(
        database=mock_db,
        document_models=[
            Course,
            CourseSection,
            CourseLesson,
            CourseEnrollment,
            CourseLessonProgress,
            CourseOrder,
            CourseQuestion,
            User,
        ],
        skip_indexes=True,
    )


@pytest.mark.asyncio
async def test_course_model_defaults():
    course = Course(
        title="Complete Vedic Astrology & Jyotish Masterclass",
        slug="complete-vedic-astrology-masterclass",
        subtitle="Learn Kundli, Dasha, Yogas and Predictive Astrology",
        description="Comprehensive 60-day curriculum with classical Parashara formulas.",
        thumbnail_url="https://res.cloudinary.com/astra/course-thumb.jpg",
        price=1499.0,
        mrp=4999.0,
        discount_percent=70,
        tags=["jyotish", "kundli", "vedic"],
    )
    assert course.title == "Complete Vedic Astrology & Jyotish Masterclass"
    assert course.price == 1499.0
    assert course.is_published is True
    assert course.certificate_enabled is True
    assert course.is_deleted is False


@pytest.mark.asyncio
async def test_course_service_list_courses():
    courses = await CourseService.list_courses(category="vedic_astrology")
    assert isinstance(courses, list)


def test_course_lesson_create_schema_resilience():
    from app.schemas.course import CourseLessonCreateRequest, CourseLessonUpdateRequest, BunnyCreateVideoRequest

    # Test float duration from video duration metadata calculation (e.g. 30 sec = 0.5005 mins)
    req1 = CourseLessonCreateRequest(
        section_id="672e42845c2f004a441e8c91",
        title="Intro to Rashi Lords",
        order=0,
        duration_minutes=0.5005,
        video_id="",
    )
    assert req1.duration_minutes >= 0
    assert req1.order == 1
    assert req1.video_id == ""

    # Test string duration and negative values
    req2 = CourseLessonCreateRequest(
        section_id="672e42845c2f004a441e8c91",
        title="Navamsha Secrets",
        order="3",
        duration_minutes="45.6",
        video_id="bunny-guid-123",
    )
    assert req2.duration_minutes == 46
    assert req2.order == 3

    # Test Bunny create placeholder default title
    bunny_req = BunnyCreateVideoRequest()
    assert bunny_req.title == "New Video Lesson"


def test_admin_course_endpoint_imports_and_settings():
    from app.api.v1.admin_course import settings, admin_create_lesson
    assert settings.BUNNY_STREAM_LIBRARY_ID == "803267"
    assert callable(admin_create_lesson)


@pytest.mark.asyncio
async def test_create_course_order_user_attribute_resilience():
    from unittest.mock import patch
    from beanie import PydanticObjectId
    from app.models.user import User

    # Create dummy user with phone instead of mobile_number
    mock_user = MagicMock(spec=User)
    mock_user.id = PydanticObjectId()
    mock_user.phone = "+919876543210"
    mock_user.email = "student@example.com"
    mock_user.full_name = "Astra Student"
    # Ensure mobile_number does NOT exist on User (which caused AttributeError before)
    del mock_user.mobile_number

    mock_course = MagicMock(spec=Course)
    mock_course.id = PydanticObjectId()
    mock_course.price = 149.0
    mock_course.slug = "demo-course-1"
    mock_course.title = "Demo Course 1"
    mock_course.is_deleted = False

    with patch.object(Course, "find_one", AsyncMock(return_value=mock_course)):
        with patch.object(CourseEnrollment, "find_one", AsyncMock(return_value=None)):
            with patch("app.services.course_service._razorpay") as mock_rzp:
                mock_order_client = MagicMock()
                mock_order_client.order.create.return_value = {"id": "order_test_123"}
                mock_rzp.return_value = mock_order_client

                res = await CourseService.create_course_order(mock_user, mock_course.id)
                assert res["order_id"] == "order_test_123"
                assert res["amount_paise"] == 14900
                assert res["course_slug"] == "demo-course-1"


def test_course_jigyasa_timestamp_formatting():
    from app.services.course_service import CourseService

    assert CourseService.format_timestamp(0) == "00:00"
    assert CourseService.format_timestamp(45) == "00:45"
    assert CourseService.format_timestamp(185) == "03:05"
    assert CourseService.format_timestamp(3672) == "01:01:12"


def test_course_question_model_structure():
    from beanie import PydanticObjectId
    from app.models.course import CourseQuestion, CourseQuestionAnswer

    q = CourseQuestion(
        course_id=PydanticObjectId(),
        section_id=PydanticObjectId(),
        lesson_id=PydanticObjectId(),
        user_id=PydanticObjectId(),
        user_name="Rahul Student",
        timestamp_seconds=125,
        timestamp_formatted="02:05",
        title="Doubt regarding Jupiter in 7th House",
        content="Is Jupiter considered benefic if conjunct Rahu in Navamsha chart?",
    )
    assert q.title == "Doubt regarding Jupiter in 7th House"
    assert q.timestamp_formatted == "02:05"
    assert q.upvote_count == 0
    assert q.is_resolved is False

    ans = CourseQuestionAnswer(
        user_id=PydanticObjectId(),
        user_name="Pt. Rahul Sharma (Acharya)",
        user_role="admin",
        is_official=True,
        content="Jupiter conjunct Rahu forms Guru Chandal Yoga. Look at the Nakshatra lord for relief.",
    )
    q.answers.append(ans)
    q.answer_count = len(q.answers)
    q.has_official_answer = True
    assert q.answer_count == 1
    assert q.has_official_answer is True


def test_admin_course_route_order():
    """Ensures static routes like /questions precede /{course_id} to prevent path parameter shadowing."""
    from app.api.v1.admin_course import router

    questions_index = None
    preview_token_index = None
    course_id_index = None

    for idx, r in enumerate(router.routes):
        if getattr(r, "path", None) == "/admin/courses/questions" and "GET" in getattr(r, "methods", set()):
            questions_index = idx
        elif getattr(r, "path", None) == "/admin/courses/preview-token/{video_id}" and "GET" in getattr(r, "methods", set()):
            preview_token_index = idx
        elif getattr(r, "path", None) == "/admin/courses/{course_id}" and "GET" in getattr(r, "methods", set()):
            course_id_index = idx

    assert questions_index is not None, "GET /admin/courses/questions route must exist"
    assert preview_token_index is not None, "GET /admin/courses/preview-token/{video_id} route must exist"
    assert course_id_index is not None, "GET /admin/courses/{course_id} route must exist"
    assert questions_index < course_id_index, (
        f"Route shadowing bug! /admin/courses/questions (idx {questions_index}) "
        f"must be registered before /admin/courses/{{course_id}} (idx {course_id_index})"
    )
    assert preview_token_index < course_id_index, (
        f"Route shadowing bug! /admin/courses/preview-token/{{video_id}} (idx {preview_token_index}) "
        f"must be registered before /admin/courses/{{course_id}} (idx {course_id_index})"
    )


def test_course_certificate_generation_and_html():
    from datetime import datetime, timezone
    from beanie import PydanticObjectId
    from app.models.user import User
    from app.schemas.course import CourseCertificateOut

    user_id = PydanticObjectId()
    course_id = PydanticObjectId()

    user = User(
        id=user_id,
        email="samiran@example.com",
        first_name="Samiran",
        last_name="Samanta",
    )
    course = Course(
        id=course_id,
        title="Vedic Astrology Foundation Masterclass",
        slug="vedic-astrology-foundation",
        instructor_name="Acharya Rahul Sharma",
        instructor_title="Vedic Jyotishacharya",
    )
    enrollment = CourseEnrollment(
        user_id=user_id,
        course_id=course_id,
        progress_percent=100.0,
        certificate_issued=True,
        certificate_id="ASTRA-CERT-SAMIRAN-TEST",
        certificate_issued_at=datetime.now(timezone.utc),
        certificate_url="https://astra-astrology-web.vercel.app/verify/certificate/ASTRA-CERT-SAMIRAN-TEST",
    )

    cert_data = CourseService.generate_course_certificate_data(enrollment, course, user)
    # Validate against Pydantic schema
    cert_out = CourseCertificateOut(**cert_data)
    assert cert_out.certificate_id == "ASTRA-CERT-SAMIRAN-TEST"
    assert cert_out.student_name == "Samiran Samanta"
    assert cert_out.course_title == "Vedic Astrology Foundation Masterclass"
    assert cert_out.digital_seal["status"] == "VERIFIED_AUTHENTIC"
    assert cert_out.instructor_name == "Acharya Rahul Sharma"
    assert len(cert_out.cryptographic_signature) == 64
    assert len(cert_out.canonical_hash) == 64
    assert cert_out.is_signature_valid is True
    assert cert_out.tamper_check["status"] == "CRYPTOGRAPHICALLY_VERIFIED_AUTHENTIC"

    # Test anti-tampering check with forged signature token
    tampered_data = CourseService.generate_course_certificate_data(
        enrollment, course, user, signature_token="fake_malicious_signature_token"
    )
    assert tampered_data["is_signature_valid"] is False
    assert tampered_data["tamper_check"]["status"] == "TAMPERED_OR_INVALID_SIGNATURE"
    assert tampered_data["digital_seal"]["status"] == "TAMPERED"

    # Validate HTML renderer
    html = CourseService.generate_course_certificate_html(cert_data)
    assert "Samiran Samanta" in html
    assert "Vedic Astrology Foundation Masterclass" in html
    assert "ASTRA-CERT-SAMIRAN-TEST" in html
    assert "DivinLink Gurukul" in html
    assert "HMAC-SHA256" in html

    # Check QR code contains properly percent-encoded verification link
    import urllib.parse
    expected_encoded_url = urllib.parse.quote(cert_data["verification_url"], safe="")
    assert f"data={expected_encoded_url}" in html


def test_public_certificate_verification_signature_enforcement():
    """Validates that public verification strictly requires and enforces the ?sig= token."""
    from datetime import datetime, timezone
    from beanie import PydanticObjectId
    from app.models.user import User

    user_id = PydanticObjectId()
    course_id = PydanticObjectId()
    user = User(id=user_id, email="student@example.com", first_name="Astra", last_name="Student")
    course = Course(id=course_id, title="Jyotish Masterclass", slug="jyotish")
    enrollment = CourseEnrollment(
        user_id=user_id,
        course_id=course_id,
        progress_percent=100.0,
        certificate_issued=True,
        certificate_id="ASTRA-CERT-PUBLIC-TEST",
        certificate_issued_at=datetime.now(timezone.utc),
    )

    # 1. Public verification without sig token MUST fail
    unauthed = CourseService.generate_course_certificate_data(
        enrollment, course, user, signature_token=None, is_public_verification=True
    )
    assert unauthed["is_valid"] is False
    assert unauthed["tamper_check"]["status"] == "SIGNATURE_REQUIRED_FOR_VERIFICATION"
    assert unauthed["digital_seal"]["status"] == "UNVERIFIED_MISSING_SIGNATURE"

    # 2. Public verification with fake sig token MUST fail
    forged = CourseService.generate_course_certificate_data(
        enrollment, course, user, signature_token="bad_signature_0000000000", is_public_verification=True
    )
    assert forged["is_valid"] is False
    assert forged["tamper_check"]["status"] == "TAMPERED_OR_INVALID_SIGNATURE"
    assert forged["digital_seal"]["status"] == "TAMPERED"

    # 3. Public verification with authentic sig token MUST succeed
    valid_sig = enrollment.certificate_signature[:32]
    authed = CourseService.generate_course_certificate_data(
        enrollment, course, user, signature_token=valid_sig, is_public_verification=True
    )
    assert authed["is_valid"] is True
    assert authed["tamper_check"]["status"] == "CRYPTOGRAPHICALLY_VERIFIED_AUTHENTIC"
    assert authed["digital_seal"]["status"] == "VERIFIED_AUTHENTIC"


def test_microsecond_truncation_does_not_break_signature_verification():
    """
    Validates that MongoDB's millisecond/microsecond truncation never corrupts
    the canonical SHA-256 hash or HMAC-SHA256 signature.
    """
    from datetime import datetime, timezone
    from beanie import PydanticObjectId
    from app.models.user import User

    user_id = PydanticObjectId()
    course_id = PydanticObjectId()
    user = User(id=user_id, email="student@example.com", first_name="Astra", last_name="Student")
    course = Course(id=course_id, title="Vedic Jyotish", slug="vedic-jyotish")

    # Time with arbitrary microseconds
    now_full_micro = datetime(2026, 11, 15, 14, 30, 45, 987654, tzinfo=timezone.utc)
    # MongoDB BSON Date drops microseconds to milliseconds (.987000)
    mongo_truncated_micro = datetime(2026, 11, 15, 14, 30, 45, 987000, tzinfo=timezone.utc)
    # Or rounded to zero microseconds
    zero_micro = datetime(2026, 11, 15, 14, 30, 45, 0, tzinfo=timezone.utc)

    iso_full = CourseService.format_certificate_issued_iso(now_full_micro)
    iso_mongo = CourseService.format_certificate_issued_iso(mongo_truncated_micro)
    iso_zero = CourseService.format_certificate_issued_iso(zero_micro)

    assert iso_full == "2026-11-15T14:30:45Z"
    assert iso_mongo == "2026-11-15T14:30:45Z"
    assert iso_zero == "2026-11-15T14:30:45Z"

    # Hash and signature must be 100% identical
    hash1, sig1 = CourseService.compute_certificate_crypto(
        "ASTRA-CERT-MICRO-TEST", str(user_id), "Astra Student", str(course_id), course.title, iso_full
    )
    hash2, sig2 = CourseService.compute_certificate_crypto(
        "ASTRA-CERT-MICRO-TEST", str(user_id), "Astra Student", str(course_id), course.title, iso_mongo
    )
    assert hash1 == hash2
    assert sig1 == sig2

    # Verify enrollment created with now_full_micro re-verifies perfectly when loaded with mongo_truncated_micro
    enrollment = CourseEnrollment(
        user_id=user_id,
        course_id=course_id,
        progress_percent=100.0,
        certificate_issued=True,
        certificate_id="ASTRA-CERT-MICRO-TEST",
        certificate_issued_at=now_full_micro,
    )
    cert1 = CourseService.generate_course_certificate_data(enrollment, course, user)
    assert cert1["is_valid"] is True

    # Simulate reloading enrollment from MongoDB where microseconds were truncated
    enrollment.certificate_issued_at = mongo_truncated_micro
    cert2 = CourseService.generate_course_certificate_data(
        enrollment, course, user, signature_token=cert1["cryptographic_signature"][:32], is_public_verification=True
    )
    assert cert2["is_valid"] is True
    assert cert2["tamper_check"]["status"] == "CRYPTOGRAPHICALLY_VERIFIED_AUTHENTIC"


def test_public_certificate_route_order():
    """Ensures static /courses/certificate/verify route precedes parameterized /{course_id}."""
    from app.api.v1.course import router

    verify_idx = None
    course_id_order_idx = None

    for idx, r in enumerate(router.routes):
        path = getattr(r, "path", None)
        if path == "/courses/certificate/verify/{certificate_id}":
            verify_idx = idx
        elif path == "/courses/{course_id}/order":
            course_id_order_idx = idx

    assert verify_idx is not None, "GET /courses/certificate/verify/{certificate_id} route must exist"
    assert course_id_order_idx is not None, "POST /courses/{course_id}/order route must exist"
    assert verify_idx < course_id_order_idx, (
        f"Route order error: verify route ({verify_idx}) must come before course_id route ({course_id_order_idx})"
    )


def test_api_response_ok_and_upload_result():
    """Ensures ApiResponse.ok helper and UploadResult secure_url are always available and do not raise AttributeError."""
    from app.schemas.common import ApiResponse
    from app.services.storage import UploadResult

    resp = ApiResponse.ok(data={"url": "https://res.cloudinary.com/test.webp"}, message="Uploaded")
    assert resp.success is True
    assert resp.message == "Uploaded"
    assert resp.data["url"] == "https://res.cloudinary.com/test.webp"

    res = ApiResponse(data={"key": "val"})
    assert res.success is True
    assert res.data["key"] == "val"

    upload = UploadResult(
        url="https://res.cloudinary.com/sample.webp",
        public_id="courses/thumbnails/sample",
        resource_type="image",
        folder="courses/thumbnails",
    )
    assert upload.url == "https://res.cloudinary.com/sample.webp"
    assert upload.secure_url == upload.url


@pytest.mark.asyncio
async def test_strict_enrollment_gate_no_staff_bypass():
    """Reading a course page must not enroll a member of staff.

    Narrow on purpose: it only covers `get_course_by_slug`. The two places
    that actually created enrollments are covered by the tests at the end
    of this file.
    """
    from unittest.mock import patch
    from beanie import PydanticObjectId

    admin_user = User(
        first_name="Admin",
        last_name="Acharya",
        role="admin",
        email="admin@gurukul.com",
    )
    course = Course(
        title="Exclusive Paid Masterclass",
        slug="exclusive-paid-masterclass",
        price=1999.0,
    )
    course.id = PydanticObjectId()

    with patch.object(Course, "find_one", new_callable=AsyncMock, return_value=course), \
         patch.object(CourseSection, "find", return_value=MagicMock(sort=MagicMock(return_value=MagicMock(to_list=AsyncMock(return_value=[]))))), \
         patch.object(CourseEnrollment, "find_one", new_callable=AsyncMock, return_value=None), \
         patch.object(CourseEnrollment, "insert", new_callable=AsyncMock) as mock_insert:

        detail = await CourseService.get_course_by_slug("exclusive-paid-masterclass", user=admin_user)
        assert detail["is_enrolled"] is False
        assert detail["user_progress_percent"] == 0.0
        mock_insert.assert_not_called()


def test_course_payment_and_admin_schemas():
    from datetime import datetime, timezone
    from app.schemas.course import (
        AdminCourseOrderListResponse,
        AdminCourseOrderOut,
        CourseOrderCreateResponse,
        CoursePaymentSyncResponse,
    )

    order_resp = CourseOrderCreateResponse(
        free_enrolled=True,
        already_paid=True,
        course_id="c1",
        course_title="Vedic Basics",
        course_slug="vedic-basics",
        message="Already paid",
    )
    assert order_resp.already_paid is True

    sync_resp = CoursePaymentSyncResponse(
        enrolled=True,
        status="paid",
        enrollment_id="e1",
        course_id="c1",
        course_slug="vedic-basics",
        course_title="Vedic Basics",
        message="Unlocked",
    )
    assert sync_resp.enrolled is True

    admin_list = AdminCourseOrderListResponse(
        items=[
            AdminCourseOrderOut(
                id="o1",
                user_id="u1",
                course_id="c1",
                razorpay_order_id="order_123",
                amount_paise=199900,
                amount_inr=1999.0,
                status="created",
                created_at=datetime.now(timezone.utc),
            )
        ],
        total=1,
        created_count=1,
    )
    assert admin_list.items[0].status == "created"


# --------------------------------------------------------- the staff bypass
@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["astrologer", "admin", "super_admin"])
async def test_watching_does_not_enroll_a_member_of_staff(role: str):
    """The hole `test_strict_enrollment_gate_no_staff_bypass` never covered.

    The player calls `update_progress` by itself the moment a video starts.
    That used to create an enrollment for anyone whose role contained "admin"
    or "astrologer", so opening the free sample of a paid course handed them
    the whole thing — for nothing, and for life.
    """
    from unittest.mock import patch

    from beanie import PydanticObjectId

    staff = User(first_name="A", last_name="B", role=role, email=f"{role}@gurukul.com")
    course_id, lesson_id = PydanticObjectId(), PydanticObjectId()

    with patch.object(CourseEnrollment, "find_one", new_callable=AsyncMock, return_value=None), \
         patch.object(CourseEnrollment, "insert", new_callable=AsyncMock) as mock_insert:

        result = await CourseService.update_progress(
            user=staff,
            course_id=course_id,
            lesson_id=lesson_id,
            watched_seconds=30,
            total_seconds=600,
        )

    mock_insert.assert_not_called()
    assert result["progress_percent"] == 0.0
    assert "not enrolled" in result["message"].lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["astrologer", "admin", "super_admin"])
async def test_staff_cannot_mint_a_certificate_for_a_course_they_never_took(role: str):
    """The second hole, and the worse one.

    This used to create an enrollment already at 100% with the certificate
    issued — a verifiable credential for a course the holder never opened.
    """
    from unittest.mock import patch

    from beanie import PydanticObjectId

    from app.core.exceptions import ForbiddenError

    staff = User(first_name="A", last_name="B", role=role, email=f"{role}2@gurukul.com")
    course = Course(title="Paid", slug=f"paid-{role}", price=1999.0)
    course.id = PydanticObjectId()

    with patch.object(Course, "find_one", new_callable=AsyncMock, return_value=course), \
         patch.object(CourseEnrollment, "find_one", new_callable=AsyncMock, return_value=None), \
         patch.object(CourseEnrollment, "insert", new_callable=AsyncMock) as mock_insert:

        with pytest.raises(ForbiddenError) as excinfo:
            await CourseService.get_course_certificate(user=staff, course_id=course.id)

    mock_insert.assert_not_called()
    assert "not enrolled" in str(excinfo.value).lower()


def test_staff_is_decided_by_an_exact_role_not_a_substring():
    """`"admin" in role` would read a future `pending_astrologer` as staff."""
    from types import SimpleNamespace

    for role in ("astrologer", "admin", "super_admin"):
        assert CourseService._is_staff(SimpleNamespace(role=role)) is True, role

    for role in ("user", "pending_astrologer", "admin_assistant", "ex_admin", "badmin"):
        assert CourseService._is_staff(SimpleNamespace(role=role)) is False, role

    # A user object with no role at all must not come out as staff.
    assert CourseService._is_staff(SimpleNamespace()) is False


# ------------------------------------------------- earning a certificate
def test_a_lesson_cannot_be_completed_by_simply_saying_so():
    """The ten-second certificate.

    `mark_completed` comes from the same client that reports the position, so
    one request per lesson used to carry a student to 100% — certificate
    issued and emailed — without a second of video being played.
    """
    from types import SimpleNamespace

    from app.services.course_service import CourseService

    lesson = SimpleNamespace(duration_minutes=40)
    claimed = SimpleNamespace(credited_seconds=1, total_seconds=1)

    assert (
        CourseService._has_watched_enough(
            lesson=lesson, prog=claimed, mark_completed=True
        )
        is False
    )


def test_a_lesson_completes_once_enough_of_it_has_been_credited():
    from types import SimpleNamespace

    from app.services.course_service import COMPLETION_FRACTION, CourseService

    lesson = SimpleNamespace(duration_minutes=40)
    needed = int(40 * 60 * COMPLETION_FRACTION)

    just_under = SimpleNamespace(credited_seconds=needed - 1, total_seconds=2400)
    assert CourseService._has_watched_enough(
        lesson=lesson, prog=just_under, mark_completed=True
    ) is False

    enough = SimpleNamespace(credited_seconds=needed, total_seconds=2400)
    assert CourseService._has_watched_enough(
        lesson=lesson, prog=enough, mark_completed=True
    ) is True


def test_the_servers_own_duration_is_what_counts():
    """A client that inflates its own `total_seconds` gains nothing."""
    from types import SimpleNamespace

    from app.services.course_service import CourseService

    lesson = SimpleNamespace(duration_minutes=40)
    # Claims the lesson is two seconds long and that both were watched.
    liar = SimpleNamespace(credited_seconds=2, total_seconds=2)

    assert CourseService._has_watched_enough(
        lesson=lesson, prog=liar, mark_completed=True
    ) is False


def test_a_lesson_with_no_recorded_length_falls_back_to_the_player():
    """Older lessons have no duration. They must still be completable."""
    from types import SimpleNamespace

    from app.services.course_service import COMPLETION_FRACTION, CourseService

    lesson = SimpleNamespace(duration_minutes=0)
    prog = SimpleNamespace(credited_seconds=int(600 * COMPLETION_FRACTION), total_seconds=600)

    assert CourseService._has_watched_enough(
        lesson=lesson, prog=prog, mark_completed=True
    ) is True


def test_real_time_is_what_bounds_the_credit():
    """A 40 minute lesson cannot be credited in ten seconds, whatever the
    player claims, because credit is capped by the clock."""
    from app.services.course_service import (
        COMPLETION_FRACTION,
        MAX_PLAYBACK_SPEED,
        PING_GRACE_SECONDS,
    )

    needed = 40 * 60 * COMPLETION_FRACTION
    # The most that can be credited in ten seconds of real time.
    best_case = 10 * MAX_PLAYBACK_SPEED + PING_GRACE_SECONDS
    assert best_case < needed

    # And the honest floor: even at the fastest playback the players offer.
    minimum_real_seconds = needed / MAX_PLAYBACK_SPEED
    assert minimum_real_seconds > 13 * 60


# ------------------------------------------------- the certificate number
def test_certificate_numbers_are_random_not_derived():
    """They used to be built out of the ids they belonged to, so one student's
    number could be worked out from another's — and two students whose
    ObjectIds ended alike shared a number outright."""
    from app.services.course_service import CourseService

    minted = {CourseService.mint_certificate_id() for _ in range(500)}
    assert len(minted) == 500, "certificate numbers collided"

    for number in list(minted)[:20]:
        assert number.startswith("ASTRA-CERT-")
        suffix = number.removeprefix("ASTRA-CERT-")
        assert len(suffix) == 16, suffix
        assert all(c in "0123456789ABCDEF" for c in suffix), suffix


# ------------------------------------------------- expires_at & renewals
def test_enrollment_active_and_expiration():
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace
    from app.services.course_service import CourseService

    # 1. Lifetime access (expires_at is None)
    lifetime_enr = SimpleNamespace(expires_at=None)
    assert CourseService.is_enrollment_active(lifetime_enr) is True

    # 2. Future expiration
    future_enr = SimpleNamespace(expires_at=datetime.now(timezone.utc) + timedelta(days=30))
    assert CourseService.is_enrollment_active(future_enr) is True

    # 3. Past expiration
    expired_enr = SimpleNamespace(expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    assert CourseService.is_enrollment_active(expired_enr) is False

    # 4. None enrollment
    assert CourseService.is_enrollment_active(None) is False


# ------------------------------------------------- price & free course guard
def test_course_pricing_intent_safeguards():
    import pytest
    from pydantic import ValidationError
    from app.schemas.course import CourseCreateRequest

    base_payload = {
        "title": "Vedic Astrology Masterclass",
        "slug": "vedic-astrology-masterclass",
        "description": "Comprehensive course",
        "thumbnail_url": "https://example.com/thumb.jpg",
        "mrp": 2999,
    }

    # 1. Accidental price 0 without is_free=True must fail
    with pytest.raises(ValidationError) as exc:
        CourseCreateRequest(**base_payload, price=0.0, is_free=False)
    assert "Course price is ₹0. To publish a free course" in str(exc.value)

    # 2. Explicit free course with is_free=True must succeed
    free_req = CourseCreateRequest(**base_payload, price=0.0, is_free=True)
    assert free_req.price == 0.0
    assert free_req.is_free is True

    # 3. Paid course with positive price must succeed
    paid_req = CourseCreateRequest(**base_payload, price=999.0, is_free=False)
    assert paid_req.price == 999.0
    assert paid_req.is_free is False

    # 4. Inconsistent: positive price with is_free=True must fail
    with pytest.raises(ValidationError) as exc2:
        CourseCreateRequest(**base_payload, price=999.0, is_free=True)
    assert "Course price cannot be greater than ₹0 when is_free=True" in str(exc2.value)


# ------------------------------------------------- youtube_unlisted masking
@pytest.mark.asyncio
async def test_youtube_unlisted_video_id_is_masked_from_stream_response():
    from unittest.mock import AsyncMock, MagicMock, patch
    from beanie import PydanticObjectId
    from types import SimpleNamespace
    from app.services.course_service import CourseService
    from app.models.course import CourseLesson, CourseEnrollment, CourseLessonProgress

    mock_lesson = SimpleNamespace(
        id=PydanticObjectId(),
        course_id=PydanticObjectId(),
        title="Secret Paid Lesson",
        is_published=True,
        is_free_preview=False,
        video_provider="youtube_unlisted",
        video_id="RAW_UNLISTED_YT_ID_123",
        library_id=None,
        duration_minutes=45,
        notes_markdown="",
        resources=[],
    )

    mock_enr = SimpleNamespace(
        id=PydanticObjectId(),
        expires_at=None,
        completed_lesson_ids=[],
    )

    with patch.object(CourseLesson, "find_one", AsyncMock(return_value=mock_lesson)):
        with patch.object(CourseEnrollment, "find_one", AsyncMock(return_value=mock_enr)):
            with patch.object(CourseLessonProgress, "find_one", AsyncMock(return_value=None)):
                with patch("app.models.user.User"):
                    mock_user = SimpleNamespace(id=PydanticObjectId(), email="student@example.com")
                    stream_res = await CourseService.get_lesson_stream(
                        course_id=mock_lesson.course_id,
                        lesson_id=mock_lesson.id,
                        user=mock_user,
                    )

                    # Raw video_id must NOT be exposed
                    assert stream_res["video_id"] is None
                    # Secure embed URL must be provided with rel=0, enablejsapi=1 & modestbranding
                    assert "RAW_UNLISTED_YT_ID_123" in stream_res["embed_url"]
                    assert "youtube-nocookie.com/embed" in stream_res["embed_url"]
                    assert "enablejsapi=1" in stream_res["embed_url"]
                    assert "rel=0" in stream_res["embed_url"]


@pytest.mark.asyncio
async def test_update_progress_atomic_add_to_set_preserves_completed_lessons():
    """Validates that update_progress uses atomic $addToSet and does not overwrite existing completed lessons."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, MagicMock, patch
    from beanie import PydanticObjectId
    course_id = PydanticObjectId()
    lesson1_id = PydanticObjectId()
    user_id = PydanticObjectId()
    mock_user = SimpleNamespace(id=user_id, email="student@example.com")

    update_mock = AsyncMock()
    enr_mock = SimpleNamespace(
        id=PydanticObjectId(),
        user_id=user_id,
        course_id=course_id,
        expires_at=None,
        completed_lesson_ids=[str(lesson1_id)],
        progress_percent=50.0,
        certificate_issued=False,
        certificate_id=None,
        certificate_issued_at=None,
        certificate_canonical_hash=None,
        certificate_signature=None,
        certificate_url=None,
        certificate_email_sent=False,
        update=update_mock,
    )

    class MockBeanieQuery:
        def __init__(self, result):
            self.result = result
            self.update = update_mock

        def __await__(self):
            async def _coro():
                return self.result
            return _coro().__await__()

    mock_query = MockBeanieQuery(enr_mock)
    find_one_mock = MagicMock(return_value=mock_query)

    with patch.object(CourseEnrollment, "find_one", find_one_mock), \
         patch.object(CourseLesson, "find_one", AsyncMock(return_value=SimpleNamespace(id=lesson1_id, course_id=course_id, duration_minutes=10))), \
         patch.object(CourseLessonProgress, "find_one", AsyncMock(return_value=SimpleNamespace(
             watched_seconds=600, total_seconds=600, credited_seconds=600,
             first_watched_at=None, last_watched_at=None, is_completed=True, save=AsyncMock()
         ))), \
         patch.object(CourseService, "_has_watched_enough", return_value=True), \
         patch("app.models.course.CourseLesson.find", return_value=SimpleNamespace(count=AsyncMock(return_value=2))):

        res = await CourseService.update_progress(
            user=mock_user,
            course_id=course_id,
            lesson_id=lesson1_id,
            watched_seconds=600,
            total_seconds=600,
            mark_completed=True,
        )

    # Validate atomic $addToSet was invoked
    update_mock.assert_any_call({"$addToSet": {"completed_lesson_ids": str(lesson1_id)}})


@pytest.mark.asyncio
async def test_qa_unenrolled_user_cannot_answer_question():
    """Validates that a non-staff user without course enrollment cannot post an answer (Q&A spam protection)."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch
    from beanie import PydanticObjectId
    from app.core.exceptions import ForbiddenError
    from app.models.course import CourseQuestion, CourseEnrollment, CourseLesson

    user_id = PydanticObjectId()
    course_id = PydanticObjectId()
    question_id = PydanticObjectId()
    lesson_id = PydanticObjectId()

    student_user = SimpleNamespace(id=user_id, role="user", full_name="Outsider")
    mock_question = SimpleNamespace(
        id=question_id,
        course_id=course_id,
        lesson_id=lesson_id,
        is_hidden=False,
        answers=[],
        answer_count=0,
        has_official_answer=False,
        is_resolved=False,
        save=AsyncMock(),
    )

    with patch.object(CourseQuestion, "find_one", AsyncMock(return_value=mock_question)), \
         patch.object(CourseEnrollment, "find_one", AsyncMock(return_value=None)), \
         patch.object(CourseLesson, "find_one", AsyncMock(return_value=SimpleNamespace(id=lesson_id, is_free_preview=False))):

        with pytest.raises(ForbiddenError) as exc_info:
            await CourseService.answer_question(
                user=student_user,
                question_id=question_id,
                content="Spam link or unauthorized answer",
            )
        assert exc_info.value.error_code == "not_enrolled"


@pytest.mark.asyncio
async def test_qa_expired_enrollment_user_cannot_answer_question():
    """Validates that an enrolled student whose access expired cannot post an answer."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch
    from beanie import PydanticObjectId
    from datetime import datetime, timezone, timedelta
    from app.core.exceptions import ForbiddenError
    from app.models.course import CourseQuestion, CourseEnrollment, CourseLesson

    user_id = PydanticObjectId()
    course_id = PydanticObjectId()
    question_id = PydanticObjectId()
    lesson_id = PydanticObjectId()

    student_user = SimpleNamespace(id=user_id, role="user", full_name="Expired Student")
    mock_question = SimpleNamespace(
        id=question_id,
        course_id=course_id,
        lesson_id=lesson_id,
        is_hidden=False,
        answers=[],
        save=AsyncMock(),
    )
    # Expired enrollment
    expired_enr = SimpleNamespace(
        id=PydanticObjectId(),
        user_id=user_id,
        course_id=course_id,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )

    with patch.object(CourseQuestion, "find_one", AsyncMock(return_value=mock_question)), \
         patch.object(CourseEnrollment, "find_one", AsyncMock(return_value=expired_enr)), \
         patch.object(CourseLesson, "find_one", AsyncMock(return_value=SimpleNamespace(id=lesson_id, is_free_preview=False))):

        with pytest.raises(ForbiddenError) as exc_info:
            await CourseService.answer_question(
                user=student_user,
                question_id=question_id,
                content="My expired reply",
            )
        assert exc_info.value.error_code == "enrollment_expired"


@pytest.mark.asyncio
async def test_qa_hidden_question_rejected_for_students():
    """Validates that answering or upvoting a hidden (spam/abuse) question is blocked for non-staff."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch
    from beanie import PydanticObjectId
    from app.core.exceptions import NotFoundError
    from app.models.course import CourseQuestion

    user_id = PydanticObjectId()
    course_id = PydanticObjectId()
    question_id = PydanticObjectId()

    student_user = SimpleNamespace(id=user_id, role="user", full_name="Active Student")
    hidden_question = SimpleNamespace(
        id=question_id,
        course_id=course_id,
        is_hidden=True,
        answers=[],
        upvote_user_ids=[],
        save=AsyncMock(),
    )

    with patch.object(CourseQuestion, "find_one", AsyncMock(return_value=hidden_question)):
        with pytest.raises(NotFoundError):
            await CourseService.answer_question(
                user=student_user,
                question_id=question_id,
                content="Answering a hidden question",
            )

        with pytest.raises(NotFoundError):
            await CourseService.toggle_question_upvote(
                user=student_user,
                question_id=question_id,
            )


@pytest.mark.asyncio
async def test_qa_staff_can_answer_even_without_enrollment():
    """Validates that faculty/admin/astrologer can answer questions (official answer) without regular enrollment."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch
    from beanie import PydanticObjectId
    from app.models.course import CourseQuestion
    from app.models.enums import UserRole

    admin_id = PydanticObjectId()
    course_id = PydanticObjectId()
    question_id = PydanticObjectId()
    lesson_id = PydanticObjectId()

    admin_user = SimpleNamespace(id=admin_id, role=UserRole.ADMIN, full_name="Pt. Shiva (Guru)")
    mock_question = SimpleNamespace(
        id=question_id,
        course_id=course_id,
        lesson_id=lesson_id,
        is_hidden=False,
        answers=[],
        answer_count=0,
        has_official_answer=False,
        is_resolved=False,
        updated_at=None,
        save=AsyncMock(),
    )

    with patch.object(CourseQuestion, "find_one", AsyncMock(return_value=mock_question)):
        ans = await CourseService.answer_question(
            user=admin_user,
            question_id=question_id,
            content="Official explanation of 7th house Saturn.",
            mark_resolved=True,
        )
        assert ans.is_official is True
        assert ans.user_role == "admin"
        assert ans.content == "Official explanation of 7th house Saturn."
        assert mock_question.has_official_answer is True
        assert mock_question.is_resolved is True
        assert mock_question.save.called


@pytest.mark.asyncio
async def test_qa_empty_content_rejected():
    """Validates that empty or whitespace-only answers are rejected with BadRequestError."""
    from types import SimpleNamespace
    from beanie import PydanticObjectId
    from app.core.exceptions import BadRequestError

    user = SimpleNamespace(id=PydanticObjectId(), role="user")
    with pytest.raises(BadRequestError):
        await CourseService.answer_question(
            user=user,
            question_id=PydanticObjectId(),
            content="   \n   ",
        )


def test_signed_bunny_embed_url():
    """Validates that get_signed_bunny_embed_url generates a tokenized URL preventing 403 Forbidden."""
    from unittest.mock import patch
    with patch("app.core.config.settings.BUNNY_STREAM_TOKEN_KEY", "test_secret_key_123"), \
         patch("app.core.config.settings.BUNNY_STREAM_LIBRARY_ID", "803267"):
        url = CourseService.get_signed_bunny_embed_url("6af0c892-1430-970e-2598-77ef12345678")
        assert "https://iframe.mediadelivery.net/embed/803267/6af0c892-1430-970e-2598-77ef12345678" in url
        assert "?token=" in url
        assert "&expires=" in url


@pytest.mark.asyncio
async def test_discount_percent_reset_when_mrp_lowered():
    """Validates that updating a course with mrp <= price resets discount_percent to 0."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch
    from beanie import PydanticObjectId
    from app.api.v1.admin_course import admin_update_course
    from app.schemas.course import CourseUpdateRequest

    course_id = PydanticObjectId()
    existing_course = SimpleNamespace(
        id=course_id,
        mrp=1000.0,
        price=500.0,
        discount_percent=50,
        thumbnail_url=None,
        promo_video_url=None,
        promo_video_provider=None,
        instructor_avatar=None,
        updated_at=None,
        save=AsyncMock(),
    )

    with patch("app.api.v1.admin_course.Course.find_one", AsyncMock(return_value=existing_course)):
        # Admin updates price to 500 and MRP to 500 (discount removed)
        update_payload = CourseUpdateRequest(price=500.0, mrp=500.0)
        res = await admin_update_course(
            course_id=course_id,
            payload=update_payload,
            _=SimpleNamespace(),
        )
        assert existing_course.discount_percent == 0
        assert existing_course.save.called


@pytest.mark.asyncio
async def test_admin_delete_course_blocked_when_active_enrollments():
    """Validates that deleting a course with enrolled students is blocked unless force=True."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch
    from beanie import PydanticObjectId
    from app.core.exceptions import BadRequestError
    from app.api.v1.admin_course import admin_delete_course

    course_id = PydanticObjectId()
    existing_course = SimpleNamespace(
        id=course_id,
        thumbnail_url=None,
        instructor_avatar=None,
        promo_video_url=None,
        slug="astrology-101",
        is_deleted=False,
        is_published=True,
        save=AsyncMock(),
    )

    with patch("app.api.v1.admin_course.Course.find_one", AsyncMock(return_value=existing_course)), \
         patch("app.api.v1.admin_course.CourseEnrollment.find", return_value=SimpleNamespace(count=AsyncMock(return_value=5))):

        # Deleting without force=True must raise BadRequestError
        with pytest.raises(BadRequestError) as exc_info:
            await admin_delete_course(
                course_id=course_id,
                _=SimpleNamespace(),
                force=False,
            )
        assert "5 student(s) are currently enrolled" in str(exc_info.value.message)

        # Deleting with force=True succeeds
        res = await admin_delete_course(
            course_id=course_id,
            _=SimpleNamespace(),
            force=True,
        )
        assert existing_course.is_deleted is True
        assert existing_course.is_published is False
        assert existing_course.save.called



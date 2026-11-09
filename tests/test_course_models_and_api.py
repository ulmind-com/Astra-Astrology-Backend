"""Tests for Astra Gurukul Course document models, schemas and service layer."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from beanie import init_beanie

from app.models.course import (
    Course,
    CourseEnrollment,
    CourseLesson,
    CourseLessonProgress,
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
    course_id_index = None

    for idx, r in enumerate(router.routes):
        if getattr(r, "path", None) == "/admin/courses/questions" and "GET" in getattr(r, "methods", set()):
            questions_index = idx
        elif getattr(r, "path", None) == "/admin/courses/{course_id}" and "GET" in getattr(r, "methods", set()):
            course_id_index = idx

    assert questions_index is not None, "GET /admin/courses/questions route must exist"
    assert course_id_index is not None, "GET /admin/courses/{course_id} route must exist"
    assert questions_index < course_id_index, (
        f"Route shadowing bug! /admin/courses/questions (idx {questions_index}) "
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







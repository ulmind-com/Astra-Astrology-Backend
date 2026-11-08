"""Tests for Astra Gurukul Course document models, schemas and service layer."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from beanie import init_beanie

from app.models.course import (
    Course,
    CourseEnrollment,
    CourseLesson,
    CourseLessonProgress,
    CourseSection,
)
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




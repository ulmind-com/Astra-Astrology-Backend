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

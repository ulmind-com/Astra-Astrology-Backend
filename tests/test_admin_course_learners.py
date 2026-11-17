"""Unit tests for Admin Course Learners & Student Progress Analytics."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from beanie import PydanticObjectId, init_beanie

from app.models.course import Course, CourseSection, CourseLesson, CourseEnrollment, CourseLessonProgress
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
    mock_db.__getitem__.return_value = mock_coll

    await init_beanie(
        database=mock_db,
        document_models=[
            Course,
            CourseSection,
            CourseLesson,
            CourseEnrollment,
            CourseLessonProgress,
            User,
        ],
    )


@pytest.mark.asyncio
async def test_admin_course_learners_and_progress_logic():
    course_id = PydanticObjectId()
    user_id = PydanticObjectId()
    section_id = PydanticObjectId()
    lesson1_id = PydanticObjectId()
    lesson2_id = PydanticObjectId()

    test_course = Course(
        id=course_id,
        title="Vedic Astrology Mastery",
        slug="vedic-astrology-mastery",
        category="vedic_astrology",
        level="all_levels",
        language="bn",
        price=1999.0,
        mrp=3999.0,
        instructor_name="Acharya Dev",
        is_published=True,
    )

    test_user = User(
        id=user_id,
        first_name="Arjun",
        last_name="Roy",
        email="learner@example.com",
        phone="9876543210",
        full_name="Arjun Roy",
        role="user",
        hashed_password="dummy",
    )

    test_enrollment = CourseEnrollment(
        id=PydanticObjectId(),
        user_id=user_id,
        course_id=course_id,
        amount_paid=1999.0,
        currency="INR",
        payment_id="pay_test123",
        order_id="order_test123",
        progress_percent=50.0,
        completed_lesson_ids=[str(lesson1_id)],
        enrolled_at=datetime.now(timezone.utc),
    )

    test_section = CourseSection(
        id=section_id,
        course_id=course_id,
        title="Module 1: Foundations",
        order=1,
    )

    test_lesson1 = CourseLesson(
        id=lesson1_id,
        course_id=course_id,
        section_id=section_id,
        title="Lesson 1: Intro",
        order=1,
        duration_minutes=15,
        video_provider="bunny_stream",
        video_id="dummy-vid-1",
    )
    test_lesson2 = CourseLesson(
        id=lesson2_id,
        course_id=course_id,
        section_id=section_id,
        title="Lesson 2: Houses",
        order=2,
        duration_minutes=20,
        video_provider="bunny_stream",
        video_id="dummy-vid-2",
    )

    test_progress1 = CourseLessonProgress(
        user_id=user_id,
        course_id=course_id,
        lesson_id=lesson1_id,
        watched_seconds=900,
        credited_seconds=900,
        is_completed=True,
        completed_at=datetime.now(timezone.utc),
    )

    # Patch Course.get, CourseLesson.find().count(), CourseEnrollment.find().sort().to_list(), User.find().to_list()
    with patch.object(Course, "get", new_callable=AsyncMock) as mock_course_get:
        mock_course_get.return_value = test_course

        with patch.object(CourseLesson, "find") as mock_lesson_find:
            mock_lesson_find.return_value.count = AsyncMock(return_value=2)
            mock_lesson_find.return_value.sort.return_value.to_list = AsyncMock(return_value=[test_lesson1, test_lesson2])

            with patch.object(CourseEnrollment, "find") as mock_enroll_find:
                mock_enroll_find.return_value.sort.return_value.to_list = AsyncMock(return_value=[test_enrollment])

                with patch.object(User, "find") as mock_user_find:
                    mock_user_find.return_value.to_list = AsyncMock(return_value=[test_user])

                    learners_data = await CourseService.admin_get_course_learners(
                        course_id=course_id,
                        page=1,
                        limit=10,
                    )

                    assert learners_data["course_id"] == str(course_id)
                    assert learners_data["stats"]["total_enrolled"] == 1
                    assert learners_data["stats"]["in_progress_count"] == 1
                    assert learners_data["stats"]["average_progress_percent"] == 50.0
                    assert learners_data["stats"]["total_revenue"] == 1999.0
                    assert learners_data["stats"]["total_lessons_in_course"] == 2
                    assert len(learners_data["items"]) == 1

                    item = learners_data["items"][0]
                    assert item["student_name"] == "Arjun Roy"
                    assert item["student_email"] == "learner@example.com"
                    assert item["completed_lessons_count"] == 1
                    assert item["total_lessons_count"] == 2

    # Test detailed progress
    with patch.object(Course, "get", new_callable=AsyncMock) as mock_course_get:
        mock_course_get.return_value = test_course

        with patch.object(CourseEnrollment, "find_one", new_callable=AsyncMock) as mock_enroll_one:
            mock_enroll_one.return_value = test_enrollment

            with patch.object(User, "get", new_callable=AsyncMock) as mock_user_get:
                mock_user_get.return_value = test_user

                with patch.object(CourseSection, "find") as mock_sec_find:
                    mock_sec_find.return_value.sort.return_value.to_list = AsyncMock(return_value=[test_section])

                    with patch.object(CourseLesson, "find") as mock_les_find:
                        mock_les_find.return_value.sort.return_value.to_list = AsyncMock(return_value=[test_lesson1, test_lesson2])

                        with patch.object(CourseLessonProgress, "find") as mock_prog_find:
                            mock_prog_find.return_value.to_list = AsyncMock(return_value=[test_progress1])

                            detail = await CourseService.admin_get_learner_progress(
                                course_id=course_id,
                                user_id=user_id,
                            )

                            assert detail["user_id"] == str(user_id)
                            assert detail["progress_percent"] == 50.0
                            assert detail["completed_lessons_count"] == 1
                            assert detail["total_lessons_count"] == 2
                            assert len(detail["sections"]) == 1
                            assert len(detail["sections"][0]["lessons"]) == 2
                            assert detail["sections"][0]["lessons"][0]["is_completed"] is True
                            assert detail["sections"][0]["lessons"][1]["is_completed"] is False

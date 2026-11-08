"""Course, Lesson, Enrollment, and Certification Document Models for Astra Gurukul LMS."""

from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field
import pymongo


class Course(Document):
    """Represents a masterclass or course in Astra Astrology Gurukul."""

    title: str = Field(..., max_length=200, description="Full title of the course")
    slug: Indexed(str, unique=True) = Field(..., max_length=220, description="URL friendly unique slug")
    subtitle: str = Field("", max_length=300, description="Brief compelling headline")
    description: str = Field("", description="Detailed markdown curriculum description and benefits")

    category: Indexed(str) = Field(
        default="vedic_astrology",
        description="Category: vedic_astrology, tarot, palmistry, numerology, lal_kitab, vastu, general",
    )
    level: str = Field(
        default="all_levels",
        description="Difficulty: beginner, intermediate, advanced, master, all_levels",
    )
    language: str = Field(default="bn", description="Primary course language: bn, hi, en")

    # Instructor Profile
    instructor_name: str = Field(default="Pt. Acharya Rahul Sharma", description="Lead instructor or astrologer")
    instructor_title: str = Field(default="Senior Vedic Jyotishacharya", description="Designation")
    instructor_avatar: str | None = Field(default=None, description="Image URL of instructor")
    instructor_bio: str | None = Field(default=None, description="Short bio of instructor")

    # Media & Visuals
    thumbnail_url: str = Field(default="", description="Course card and banner image URL")
    promo_video_url: str | None = Field(default=None, description="Trailer / introduction video URL")
    promo_video_provider: str = Field(default="youtube", description="youtube or bunny_stream")

    # Pricing & Monetization (in ₹ INR)
    price: float = Field(default=0.0, ge=0, description="Actual selling price in ₹ INR")
    mrp: float = Field(default=0.0, ge=0, description="Original crossed-out MRP in ₹ INR")
    discount_percent: int = Field(default=0, ge=0, le=100)
    currency: str = Field(default="INR")

    # Metrics
    duration_hours: float = Field(default=0.0, ge=0, description="Approximate course length in hours")
    total_lessons: int = Field(default=0, ge=0, description="Total number of video lessons")
    total_students: int = Field(default=0, ge=0, description="Number of enrolled students")
    average_rating: float = Field(default=5.0, ge=1.0, le=5.0)
    rating_count: int = Field(default=0, ge=0)

    # Highlights & Learning Objectives
    what_you_will_learn: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    # Status & Certification
    is_published: bool = Field(default=True)
    is_featured: bool = Field(default=False)
    certificate_enabled: bool = Field(default=True, description="Whether students get a verifiable certificate")
    is_deleted: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "courses"
        indexes = [
            [("slug", pymongo.ASCENDING)],
            [("category", pymongo.ASCENDING), ("is_published", pymongo.ASCENDING)],
            [("is_featured", pymongo.ASCENDING)],
            [("is_deleted", pymongo.ASCENDING)],
            [("created_at", pymongo.DESCENDING)],
        ]


class CourseSection(Document):
    """A chapter or module inside a course."""

    course_id: Indexed(PydanticObjectId)
    title: str = Field(..., max_length=200)
    order: int = Field(default=1)
    description: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "course_sections"
        indexes = [
            [("course_id", pymongo.ASCENDING), ("order", pymongo.ASCENDING)],
        ]


class CourseLesson(Document):
    """An individual recorded video lesson inside a course module."""

    course_id: Indexed(PydanticObjectId)
    section_id: Indexed(PydanticObjectId)
    title: str = Field(..., max_length=250)
    order: int = Field(default=1)
    duration_minutes: int = Field(default=0, ge=0)

    # Video Hosting Specifications
    video_provider: str = Field(
        default="bunny_stream",
        description="bunny_stream, youtube_unlisted, or direct_hls",
    )
    video_id: str = Field(default="", description="Bunny Video GUID or YouTube video ID")
    library_id: str | None = Field(default=None, description="Bunny Stream Library ID if applicable")

    # Accessibility & Content
    is_free_preview: bool = Field(default=False, description="Available for free sample watching")
    summary: str | None = None
    notes_markdown: str | None = Field(default=None, description="Class notes & planetary tables")
    resources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Attached PDFs, charts, mantras: [{'title': '...', 'url': '...', 'type': 'pdf'}]",
    )
    is_published: bool = Field(default=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "course_lessons"
        indexes = [
            [("course_id", pymongo.ASCENDING), ("section_id", pymongo.ASCENDING), ("order", pymongo.ASCENDING)],
            [("is_free_preview", pymongo.ASCENDING)],
        ]


class CourseEnrollment(Document):
    """User enrollment & purchase record for a course."""

    user_id: Indexed(PydanticObjectId)
    course_id: Indexed(PydanticObjectId)
    enrolled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = Field(default=None, description="None = Lifetime Access")

    # Payment References
    payment_id: str | None = None
    order_id: str | None = None
    amount_paid: float = Field(default=0.0, ge=0)
    currency: str = Field(default="INR")

    # Learning Progress
    progress_percent: float = Field(default=0.0, ge=0, le=100)
    completed_lesson_ids: list[str] = Field(default_factory=list)
    last_accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Certificate Generation
    certificate_issued: bool = Field(default=False)
    certificate_id: str | None = None
    certificate_url: str | None = None
    certificate_issued_at: datetime | None = None

    class Settings:
        name = "course_enrollments"
        indexes = [
            [("user_id", pymongo.ASCENDING), ("course_id", pymongo.ASCENDING)],
            [("course_id", pymongo.ASCENDING)],
            [("enrolled_at", pymongo.DESCENDING)],
        ]


class CourseLessonProgress(Document):
    """Tracks a student's exact watched position inside each lesson."""

    user_id: Indexed(PydanticObjectId)
    course_id: Indexed(PydanticObjectId)
    lesson_id: Indexed(PydanticObjectId)

    watched_seconds: int = Field(default=0, ge=0)
    total_seconds: int = Field(default=0, ge=0)
    is_completed: bool = Field(default=False)
    last_watched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "course_lesson_progress"
        indexes = [
            [("user_id", pymongo.ASCENDING), ("lesson_id", pymongo.ASCENDING)],
            [("user_id", pymongo.ASCENDING), ("course_id", pymongo.ASCENDING)],
        ]

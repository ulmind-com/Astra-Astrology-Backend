"""Course, Lesson, Enrollment, and Certification Document Models for Astra Gurukul LMS."""

import secrets
from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field
import pymongo

from app.models.enums import PaymentOrderStatus


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
    certificate_email_sent: bool = Field(default=False)
    certificate_signature: str | None = None
    certificate_canonical_hash: str | None = None

    class Settings:
        name = "course_enrollments"
        indexes = [
            # Unique, because two paths now race to create it: the browser
            # coming back from checkout and Razorpay's webhook. Whichever
            # arrives second must collide rather than enroll the student
            # twice and count them twice in `total_students`.
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("course_id", pymongo.ASCENDING)],
                name="enrollment_user_course_unique",
                unique=True,
            ),
            [("course_id", pymongo.ASCENDING)],
            # Unique and sparse: a certificate number must identify exactly
            # one credential, and most enrollments have not earned one yet.
            pymongo.IndexModel(
                [("certificate_id", pymongo.ASCENDING)],
                name="enrollment_certificate_unique",
                unique=True,
                partialFilterExpression={"certificate_id": {"$type": "string"}},
            ),
            [("enrolled_at", pymongo.DESCENDING)],
        ]


class CourseOrder(Document):
    """One attempt to buy a course.

    This did not exist, and that is where the money went. A Razorpay order was
    opened and nothing was written down, so the only thing that could ever
    turn a payment into an enrollment was the browser coming back to say so.
    A closed tab, a dropped connection, an app sent to the background during
    UPI — the money left the bank and no record tied it to anything.

    Kept even when it fails or is abandoned: when a student says they paid and
    got nothing, this is the only place that shows the attempt happened.
    """

    user_id: Indexed(PydanticObjectId)
    course_id: Indexed(PydanticObjectId)

    razorpay_order_id: Indexed(str, unique=True)
    receipt: str = ""

    # Frozen when the order is opened. The student was shown this price before
    # they paid, so this is what the payment is checked against even if an
    # admin re-prices the course while the checkout window is still open.
    amount_paise: int = Field(gt=0)
    currency: str = "INR"

    status: PaymentOrderStatus = PaymentOrderStatus.CREATED

    razorpay_payment_id: str | None = None
    method: str | None = None  # upi / card / netbanking …
    failure_reason: str | None = None
    # Which path confirmed it: the browser callback, or the webhook.
    verified_via: str | None = None
    paid_at: datetime | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "course_orders"
        indexes = [
            [("razorpay_order_id", pymongo.ASCENDING)],
            [("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
            [("course_id", pymongo.ASCENDING)],
            [("status", pymongo.ASCENDING)],
        ]


class CourseLessonProgress(Document):
    """Tracks a student's exact watched position inside each lesson."""

    user_id: Indexed(PydanticObjectId)
    course_id: Indexed(PydanticObjectId)
    lesson_id: Indexed(PydanticObjectId)

    # What the player says the playhead is at. Useful for resuming, and
    # nothing else: it comes from the client and a client can say anything.
    watched_seconds: int = Field(default=0, ge=0)
    total_seconds: int = Field(default=0, ge=0)

    # What the server is willing to believe was actually watched. Advanced in
    # steps no larger than the real time that passed between check-ins, so a
    # whole course cannot be completed in one request — which is how students
    # were collecting certificates in seconds.
    credited_seconds: int = Field(default=0, ge=0)
    first_watched_at: datetime | None = None

    is_completed: bool = Field(default=False)
    completed_at: datetime | None = None
    last_watched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "course_lesson_progress"
        indexes = [
            [("user_id", pymongo.ASCENDING), ("lesson_id", pymongo.ASCENDING)],
            [("user_id", pymongo.ASCENDING), ("course_id", pymongo.ASCENDING)],
        ]


class CourseQuestionAnswer(BaseModel):
    """An individual reply or official instructor explanation inside a Q&A thread."""

    id: str = Field(default_factory=lambda: secrets.token_hex(8))
    user_id: PydanticObjectId
    user_name: str = "Astra Student"
    user_role: str = "student"  # "student", "admin", "astrologer"
    user_avatar: str | None = None
    is_official: bool = False  # True when answered by Gurukul Acharya / Admin
    content: str = Field(..., min_length=1, max_length=5000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CourseQuestion(Document):
    """Timestamped discussion or question posted on a specific video lecture in Gurukul LMS."""

    course_id: Indexed(PydanticObjectId)
    section_id: Indexed(PydanticObjectId)
    lesson_id: Indexed(PydanticObjectId)
    user_id: Indexed(PydanticObjectId)

    # Student metadata at time of posting (denormalized for fast list rendering)
    user_name: str = "Astra Student"
    user_email: str | None = None
    user_phone: str | None = None
    user_avatar: str | None = None

    # Video timestamp in seconds (e.g. 185 = 03:05 in video)
    timestamp_seconds: int = Field(default=0, ge=0)
    timestamp_formatted: str = Field(default="00:00")  # "03:05" or "General"

    title: str = Field(..., min_length=2, max_length=300)
    content: str = Field(..., min_length=2, max_length=5000)

    # Community and Moderation
    upvote_user_ids: list[str] = Field(default_factory=list)
    upvote_count: int = Field(default=0)
    answers: list[CourseQuestionAnswer] = Field(default_factory=list)
    answer_count: int = Field(default=0)

    # Status & Flags
    is_resolved: bool = Field(default=False)
    has_official_answer: bool = Field(default=False)
    is_pinned: bool = Field(default=False)
    is_hidden: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "course_questions"
        indexes = [
            [("lesson_id", pymongo.ASCENDING), ("timestamp_seconds", pymongo.ASCENDING)],
            [("course_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
            [("user_id", pymongo.ASCENDING)],
            [("has_official_answer", pymongo.ASCENDING)],
            [("is_resolved", pymongo.ASCENDING)],
        ]


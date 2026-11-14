"""Pydantic schemas for Astra Gurukul Courses, Modules, Lessons & Enrollments."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class LessonResourceOut(BaseModel):
    title: str
    url: str
    type: str = "pdf"  # pdf, audio, image, link


class CourseLessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    section_id: str
    title: str
    order: int
    duration_minutes: int
    is_free_preview: bool
    summary: str | None = None
    resources_count: int = 0
    # Video streaming details are only populated for enrolled users or free previews
    video_provider: str | None = None
    video_id: str | None = None
    is_completed: bool = False


class CourseSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    order: int
    description: str | None = None
    lessons: list[CourseLessonOut] = Field(default_factory=list)


class CourseListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    subtitle: str = ""
    category: str = "vedic_astrology"
    level: str = "all_levels"
    language: str = "bn"
    instructor_name: str = "Senior Astrologer"
    instructor_title: str = "Vedic Jyotishacharya"
    instructor_avatar: str | None = None
    thumbnail_url: str = ""
    price: float = 0.0
    mrp: float = 0.0
    discount_percent: int = 0
    currency: str = "INR"
    duration_hours: float = 0.0
    total_lessons: int = 0
    total_students: int = 0
    average_rating: float = 5.0
    rating_count: int = 0
    is_featured: bool = False
    certificate_enabled: bool = True
    is_enrolled: bool = False
    user_progress_percent: float = 0.0


class CourseDetailOut(CourseListItemOut):
    description: str = ""
    promo_video_url: str | None = None
    promo_video_provider: str = "youtube"
    what_you_will_learn: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    sections: list[CourseSectionOut] = Field(default_factory=list)
    is_enrolled: bool = False
    user_progress_percent: float = 0.0
    certificate_issued: bool = False
    certificate_id: str | None = None
    certificate_url: str | None = None


class CourseEnrollmentOut(BaseModel):
    id: str
    course_id: str
    course_title: str | None = None
    course_slug: str | None = None
    thumbnail_url: str | None = None
    instructor_name: str | None = None
    enrolled_at: datetime
    expires_at: datetime | None = None
    progress_percent: float
    completed_lesson_ids: list[str]
    certificate_issued: bool
    certificate_id: str | None = None
    certificate_url: str | None = None


class LessonStreamResponse(BaseModel):
    """Secure playback response for an individual video lesson."""

    lesson_id: str
    title: str
    video_provider: str
    video_id: str
    library_id: str | None = None
    embed_url: str
    token: str | None = None
    expires_at: int | None = None
    watermark_text: str | None = None
    notes_markdown: str | None = None
    resources: list[LessonResourceOut] = Field(default_factory=list)
    last_watched_seconds: int = 0
    is_completed: bool = False


class LessonProgressUpdateRequest(BaseModel):
    watched_seconds: int = Field(..., ge=0)
    total_seconds: int = Field(..., ge=0)
    mark_completed: bool = False


class LessonProgressUpdateResponse(BaseModel):
    progress_percent: float = Field(default=0.0, ge=0, le=100)
    is_lesson_completed: bool = False
    certificate_issued: bool = False
    certificate_id: str | None = None
    certificate_url: str | None = None
    message: str | None = None


class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    slug: str = Field(..., min_length=3, max_length=220)
    subtitle: str = Field("", max_length=300)
    description: str = Field(...)
    category: str = Field(default="vedic_astrology")
    level: str = Field(default="all_levels")
    language: str = Field(default="bn")
    instructor_name: str = Field(default="Pt. Acharya Rahul Sharma")
    instructor_title: str = Field(default="Senior Vedic Jyotishacharya")
    instructor_avatar: str | None = None
    instructor_bio: str | None = None
    thumbnail_url: str = Field(...)
    promo_video_url: str | None = None
    promo_video_provider: str = Field(default="youtube")
    price: float = Field(..., ge=0)
    mrp: float = Field(..., ge=0)
    certificate_enabled: bool = True
    what_you_will_learn: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class CourseUpdateRequest(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    description: str | None = None
    category: str | None = None
    level: str | None = None
    language: str | None = None
    instructor_name: str | None = None
    instructor_title: str | None = None
    instructor_avatar: str | None = None
    thumbnail_url: str | None = None
    promo_video_url: str | None = None
    promo_video_provider: str | None = None
    price: float | None = None
    mrp: float | None = None
    is_published: bool | None = None
    is_featured: bool | None = None
    certificate_enabled: bool | None = None
    what_you_will_learn: list[str] | None = None
    prerequisites: list[str] | None = None
    tags: list[str] | None = None


# Order & Payment Schemas
class CourseOrderCreateResponse(BaseModel):
    free_enrolled: bool = False
    already_paid: bool = False
    order_id: str | None = None
    amount_paise: int = 0
    amount_inr: float = 0.0
    currency: str = "INR"
    key_id: str | None = None
    course_id: str
    course_title: str
    course_slug: str
    message: str | None = None


class CoursePaymentVerifyRequest(BaseModel):
    razorpay_order_id: str = Field(..., min_length=4)
    razorpay_payment_id: str = Field(..., min_length=4)
    razorpay_signature: str = Field(..., min_length=16)


class CoursePaymentSyncRequest(BaseModel):
    razorpay_order_id: str | None = None


class CoursePaymentSyncResponse(BaseModel):
    enrolled: bool
    status: str
    enrollment_id: str | None = None
    course_id: str
    course_slug: str
    course_title: str
    message: str = ""


# Admin Section & Lesson CRUD Schemas
class CourseSectionCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    order: int = Field(default=1, ge=1)
    description: str | None = None


class CourseSectionUpdateRequest(BaseModel):
    title: str | None = None
    order: int | None = None
    description: str | None = None


class CourseLessonCreateRequest(BaseModel):
    section_id: str
    title: str = Field(..., min_length=1, max_length=250)
    order: int = Field(default=1)
    duration_minutes: int = Field(default=0)
    video_provider: str = Field(default="bunny_stream")  # bunny_stream, youtube_unlisted
    video_id: str = Field(default="", max_length=250)  # Bunny video GUID or YouTube ID
    library_id: str | None = None
    is_free_preview: bool = False
    summary: str | None = None
    notes_markdown: str | None = None
    resources: list[LessonResourceOut] = Field(default_factory=list)

    @field_validator("duration_minutes", mode="before")
    @classmethod
    def parse_duration(cls, v: Any) -> int:
        if v is None:
            return 0
        try:
            return max(0, int(round(float(v))))
        except (ValueError, TypeError):
            return 0

    @field_validator("order", mode="before")
    @classmethod
    def parse_order(cls, v: Any) -> int:
        if v is None:
            return 1
        try:
            return max(1, int(v))
        except (ValueError, TypeError):
            return 1


class CourseLessonUpdateRequest(BaseModel):
    section_id: str | None = None
    title: str | None = None
    order: int | None = None
    duration_minutes: int | None = None
    video_provider: str | None = None
    video_id: str | None = None
    library_id: str | None = None
    is_free_preview: bool | None = None
    summary: str | None = None
    notes_markdown: str | None = None
    resources: list[LessonResourceOut] | None = None
    is_published: bool | None = None

    @field_validator("duration_minutes", mode="before")
    @classmethod
    def parse_duration(cls, v: Any) -> int | None:
        if v is None:
            return None
        try:
            return max(0, int(round(float(v))))
        except (ValueError, TypeError):
            return 0

    @field_validator("order", mode="before")
    @classmethod
    def parse_order(cls, v: Any) -> int | None:
        if v is None:
            return None
        try:
            return max(1, int(v))
        except (ValueError, TypeError):
            return 1


class BunnyCreateVideoRequest(BaseModel):
    title: str = Field(default="New Video Lesson", max_length=250)


class BunnyCreateVideoResponse(BaseModel):
    """A video slot, and permission to upload into it — but not the key.

    The browser used to be handed `BUNNY_STREAM_API_KEY`, which can create,
    overwrite and delete every video in the library. It now gets a signature
    that is good for one video and expires, which is what Bunny's presigned
    TUS flow is for.
    """

    video_id: str
    library_id: str
    title: str
    # Bunny's resumable endpoint; the same for every upload.
    tus_endpoint: str = "https://video.bunnycdn.com/tusupload"
    # Sent as the `AuthorizationSignature` and `AuthorizationExpire` headers.
    authorization_signature: str = ""
    authorization_expire: int = 0


# -----------------------------------------------------------------------------
# GURUKUL JIGYASA (TIMESTAMPED Q&A FORUM) SCHEMAS
# -----------------------------------------------------------------------------
class CourseQuestionAnswerOut(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_role: str
    user_avatar: str | None = None
    is_official: bool = False
    content: str
    created_at: datetime


class CourseQuestionOut(BaseModel):
    id: str
    course_id: str
    section_id: str
    lesson_id: str
    user_id: str
    user_name: str
    user_avatar: str | None = None
    timestamp_seconds: int
    timestamp_formatted: str
    title: str
    content: str
    upvote_count: int
    is_upvoted_by_me: bool = False
    answer_count: int
    is_resolved: bool = False
    has_official_answer: bool = False
    is_pinned: bool = False
    answers: list[CourseQuestionAnswerOut] = Field(default_factory=list)
    created_at: datetime


class CourseQuestionCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=300)
    content: str = Field(..., min_length=2, max_length=5000)
    timestamp_seconds: int = Field(default=0, ge=0)


class CourseQuestionAnswerRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class AdminCourseQuestionAnswerRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    mark_resolved: bool = True


class AdminCourseQuestionUpdateRequest(BaseModel):
    is_resolved: bool | None = None
    is_pinned: bool | None = None
    is_hidden: bool | None = None


class AdminCourseQuestionDetailOut(BaseModel):
    id: str
    course_id: str
    course_title: str
    course_slug: str
    section_id: str
    section_title: str
    lesson_id: str
    lesson_title: str
    video_id: str | None = None
    video_provider: str = "bunny_stream"

    # Student metadata
    user_id: str
    user_name: str
    user_email: str | None = None
    user_phone: str | None = None
    user_avatar: str | None = None
    student_enrolled_at: datetime | None = None
    student_progress_percent: float = 0.0

    timestamp_seconds: int
    timestamp_formatted: str
    title: str
    content: str
    upvote_count: int
    answer_count: int
    is_resolved: bool
    has_official_answer: bool
    is_pinned: bool
    is_hidden: bool
    answers: list[CourseQuestionAnswerOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AdminCourseQuestionListResponse(BaseModel):
    questions: list[AdminCourseQuestionDetailOut] = Field(default_factory=list)
    total: int = 0
    unanswered_count: int = 0
    resolved_count: int = 0


class CourseCertificateOut(BaseModel):
    certificate_id: str
    is_valid: bool = True
    student_name: str
    student_email: str | None = None
    course_id: str
    course_title: str
    course_slug: str
    instructor_name: str
    instructor_title: str
    instructor_avatar: str | None = None
    issued_at: datetime
    issued_at_formatted: str
    total_lessons_completed: int
    distinction: str = "Vidya Parangata (Summa Cum Laude • পরম বিদ্বান)"
    verification_url: str
    certificate_html_url: str
    digital_seal: dict[str, Any] = Field(default_factory=dict)
    cryptographic_signature: str = ""
    canonical_hash: str = ""
    signature_algorithm: str = "HMAC-SHA256 (FIPS 198-1 Standard)"
    is_signature_valid: bool = True
    tamper_check: dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# ADMIN COURSE ORDERS & ENROLLMENTS MANAGEMENT SCHEMAS
# -----------------------------------------------------------------------------
class AdminCourseOrderOut(BaseModel):
    id: str
    user_id: str
    student_name: str | None = None
    student_email: str | None = None
    student_phone: str | None = None
    course_id: str
    course_title: str | None = None
    course_slug: str | None = None
    razorpay_order_id: str
    razorpay_payment_id: str | None = None
    receipt: str = ""
    amount_paise: int
    amount_inr: float
    currency: str = "INR"
    status: str
    method: str | None = None
    failure_reason: str | None = None
    verified_via: str | None = None
    paid_at: datetime | None = None
    created_at: datetime


class AdminCourseOrderListResponse(BaseModel):
    items: list[AdminCourseOrderOut] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    limit: int = 25
    pages: int = 1
    created_count: int = 0
    paid_count: int = 0
    failed_count: int = 0
    refunded_count: int = 0


class AdminCourseEnrollmentOut(BaseModel):
    id: str
    user_id: str
    student_name: str | None = None
    student_email: str | None = None
    student_phone: str | None = None
    course_id: str
    course_title: str | None = None
    course_slug: str | None = None
    payment_id: str | None = None
    order_id: str | None = None
    amount_paid: float = 0.0
    currency: str = "INR"
    progress_percent: float = 0.0
    certificate_issued: bool = False
    enrolled_at: datetime
    last_accessed_at: datetime


class AdminCourseEnrollmentListResponse(BaseModel):
    items: list[AdminCourseEnrollmentOut] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    limit: int = 25
    pages: int = 1


class AdminManualEnrollRequest(BaseModel):
    user_id: str | None = None
    email: str | None = None
    amount_paid: float = Field(default=0.0, ge=0)
    payment_id: str | None = Field(default=None, max_length=120)
    note: str | None = Field(default=None, max_length=250)



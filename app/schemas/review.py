"""Review request and response shapes."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReviewKind


class LeaveReviewRequest(BaseModel):
    kind: ReviewKind
    session_id: str
    stars: int = Field(ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)


class ReviewOut(BaseModel):
    """A review as anyone may see it.

    No user id: a review is public, and pairing a name with an account id
    would let anyone build a list of everything one person has consulted
    about.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    astrologer_id: str
    kind: ReviewKind
    stars: int
    text: str | None = None
    author_name: str | None = None
    created_at: datetime


class ReviewSummary(BaseModel):
    """What a profile shows above the list."""

    average: float
    count: int
    # How many gave each star count, five down to one.
    breakdown: dict[int, int]


class ReviewPage(BaseModel):
    items: list[ReviewOut]
    total: int
    summary: ReviewSummary


class PendingReview(BaseModel):
    """A finished consultation this user has not reviewed yet."""

    kind: ReviewKind
    session_id: str
    astrologer_id: str
    astrologer_name: str
    astrologer_avatar_url: str | None = None
    label: str


class HideReviewRequest(BaseModel):
    hidden: bool = True
    reason: str | None = Field(default=None, max_length=300)

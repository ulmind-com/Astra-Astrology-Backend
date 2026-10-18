"""An astrologer's professional profile.

Accounts are created by an admin, never by the astrologer — so this document is
always created alongside a `User` whose role is `astrologer`, and the two are
linked by `user_id`.
"""

from datetime import datetime

import pymongo
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.models.base import TimestampedDocument
from app.models.enums import ConsultationMode, Skill


class GalleryImage(BaseModel):
    """A gallery picture. The public_id is kept so it can be deleted again."""

    url: str
    public_id: str


class Availability(BaseModel):
    """Whether this astrologer can be consulted right now.

    `is_online` is not trusted on its own. It says the astrologer meant to be
    available; `last_seen_at` says their panel was actually open recently. A
    browser that is closed, crashes, or loses its connection stops sending the
    heartbeat and no longer reports anything — so without the second field an
    astrologer would stay "online" forever after closing the tab, and users
    would queue for someone who is not there.

    Both fields are always read together through `app.services.presence`.
    """

    is_online: bool = False
    is_available_for_chat: bool = True
    is_available_for_call: bool = True
    is_available_for_video: bool = True
    is_busy: bool = False
    last_online_at: datetime | None = None

    # Stamped by every heartbeat from an open panel. None means they have not
    # been seen since this field was introduced, which counts as offline.
    last_seen_at: datetime | None = None


class RateCard(BaseModel):
    """What this astrologer charges, in **coins per started minute**.

    Coins rather than rupees because that is what a wallet holds. Storing
    rupees and converting at the coin rate would mean an admin changing
    `coins_per_rupee` silently re-priced every astrologer on the platform.

    `None` means "whatever the platform charges" — so a new astrologer needs no
    pricing decision to go live, and changing the default moves everyone who
    has not been priced individually.
    """

    chat_coins_per_minute: int | None = Field(default=None, ge=1, le=100_000)
    call_coins_per_minute: int | None = Field(default=None, ge=1, le=100_000)
    video_coins_per_minute: int | None = Field(default=None, ge=1, le=100_000)


class RatingSummary(BaseModel):
    average: float = Field(default=0.0, ge=0, le=5)
    count: int = Field(default=0, ge=0)


class BankDetails(BaseModel):
    account_holder_name: str | None = None
    account_number_last4: str | None = Field(default=None, max_length=4)
    ifsc: str | None = Field(default=None, max_length=20)
    bank_name: str | None = Field(default=None, max_length=120)
    upi_id: str | None = Field(default=None, max_length=120)


class Astrologer(TimestampedDocument):
    user_id: PydanticObjectId

    # ------------------------------------------------------------- listing
    display_name: str = Field(max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    tagline: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=5000)
    profile_image_url: str | None = None
    profile_image_public_id: str | None = None
    gallery: list[GalleryImage] = Field(default_factory=list)
    intro_video_url: str | None = None

    # ---------------------------------------------------------- competence
    skills: list[Skill] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    specialisations: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    experience_years: int = Field(default=0, ge=0, le=90)

    # ------------------------------------------------------------ commerce
    rates: RateCard = Field(default_factory=RateCard)
    modes_enabled: list[ConsultationMode] = Field(
        default_factory=lambda: [ConsultationMode.CHAT, ConsultationMode.CALL]
    )
    # None means the platform's default. An explicit value is this
    # astrologer's own deal.
    commission_percent: float | None = Field(default=None, ge=0, le=100)
    bank: BankDetails = Field(default_factory=BankDetails)

    # ------------------------------------------------------------ platform
    availability: Availability = Field(default_factory=Availability)
    rating: RatingSummary = Field(default_factory=RatingSummary)
    total_consultations: int = Field(default=0, ge=0)
    followers_count: int = Field(default=0, ge=0)

    # ------------------------------------------------------------ curation
    is_listed: bool = Field(default=True, description="Shown in the public directory")
    is_featured: bool = False
    display_order: int = 0

    class Settings(TimestampedDocument.Settings):
        name = "astrologers"
        indexes = [
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING)], name="astrologer_user_unique", unique=True
            ),
            pymongo.IndexModel(
                [("slug", pymongo.ASCENDING)],
                name="astrologer_slug_unique",
                unique=True,
                partialFilterExpression={"slug": {"$type": "string"}},
            ),
            [("is_listed", pymongo.DESCENDING), ("display_order", pymongo.ASCENDING)],
            [("skills", pymongo.ASCENDING)],
            [("languages", pymongo.ASCENDING)],
        ]

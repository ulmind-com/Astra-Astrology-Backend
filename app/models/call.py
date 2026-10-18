"""A one-to-one call between a user and an astrologer.

This document — not the ZEGOCLOUD room — is the record of what happened. The
room is only the pipe the audio and video travel through: ZEGOCLOUD knows
nothing about who may call whom, when a call really began, or what it is worth.
So the server decides all of that, and the room is created to match.

Billing is deliberately not here yet.
"""

from datetime import datetime

import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from app.models.base import TimestampedDocument
from app.models.enums import CallParty, CallStatus, ConsultationMode


class CallSession(TimestampedDocument):
    user_id: PydanticObjectId
    # Both ids are kept: the profile is what the user picked, the account is
    # what signs the astrologer's requests.
    astrologer_id: PydanticObjectId
    astrologer_user_id: PydanticObjectId

    mode: ConsultationMode = ConsultationMode.VIDEO
    # The ZEGOCLOUD room. Unique, and never reused — a fresh room per call
    # means a stale token can never open an old conversation.
    room_id: str

    status: CallStatus = CallStatus.RINGING

    # When the astrologer accepted, which is when the call really starts. Not
    # when it was dialled: nobody should be charged for ringing.
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int = 0

    ended_by: CallParty | None = None
    end_reason: str | None = None

    # Both sides send these while they are in the room. When they stop, the
    # sweeper closes the call — otherwise a crashed tab leaves it open forever.
    user_seen_at: datetime | None = None
    astrologer_seen_at: datetime | None = None

    # --- price, frozen when the session starts ---------------------------
    # An admin re-pricing mid-session must not change a session in progress,
    # and a later change to the coin rate must not restate what was earned.
    coins_per_minute: int = Field(default=0, ge=0)
    commission_percent: float = Field(default=0.0, ge=0, le=100)
    coin_value_paise: int = Field(default=0, ge=0)

    # What the user booked. A hard cap: the session ends here even if the
    # wallet could carry on.
    requested_minutes: int = Field(default=0, ge=0)

    # --- what has actually been taken ------------------------------------
    minutes_charged: int = Field(default=0, ge=0)
    coins_charged: int = Field(default=0, ge=0)
    earning_paise: int = Field(default=0, ge=0)

    class Settings:
        name = "call_sessions"
        indexes = [
            pymongo.IndexModel(
                [("room_id", pymongo.ASCENDING)], name="call_room_unique", unique=True
            ),
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="call_user_recent",
            ),
            pymongo.IndexModel(
                [("astrologer_user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="call_astrologer_recent",
            ),
            # The sweeper's query, and the "is anyone already on a call" check.
            pymongo.IndexModel([("status", pymongo.ASCENDING)], name="call_status"),
        ]


class ZegoCallbackEvent(TimestampedDocument):
    """Replay guard for ZEGOCLOUD's room callbacks, which are retried."""

    event_key: str
    event: str
    payload: dict = Field(default_factory=dict)
    result: str | None = None

    class Settings:
        name = "zego_callback_events"
        indexes = [
            pymongo.IndexModel(
                [("event_key", pymongo.ASCENDING)], name="zego_event_unique", unique=True
            ),
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)], name="zego_event_recent"),
        ]

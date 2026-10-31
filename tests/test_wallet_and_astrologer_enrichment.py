"""Tests for enriched wallet activities, astrologer earnings, and astrologer review feedback."""

import pytest
from beanie import PydanticObjectId
from httpx import AsyncClient

from app.api.v1.wallet import enrich_consultations, to_transaction
from app.models.astrologer import Astrologer
from app.models.call import CallSession
from app.models.chat import ChatSession
from app.models.earning import EarningEntry
from app.models.enums import (
    CallStatus,
    ChatStatus,
    ConsultationMode,
    TransactionDirection,
    TransactionReason,
)
from app.models.wallet import TransactionRef, WalletTransaction

pytestmark = pytest.mark.usefixtures("fake_firebase")


@pytest.mark.asyncio
async def test_enrich_consultations_chat_call_appointment(client: AsyncClient):
    # Setup test astrologer
    astro_user_id = PydanticObjectId()
    astro = Astrologer(
        user_id=astro_user_id,
        display_name="Dr. Jyotish Sharma",
        profile_image_url="https://example.com/avatar.jpg",
    )
    await astro.insert()

    # Setup chat session
    chat = ChatSession(
        user_id=PydanticObjectId(),
        astrologer_id=astro.id,
        astrologer_user_id=astro_user_id,
        user_uid="uid1",
        astrologer_uid="uid2",
        conversation_id="conv1",
        status=ChatStatus.ENDED,
        duration_seconds=300,
    )
    await chat.insert()

    # Setup call session
    call = CallSession(
        user_id=PydanticObjectId(),
        astrologer_id=astro.id,
        astrologer_user_id=astro_user_id,
        mode=ConsultationMode.VIDEO,
        room_id="room1",
        status=CallStatus.ENDED,
        duration_seconds=420,
    )
    await call.insert()

    # Setup transactions
    txn1 = WalletTransaction(
        wallet_id=PydanticObjectId(),
        user_id=PydanticObjectId(),
        direction=TransactionDirection.DEBIT,
        reason=TransactionReason.CONSULTATION,
        amount_coins=100,
        balance_after_coins=900,
        idempotency_key="test:txn:1",
        ref=TransactionRef(session_id=chat.id),
        note="chat · minute 1",
    )
    txn2 = WalletTransaction(
        wallet_id=PydanticObjectId(),
        user_id=PydanticObjectId(),
        direction=TransactionDirection.DEBIT,
        reason=TransactionReason.CONSULTATION,
        amount_coins=150,
        balance_after_coins=750,
        idempotency_key="test:txn:2",
        ref=TransactionRef(session_id=call.id),
        note="video · minute 1",
    )

    enriched = await enrich_consultations([txn1, txn2])
    assert str(chat.id) in enriched
    assert str(call.id) in enriched

    chat_meta = enriched[str(chat.id)]
    assert chat_meta.astrologer_name == "Dr. Jyotish Sharma"
    assert chat_meta.astrologer_avatar == "https://example.com/avatar.jpg"
    assert chat_meta.mode == "chat"
    assert chat_meta.duration_seconds == 300

    call_meta = enriched[str(call.id)]
    assert call_meta.astrologer_name == "Dr. Jyotish Sharma"
    assert call_meta.mode == "video"
    assert call_meta.duration_seconds == 420

    t_out1 = to_transaction(txn1, enriched)
    assert t_out1.consultation is not None
    assert t_out1.consultation.astrologer_name == "Dr. Jyotish Sharma"
    assert "Dr. Jyotish Sharma" in (t_out1.note or "")


@pytest.mark.asyncio
async def test_earning_entry_user_aggregation(client: AsyncClient):
    from app.services import earnings as earnings_service

    astro_user_id = PydanticObjectId()
    client_user_id = PydanticObjectId()
    session_id = PydanticObjectId()

    await EarningEntry(
        astrologer_id=PydanticObjectId(),
        astrologer_user_id=astro_user_id,
        user_id=client_user_id,
        mode=ConsultationMode.CALL,
        session_id=session_id,
        minute_index=1,
        coins_charged=20,
        gross_paise=2000,
        commission_percent=20.0,
        commission_paise=400,
        earning_paise=1600,
    ).insert()

    await EarningEntry(
        astrologer_id=PydanticObjectId(),
        astrologer_user_id=astro_user_id,
        user_id=client_user_id,
        mode=ConsultationMode.CALL,
        session_id=session_id,
        minute_index=2,
        coins_charged=20,
        gross_paise=2000,
        commission_percent=20.0,
        commission_paise=400,
        earning_paise=1600,
    ).insert()

    recent = await earnings_service.recent_for_astrologer(astro_user_id)
    assert len(recent) == 1
    session_row = recent[0]
    assert session_row["_id"] == session_id
    assert session_row["user_id"] == client_user_id
    assert session_row["minutes"] == 2
    assert session_row["coins_charged"] == 40
    assert session_row["earning_paise"] == 3200


@pytest.mark.asyncio
async def test_dynamic_realtime_service_duration_tracking():
    from types import SimpleNamespace
    from app.models.astrologer import ServiceDuration
    from app.services.astrologer import _format_service_duration

    astro = SimpleNamespace(service_duration=None, experience_years=10)

    # 1. Brand new astrologer: MUST NOT have fake 1440 hours!
    sd_init = _format_service_duration(astro)
    assert sd_init.chat_minutes == 0
    assert sd_init.call_minutes == 0
    assert sd_init.video_minutes == 0
    assert sd_init.total_minutes == 0
    assert sd_init.total_hours == 0
    assert sd_init.formatted_total == "0 mins"

    # 2. User chats with astrologer for 5 minutes
    astro.service_duration = ServiceDuration(chat_minutes=5, call_minutes=0, video_minutes=0)
    sd_chat = _format_service_duration(astro)
    assert sd_chat.chat_minutes == 5
    assert sd_chat.call_minutes == 0
    assert sd_chat.video_minutes == 0
    assert sd_chat.total_minutes == 5
    assert sd_chat.formatted_chat == "5 mins"

    # 3. Another user calls astrologer for 12 minutes
    astro.service_duration.call_minutes += 12
    sd_call = _format_service_duration(astro)
    assert sd_call.chat_minutes == 5
    assert sd_call.call_minutes == 12
    assert sd_call.video_minutes == 0
    assert sd_call.total_minutes == 17
    assert sd_call.formatted_total == "17 mins"

    # 4. Another user does a video call for 30 minutes
    astro.service_duration.video_minutes += 30
    sd_video = _format_service_duration(astro)
    assert sd_video.chat_minutes == 5
    assert sd_video.call_minutes == 12
    assert sd_video.video_minutes == 30
    assert sd_video.total_minutes == 47
    assert sd_video.formatted_total == "47 mins"


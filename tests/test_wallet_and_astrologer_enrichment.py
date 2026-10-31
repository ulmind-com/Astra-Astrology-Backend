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

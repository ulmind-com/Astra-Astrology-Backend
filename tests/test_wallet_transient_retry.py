"""Tests for wallet transaction retry under transient WriteConflict errors."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from pymongo.errors import OperationFailure

from app.models.enums import TransactionDirection, TransactionReason
from app.services import wallet as wallet_service
from app.services.wallet import _is_transient


def test_is_transient_detection():
    # Test 1: has_error_label returning True
    exc1 = OperationFailure("Write conflict error")
    exc1._error_labels = {"TransientTransactionError"}
    assert _is_transient(exc1) is True

    # Test 2: details dictionary code 112
    exc2 = OperationFailure("Write conflict during plan execution", details={"code": 112, "codeName": "WriteConflict"})
    assert _is_transient(exc2) is True

    # Test 3: details errorLabels
    exc3 = OperationFailure("Some error", details={"errorLabels": ["TransientTransactionError"]})
    assert _is_transient(exc3) is True

    # Test 4: string fallback
    exc4 = Exception("Caused by :: Write conflict during plan execution and yielding is disabled.")
    assert _is_transient(exc4) is True

    # Test 5: non-transient error
    exc5 = OperationFailure("Document not found", details={"code": 2})
    assert _is_transient(exc5) is False


@pytest.mark.asyncio
async def test_wallet_move_retries_on_write_conflict(monkeypatch):
    """Verifies that _move catches WriteConflict, sleeps, and succeeds on subsequent attempt."""
    user_id = ObjectId()
    fake_wallet = MagicMock()
    fake_wallet.id = ObjectId()
    fake_wallet.is_frozen = False
    fake_wallet.balance_coins = 1000
    fake_wallet.blocked_coins = 0

    monkeypatch.setattr(wallet_service, "_existing_transaction", AsyncMock(return_value=None))
    monkeypatch.setattr(wallet_service, "get_or_create_wallet", AsyncMock(return_value=fake_wallet))
    
    # Mock realtime publish
    from app.services import realtime
    monkeypatch.setattr(realtime, "publish_wallet_for_user", AsyncMock())

    attempts = 0

    class FakeSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class FakeTxnContext:
        async def __aenter__(self):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                # Simulate MongoDB WriteConflict on attempt 1
                raise OperationFailure(
                    "Caused by :: Write conflict during plan execution and yielding is disabled.",
                    details={"code": 112, "codeName": "WriteConflict", "errorLabels": ["TransientTransactionError"]}
                )
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class FakeClient:
        def start_session(self):
            session = FakeSession()
            session.start_transaction = AsyncMock(return_value=FakeTxnContext())
            return session

    monkeypatch.setattr(wallet_service, "get_client", lambda: FakeClient())

    # Mock Wallet.get
    monkeypatch.setattr(wallet_service.Wallet, "get", AsyncMock(return_value=fake_wallet))
    
    fake_txn = MagicMock()
    fake_txn.balance_after_coins = 990
    fake_txn.insert = AsyncMock()

    # Mock WalletTransaction constructor to avoid Beanie uninitialized error in unit test
    monkeypatch.setattr(wallet_service, "WalletTransaction", MagicMock(return_value=fake_txn))

    with patch.object(wallet_service.Wallet, "get_pymongo_collection") as mock_col, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        
        mock_collection = MagicMock()
        mock_collection.update_one = AsyncMock()
        mock_col.return_value = mock_collection

        txn, newly_created = await wallet_service._move(
            user_id=user_id,
            direction=TransactionDirection.DEBIT,
            reason=TransactionReason.CONSULTATION,
            amount_coins=10,
            idempotency_key="test_conflict_retry_key",
        )

        assert newly_created is True
        assert attempts == 2  # Failed once, retried and succeeded on attempt 2!
        assert mock_sleep.await_count == 1  # Verified exponential backoff sleep was called!
        assert fake_txn.insert.await_count == 1


@pytest.mark.asyncio
async def test_wallet_move_exhausts_attempts_raises_conflict(monkeypatch):
    """Verifies that if WriteConflict persists across all 6 attempts, it raises ConflictError."""
    user_id = ObjectId()
    fake_wallet = MagicMock()
    fake_wallet.id = ObjectId()
    fake_wallet.is_frozen = False
    fake_wallet.balance_coins = 1000
    fake_wallet.blocked_coins = 0

    monkeypatch.setattr(wallet_service, "_existing_transaction", AsyncMock(return_value=None))
    monkeypatch.setattr(wallet_service, "get_or_create_wallet", AsyncMock(return_value=fake_wallet))

    attempts = 0

    class FakeSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class FakeTxnContext:
        async def __aenter__(self):
            nonlocal attempts
            attempts += 1
            raise OperationFailure(
                "Caused by :: Write conflict during plan execution and yielding is disabled.",
                details={"code": 112, "codeName": "WriteConflict", "errorLabels": ["TransientTransactionError"]}
            )

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class FakeClient:
        def start_session(self):
            session = FakeSession()
            session.start_transaction = AsyncMock(return_value=FakeTxnContext())
            return session

    monkeypatch.setattr(wallet_service, "get_client", lambda: FakeClient())

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(wallet_service.ConflictError) as exc_info:
            await wallet_service._move(
                user_id=user_id,
                direction=TransactionDirection.DEBIT,
                reason=TransactionReason.CONSULTATION,
                amount_coins=10,
                idempotency_key="test_exhaust_attempts_key",
            )
        assert attempts == 6
        assert mock_sleep.await_count == 5  # Retried 5 times before failing on 6th
        assert exc_info.value.error_code == "wallet_busy"


@pytest.mark.asyncio
async def test_capture_held_coins_atomic(monkeypatch):
    """Verifies capture_held_coins passes unblock_coins to debit for single atomic transaction."""
    user_id = ObjectId()
    appointment_id = ObjectId()

    mock_debit = AsyncMock()
    monkeypatch.setattr(wallet_service, "debit", mock_debit)

    await wallet_service.capture_held_coins(
        user_id=user_id,
        amount_coins=150,
        appointment_id=appointment_id,
        note="Appointment completed",
    )

    mock_debit.assert_awaited_once_with(
        user_id=user_id,
        amount_coins=150,
        unblock_coins=150,
        reason=TransactionReason.APPOINTMENT_BALANCE,
        idempotency_key=f"appointment:{appointment_id}:capture_balance",
        ref=wallet_service.TransactionRef(session_id=appointment_id),
        note="Appointment completed",
    )



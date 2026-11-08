"""Wallet movements.

The wallet's unit is **coins**, not money — see `docs/COINS-PLAN.md`. A recharge
row also carries the rupees that were paid and the rate honoured, so history can
still be read in money years after the rate has changed.

Every credit and debit goes through `_move`, which does two things in one
MongoDB transaction: it writes the ledger row and it updates the cached
balance. Doing only one of the two is what makes a wallet untrustworthy, so
they are never allowed to happen separately.

Double-spend protection is the unique index on
`WalletTransaction.idempotency_key` — not a check-then-write, which two
concurrent requests can both pass. The insert itself is the lock.
"""

import asyncio
import random
from datetime import UTC, datetime

from beanie import PydanticObjectId
from loguru import logger
from pymongo.errors import DuplicateKeyError, OperationFailure, PyMongoError

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.db.mongodb import get_client
from app.models.enums import TransactionDirection, TransactionReason
from app.models.wallet import TransactionRef, Wallet, WalletTransaction

# A transaction that touches a document another transaction is writing aborts
# with a transient error (e.g. WriteConflict code 112). MongoDB guidance is to
# retry the transaction with exponential backoff and randomized jitter to
# eliminate retry collisions and allow the competing transaction to commit.
_MAX_TRANSACTION_ATTEMPTS = 6


async def get_or_create_wallet(user_id: PydanticObjectId) -> Wallet:
    """Returns the user's wallet, opening one the first time it is needed."""
    wallet = await Wallet.find_one(Wallet.user_id == user_id)
    if wallet is not None:
        return wallet

    wallet = Wallet(user_id=user_id)
    try:
        await wallet.insert()
    except DuplicateKeyError:
        # Two requests opened the wallet at once; the unique index settled it.
        wallet = await Wallet.find_one(Wallet.user_id == user_id)
        if wallet is None:  # pragma: no cover - the index guarantees one exists
            raise
    return wallet


async def _existing_transaction(idempotency_key: str) -> WalletTransaction | None:
    return await WalletTransaction.find_one(
        WalletTransaction.idempotency_key == idempotency_key
    )


def _is_transient(exc: Exception) -> bool:
    """Detects whether a PyMongo error is a transient transaction error or write conflict."""
    # PyMongo standard helper method on OperationFailure / PyMongoError
    if hasattr(exc, "has_error_label"):
        try:
            if exc.has_error_label("TransientTransactionError") or exc.has_error_label("UnknownTransactionCommitResult"):
                return True
        except Exception:
            pass

    # Direct attribute checks
    labels = getattr(exc, "_error_labels", None) or getattr(exc, "error_labels", None)
    if labels and any(lbl in labels for lbl in ("TransientTransactionError", "UnknownTransactionCommitResult")):
        return True

    # Details dictionary checks
    details = getattr(exc, "details", None)
    if isinstance(details, dict):
        det_labels = details.get("errorLabels") or []
        if any(lbl in det_labels for lbl in ("TransientTransactionError", "UnknownTransactionCommitResult")):
            return True
        if details.get("code") == 112 or details.get("codeName") == "WriteConflict":
            return True

    # Direct code check (112 = WriteConflict in MongoDB WiredTiger)
    if getattr(exc, "code", None) == 112:
        return True

    # String inspection fallback for wrapped or stringified exceptions
    msg = str(exc)
    if "Write conflict" in msg or "WriteConflict" in msg or "TransientTransactionError" in msg:
        return True

    return False


async def _move(
    *,
    user_id: PydanticObjectId,
    direction: TransactionDirection,
    reason: TransactionReason,
    amount_coins: int,
    idempotency_key: str,
    ref: TransactionRef | None = None,
    note: str | None = None,
    created_by: PydanticObjectId | None = None,
    allow_when_frozen: bool = False,
    amount_paise: int | None = None,
    coins_per_rupee: int | None = None,
    unblock_coins: int = 0,
) -> tuple[WalletTransaction, bool]:
    """Moves coins. Returns (transaction, was_newly_created).

    Calling this twice with the same `idempotency_key` is safe and returns the
    first transaction — that is what lets the browser callback and the webhook
    both report the same payment without crediting it twice.
    """
    if amount_coins <= 0:
        raise BadRequestError("Amount must be greater than zero.", error_code="invalid_amount")

    # Cheap pre-check. It does not replace the unique index — it just avoids
    # opening a transaction for a payment that has obviously already landed.
    already = await _existing_transaction(idempotency_key)
    if already is not None:
        return already, False

    # Opened before the transaction starts on purpose: a document created after
    # a transaction begins is not visible inside its snapshot.
    opened = await get_or_create_wallet(user_id)
    assert opened.id is not None

    client = get_client()

    for attempt in range(1, _MAX_TRANSACTION_ATTEMPTS + 1):
        try:
            async with client.start_session() as session:
                # pymongo's async start_transaction is a coroutine that returns
                # the context manager, so it has to be awaited first.
                async with await session.start_transaction():
                    wallet = await Wallet.get(opened.id, session=session)
                    assert wallet is not None and wallet.id is not None

                    if wallet.is_frozen and not allow_when_frozen:
                        raise ForbiddenError(
                            "This wallet is frozen. Please contact support.",
                            error_code="wallet_frozen",
                        )

                    current_blocked = getattr(wallet, "blocked_coins", 0) or 0
                    new_blocked = current_blocked
                    if direction is TransactionDirection.CREDIT:
                        new_balance = wallet.balance_coins + amount_coins
                    else:
                        if unblock_coins > 0:
                            new_blocked = max(0, current_blocked - unblock_coins)
                        available = max(0, wallet.balance_coins - new_blocked)
                        if available < amount_coins:
                            raise BadRequestError(
                                "Not enough spendable coins. Some coins are reserved for your scheduled appointments. Please recharge.",
                                error_code="insufficient_balance",
                                details={
                                    "balance_coins": wallet.balance_coins,
                                    "blocked_coins": new_blocked,
                                    "available_coins": available,
                                    "required_coins": amount_coins,
                                },
                            )
                        new_balance = wallet.balance_coins - amount_coins

                    now = datetime.now(UTC)
                    txn = WalletTransaction(
                        wallet_id=wallet.id,
                        user_id=user_id,
                        direction=direction,
                        reason=reason,
                        amount_coins=amount_coins,
                        balance_after_coins=new_balance,
                        amount_paise=amount_paise,
                        coins_per_rupee=coins_per_rupee,
                        idempotency_key=idempotency_key,
                        ref=ref or TransactionRef(),
                        note=note,
                        created_by=created_by,
                    )
                    # First, because the unique index on idempotency_key is what
                    # makes a second credit impossible rather than unlikely.
                    await txn.insert(session=session)

                    set_fields: dict[str, object] = {
                        "balance_coins": new_balance,
                        "last_transaction_at": now,
                        "updated_at": now,
                    }
                    if unblock_coins > 0:
                        set_fields["blocked_coins"] = new_blocked

                    await Wallet.get_pymongo_collection().update_one(
                        {"_id": wallet.id},
                        {"$set": set_fields},
                        session=session,
                    )

            logger.info(
                "Wallet {} {} {} coins ({}) -> balance {}",
                user_id,
                direction.value,
                amount_coins,
                reason.value,
                txn.balance_after_coins,
            )

            # Published after the transaction has committed, never inside it:
            # a mirror written from an aborted transaction would show coins
            # that no longer exist. It cannot raise — see services.realtime.
            from app.services import realtime

            await realtime.publish_wallet_for_user(user_id, txn.balance_after_coins)

            return txn, True

        except DuplicateKeyError:
            # The other path got there first. That is a success, not a failure.
            existing = await _existing_transaction(idempotency_key)
            if existing is None:  # pragma: no cover - the index guarantees one
                raise
            logger.info("Wallet movement {} was already applied.", idempotency_key)
            return existing, False

        except (OperationFailure, PyMongoError) as exc:
            if _is_transient(exc):
                if attempt < _MAX_TRANSACTION_ATTEMPTS:
                    delay = min(0.6, (0.05 * (2 ** (attempt - 1))) + random.uniform(0.02, 0.08))
                    logger.warning(
                        "Wallet transaction conflict for {} (attempt {}/{}), retrying in {:.3f}s: {}",
                        user_id,
                        attempt,
                        _MAX_TRANSACTION_ATTEMPTS,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(
                        "Wallet transaction conflict for {} exhausted all {} attempts: {}",
                        user_id,
                        _MAX_TRANSACTION_ATTEMPTS,
                        exc,
                    )
                    raise ConflictError(
                        "Could not complete the wallet update due to high concurrency. Please try again.",
                        error_code="wallet_busy",
                    ) from exc
            raise

    raise ConflictError(  # pragma: no cover - loop always returns or raises
        "Could not complete the wallet update. Please try again.",
        error_code="wallet_busy",
    )


async def credit(
    *,
    user_id: PydanticObjectId,
    amount_coins: int,
    reason: TransactionReason,
    idempotency_key: str,
    ref: TransactionRef | None = None,
    note: str | None = None,
    created_by: PydanticObjectId | None = None,
    allow_when_frozen: bool = False,
    amount_paise: int | None = None,
    coins_per_rupee: int | None = None,
) -> tuple[WalletTransaction, bool]:
    return await _move(
        user_id=user_id,
        direction=TransactionDirection.CREDIT,
        reason=reason,
        amount_coins=amount_coins,
        idempotency_key=idempotency_key,
        ref=ref,
        note=note,
        created_by=created_by,
        allow_when_frozen=allow_when_frozen,
        amount_paise=amount_paise,
        coins_per_rupee=coins_per_rupee,
    )


async def debit(
    *,
    user_id: PydanticObjectId,
    amount_coins: int,
    reason: TransactionReason,
    idempotency_key: str,
    ref: TransactionRef | None = None,
    note: str | None = None,
    created_by: PydanticObjectId | None = None,
    allow_when_frozen: bool = False,
    amount_paise: int | None = None,
    coins_per_rupee: int | None = None,
    unblock_coins: int = 0,
) -> tuple[WalletTransaction, bool]:
    return await _move(
        user_id=user_id,
        direction=TransactionDirection.DEBIT,
        reason=reason,
        amount_coins=amount_coins,
        idempotency_key=idempotency_key,
        ref=ref,
        note=note,
        created_by=created_by,
        allow_when_frozen=allow_when_frozen,
        amount_paise=amount_paise,
        coins_per_rupee=coins_per_rupee,
        unblock_coins=unblock_coins,
    )


async def list_transactions(
    user_id: PydanticObjectId,
    *,
    page: int = 1,
    limit: int = 20,
    reason: TransactionReason | None = None,
) -> tuple[list[WalletTransaction], int]:
    query = WalletTransaction.find(WalletTransaction.user_id == user_id)
    if reason is not None:
        query = query.find(WalletTransaction.reason == reason)

    total = await query.count()
    items = (
        await query.sort(-WalletTransaction.created_at)
        .skip((page - 1) * limit)
        .limit(limit)
        .to_list()
    )
    return items, total


async def recalculate_balance(user_id: PydanticObjectId) -> dict[str, int]:
    """Rebuilds the balance from the ledger.

    The ledger is the truth, so this is both the repair tool and the proof that
    the cached balance is still right.
    """
    wallet = await get_or_create_wallet(user_id)

    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": "$direction",
                "total": {"$sum": "$amount_coins"},
            }
        },
    ]
    cursor = await WalletTransaction.get_pymongo_collection().aggregate(pipeline)
    sums = {row["_id"]: row["total"] async for row in cursor}
    credited = sums.get(TransactionDirection.CREDIT.value, 0)
    debited = sums.get(TransactionDirection.DEBIT.value, 0)
    ledger_balance = credited - debited

    drift = ledger_balance - wallet.balance_coins
    if drift != 0:
        logger.error(
            "Wallet {} drifted from its ledger by {} coins — repairing to {}.",
            user_id,
            drift,
            ledger_balance,
        )
        wallet.balance_coins = ledger_balance
        await wallet.save()

    return {
        "credited_coins": credited,
        "debited_coins": debited,
        "ledger_balance_coins": ledger_balance,
        "drift_coins": drift,
    }


async def set_frozen(
    user_id: PydanticObjectId, *, frozen: bool, reason: str | None = None
) -> Wallet:
    wallet = await get_or_create_wallet(user_id)
    wallet.is_frozen = frozen
    wallet.frozen_reason = reason if frozen else None
    await wallet.save()
    logger.warning("Wallet {} {}.", user_id, "frozen" if frozen else "unfrozen")
    return wallet


async def require_wallet(user_id: PydanticObjectId) -> Wallet:
    wallet = await Wallet.find_one(Wallet.user_id == user_id)
    if wallet is None:
        raise NotFoundError("Wallet not found.", error_code="wallet_not_found")
    return wallet


async def hold_coins(
    *,
    user_id: PydanticObjectId,
    amount_coins: int,
    appointment_id: PydanticObjectId,
    note: str | None = None,
) -> int:
    """Blocks/reserves coins in user's wallet for a pending appointment."""
    if amount_coins <= 0:
        return 0
    wallet = await get_or_create_wallet(user_id)
    available = max(0, wallet.balance_coins - getattr(wallet, "blocked_coins", 0))
    if available < amount_coins:
        raise BadRequestError(
            f"Not enough coins to reserve session. Need {amount_coins} coins, available {available}.",
            error_code="insufficient_balance",
            details={"available_coins": available, "required_coins": amount_coins},
        )
    now = datetime.now(UTC)
    new_blocked = getattr(wallet, "blocked_coins", 0) + amount_coins
    await Wallet.get_pymongo_collection().update_one(
        {"_id": wallet.id},
        {"$set": {"blocked_coins": new_blocked, "updated_at": now}},
    )
    logger.info(
        "Wallet {} held {} coins for appointment {} -> total blocked {}",
        user_id,
        amount_coins,
        appointment_id,
        new_blocked,
    )
    return new_blocked


async def release_held_coins(
    *,
    user_id: PydanticObjectId,
    amount_coins: int,
    appointment_id: PydanticObjectId,
    note: str | None = None,
) -> int:
    """Releases previously blocked coins back to user's available balance."""
    if amount_coins <= 0:
        return 0
    wallet = await get_or_create_wallet(user_id)
    now = datetime.now(UTC)
    new_blocked = max(0, getattr(wallet, "blocked_coins", 0) - amount_coins)
    await Wallet.get_pymongo_collection().update_one(
        {"_id": wallet.id},
        {"$set": {"blocked_coins": new_blocked, "updated_at": now}},
    )
    logger.info(
        "Wallet {} released {} held coins for appointment {} -> total blocked {}",
        user_id,
        amount_coins,
        appointment_id,
        new_blocked,
    )
    return new_blocked


async def capture_held_coins(
    *,
    user_id: PydanticObjectId,
    amount_coins: int,
    appointment_id: PydanticObjectId,
    astrologer_user_id: PydanticObjectId | None = None,
    note: str | None = None,
) -> None:
    """Captures held coins on appointment completion: debits balance and unblocks atomically."""
    if amount_coins <= 0:
        return
    await debit(
        user_id=user_id,
        amount_coins=amount_coins,
        unblock_coins=amount_coins,
        reason=TransactionReason.APPOINTMENT_BALANCE,
        idempotency_key=f"appointment:{appointment_id}:capture_balance",
        ref=TransactionRef(session_id=appointment_id),
        note=note or "Consultation session balance completed",
    )
    logger.info("Wallet {} captured {} held coins for appointment {}", user_id, amount_coins, appointment_id)

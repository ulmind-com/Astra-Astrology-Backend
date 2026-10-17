"""Wallet movements.

Every credit and debit goes through `_move`, which does two things in one
MongoDB transaction: it writes the ledger row and it updates the cached
balance. Doing only one of the two is what makes a wallet untrustworthy, so
they are never allowed to happen separately.

Double-spend protection is the unique index on
`WalletTransaction.idempotency_key` — not a check-then-write, which two
concurrent requests can both pass. The insert itself is the lock.
"""

from datetime import UTC, datetime

from beanie import PydanticObjectId
from loguru import logger
from pymongo.errors import DuplicateKeyError, OperationFailure

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.db.mongodb import get_client
from app.models.enums import TransactionDirection, TransactionReason
from app.models.wallet import TransactionRef, Wallet, WalletTransaction

# A transaction that touches a document another transaction is writing aborts
# with a transient error; MongoDB's guidance is to retry the whole thing.
_MAX_TRANSACTION_ATTEMPTS = 3


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


def _is_transient(exc: OperationFailure) -> bool:
    labels = getattr(exc, "_error_labels", None) or exc.details.get("errorLabels", [])
    return "TransientTransactionError" in labels


async def _move(
    *,
    user_id: PydanticObjectId,
    direction: TransactionDirection,
    reason: TransactionReason,
    amount_paise: int,
    idempotency_key: str,
    ref: TransactionRef | None = None,
    note: str | None = None,
    created_by: PydanticObjectId | None = None,
    allow_when_frozen: bool = False,
) -> tuple[WalletTransaction, bool]:
    """Moves money. Returns (transaction, was_newly_created).

    Calling this twice with the same `idempotency_key` is safe and returns the
    first transaction — that is what lets the browser callback and the webhook
    both report the same payment without crediting it twice.
    """
    if amount_paise <= 0:
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

                    if direction is TransactionDirection.CREDIT:
                        new_balance = wallet.balance_paise + amount_paise
                    else:
                        if wallet.balance_paise < amount_paise:
                            raise BadRequestError(
                                "Not enough balance. Please recharge and try again.",
                                error_code="insufficient_balance",
                                details={
                                    "balance_paise": wallet.balance_paise,
                                    "required_paise": amount_paise,
                                },
                            )
                        new_balance = wallet.balance_paise - amount_paise

                    now = datetime.now(UTC)
                    txn = WalletTransaction(
                        wallet_id=wallet.id,
                        user_id=user_id,
                        direction=direction,
                        reason=reason,
                        amount_paise=amount_paise,
                        currency=wallet.currency,
                        balance_after_paise=new_balance,
                        idempotency_key=idempotency_key,
                        ref=ref or TransactionRef(),
                        note=note,
                        created_by=created_by,
                    )
                    # First, because the unique index on idempotency_key is what
                    # makes a second credit impossible rather than unlikely.
                    await txn.insert(session=session)

                    await Wallet.get_pymongo_collection().update_one(
                        {"_id": wallet.id},
                        {
                            "$set": {
                                "balance_paise": new_balance,
                                "last_transaction_at": now,
                                "updated_at": now,
                            }
                        },
                        session=session,
                    )

            logger.info(
                "Wallet {} {} {} paise ({}) -> balance {}",
                user_id,
                direction.value,
                amount_paise,
                reason.value,
                txn.balance_after_paise,
            )
            return txn, True

        except DuplicateKeyError:
            # The other path got there first. That is a success, not a failure.
            existing = await _existing_transaction(idempotency_key)
            if existing is None:  # pragma: no cover - the index guarantees one
                raise
            logger.info("Wallet movement {} was already applied.", idempotency_key)
            return existing, False

        except OperationFailure as exc:
            if _is_transient(exc) and attempt < _MAX_TRANSACTION_ATTEMPTS:
                logger.warning(
                    "Wallet transaction conflict for {} (attempt {}), retrying.",
                    user_id,
                    attempt,
                )
                continue
            raise

    raise ConflictError(  # pragma: no cover - loop always returns or raises
        "Could not complete the wallet update. Please try again.",
        error_code="wallet_busy",
    )


async def credit(
    *,
    user_id: PydanticObjectId,
    amount_paise: int,
    reason: TransactionReason,
    idempotency_key: str,
    ref: TransactionRef | None = None,
    note: str | None = None,
    created_by: PydanticObjectId | None = None,
    allow_when_frozen: bool = False,
) -> tuple[WalletTransaction, bool]:
    return await _move(
        user_id=user_id,
        direction=TransactionDirection.CREDIT,
        reason=reason,
        amount_paise=amount_paise,
        idempotency_key=idempotency_key,
        ref=ref,
        note=note,
        created_by=created_by,
        allow_when_frozen=allow_when_frozen,
    )


async def debit(
    *,
    user_id: PydanticObjectId,
    amount_paise: int,
    reason: TransactionReason,
    idempotency_key: str,
    ref: TransactionRef | None = None,
    note: str | None = None,
    created_by: PydanticObjectId | None = None,
    allow_when_frozen: bool = False,
) -> tuple[WalletTransaction, bool]:
    return await _move(
        user_id=user_id,
        direction=TransactionDirection.DEBIT,
        reason=reason,
        amount_paise=amount_paise,
        idempotency_key=idempotency_key,
        ref=ref,
        note=note,
        created_by=created_by,
        allow_when_frozen=allow_when_frozen,
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
                "total": {"$sum": "$amount_paise"},
            }
        },
    ]
    cursor = await WalletTransaction.get_pymongo_collection().aggregate(pipeline)
    sums = {row["_id"]: row["total"] async for row in cursor}
    credited = sums.get(TransactionDirection.CREDIT.value, 0)
    debited = sums.get(TransactionDirection.DEBIT.value, 0)
    ledger_balance = credited - debited

    drift = ledger_balance - wallet.balance_paise
    if drift != 0:
        logger.error(
            "Wallet {} drifted from its ledger by {} paise — repairing to {}.",
            user_id,
            drift,
            ledger_balance,
        )
        wallet.balance_paise = ledger_balance
        await wallet.save()

    return {
        "credited_paise": credited,
        "debited_paise": debited,
        "ledger_balance_paise": ledger_balance,
        "drift_paise": drift,
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

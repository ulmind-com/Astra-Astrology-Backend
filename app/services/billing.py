"""Per-minute billing.

One idea runs through all of it: **a minute is paid for before it is used.**
Charging afterwards would mean handing someone a minute that might turn out to
be unaffordable, and giving one away every single time anyone runs out.

Three things make that safe, and none of them are new here:

* the server's clock decides which minutes have started — a client timer can be
  stopped, and would be;
* the charge for minute *n* carries the key `session:{id}:minute:{n}`, so the
  unique index on the ledger makes charging it twice **impossible** rather than
  unlikely — which matters because both sides heartbeat and the two can land in
  the same instant;
* the price is frozen when the session starts, so an admin re-pricing mid-call
  cannot change the call in progress.
"""

import math
from dataclasses import dataclass
from datetime import UTC, datetime

from beanie import PydanticObjectId
from loguru import logger

from app.core.exceptions import BadRequestError
from app.models.astrologer import Astrologer
from app.models.earning import EarningEntry
from app.models.enums import ConsultationMode, TransactionReason
from app.models.settings import PlatformSettings
from app.models.wallet import TransactionRef
from app.services import settings as settings_service
from app.services import wallet as wallet_service


@dataclass(frozen=True)
class Price:
    """Everything a session needs frozen into it at the moment it starts."""

    coins_per_minute: int
    commission_percent: float
    # What one coin is worth in money, from what users pay for coins. Frozen
    # too, so a later change to the coin rate cannot restate an earning that
    # has already been paid.
    coin_value_paise: int


def _default_rate(platform: PlatformSettings, mode: ConsultationMode) -> int:
    return {
        ConsultationMode.CHAT: platform.default_chat_coins_per_minute,
        ConsultationMode.CALL: platform.default_call_coins_per_minute,
        ConsultationMode.VIDEO: platform.default_video_coins_per_minute,
    }[mode]


def _own_rate(profile: Astrologer, mode: ConsultationMode) -> int | None:
    return {
        ConsultationMode.CHAT: profile.rates.chat_coins_per_minute,
        ConsultationMode.CALL: profile.rates.call_coins_per_minute,
        ConsultationMode.VIDEO: profile.rates.video_coins_per_minute,
    }[mode]


def coin_value_paise(coins_per_rupee: int) -> int:
    """What one coin is worth, in paise.

    A coin is worth what people pay for it: at 5 coins per rupee, 20 paise.
    Integer division on purpose — the fraction it drops is at most a paisa per
    coin, and rounding up would pay out more than was ever taken in.
    """
    return 100 // max(coins_per_rupee, 1)


async def price_for(profile: Astrologer, mode: ConsultationMode) -> Price:
    """This astrologer's price for this kind of session, right now."""
    platform = await settings_service.get_settings()

    rate = _own_rate(profile, mode) or _default_rate(platform, mode)
    commission = (
        profile.commission_percent
        if profile.commission_percent is not None
        else platform.default_commission_percent
    )
    return Price(
        coins_per_minute=rate,
        commission_percent=commission,
        coin_value_paise=coin_value_paise(platform.coins_per_rupee),
    )


def affordable_minutes(balance_coins: int, coins_per_minute: int) -> int:
    """How many whole minutes this balance covers."""
    if coins_per_minute <= 0:
        return 0
    return balance_coins // coins_per_minute


async def check_can_start(
    *,
    user_id: PydanticObjectId,
    price: Price,
    requested_minutes: int,
) -> int:
    """Refuses a session the wallet cannot cover, and says what is missing.

    Returns the coins the booking needs.
    """
    platform = await settings_service.get_settings()
    if not (platform.min_session_minutes <= requested_minutes <= platform.max_session_minutes):
        raise BadRequestError(
            f"Choose between {platform.min_session_minutes} and "
            f"{platform.max_session_minutes} minutes.",
            error_code="invalid_duration",
        )

    needed = price.coins_per_minute * requested_minutes
    wallet = await wallet_service.get_or_create_wallet(user_id)

    if wallet.balance_coins < needed:
        short = needed - wallet.balance_coins
        can_afford = affordable_minutes(wallet.balance_coins, price.coins_per_minute)
        # Say the useful thing: how short they are, and what they *can* have.
        detail = (
            f" You can talk for {can_afford} minute{'s' if can_afford != 1 else ''} instead."
            if can_afford >= platform.min_session_minutes
            else ""
        )
        raise BadRequestError(
            f"Not enough coins for {requested_minutes} minute"
            f"{'s' if requested_minutes != 1 else ''}. You need {needed} and have "
            f"{wallet.balance_coins} — add {short} more.{detail}",
            error_code="insufficient_coins",
            details={
                "needed_coins": needed,
                "balance_coins": wallet.balance_coins,
                "short_by_coins": short,
                "affordable_minutes": can_afford,
            },
        )
    return needed


def minutes_elapsed(started_at: datetime, now: datetime | None = None) -> int:
    """How many minutes have *started*.

    A started minute is charged in full, which is what every consultation app
    does and what the price is quoted against — 61 seconds is two minutes.
    """
    now = now or datetime.now(UTC)
    started = started_at if started_at.tzinfo else started_at.replace(tzinfo=UTC)
    seconds = max(0.0, (now - started).total_seconds())
    return max(1, math.floor(seconds / 60) + 1)


async def check_can_extend(
    *,
    user_id: PydanticObjectId,
    price: Price,
    current_minutes: int,
    extra_minutes: int,
    minutes_used: int,
) -> int:
    """Refuses an extension the wallet cannot cover.

    Only the minutes not yet paid for need covering — the ones already charged
    came out of the wallet long ago.
    """
    platform = await settings_service.get_settings()
    total = current_minutes + extra_minutes
    if total > platform.max_session_minutes:
        raise BadRequestError(
            f"A session cannot run longer than {platform.max_session_minutes} minutes.",
            error_code="too_long",
        )
    if extra_minutes < 1:
        raise BadRequestError("Add at least a minute.", error_code="invalid_duration")

    unpaid = max(0, total - minutes_used)
    needed = price.coins_per_minute * unpaid
    wallet = await wallet_service.get_or_create_wallet(user_id)

    if wallet.balance_coins < needed:
        can_add = affordable_minutes(wallet.balance_coins, price.coins_per_minute)
        raise BadRequestError(
            f"Not enough coins for {extra_minutes} more minute"
            f"{'s' if extra_minutes != 1 else ''}. You can add "
            f"{can_add} minute{'s' if can_add != 1 else ''}.",
            error_code="insufficient_coins",
            details={
                "balance_coins": wallet.balance_coins,
                "affordable_minutes": can_add,
            },
        )
    return needed


@dataclass
class ChargeResult:
    minutes_charged: int
    coins_charged: int
    earning_paise: int
    out_of_coins: bool
    minutes_left: int


async def charge_due(
    *,
    session_id: PydanticObjectId,
    mode: ConsultationMode,
    user_id: PydanticObjectId,
    astrologer_id: PydanticObjectId,
    astrologer_user_id: PydanticObjectId,
    started_at: datetime,
    price: Price,
    already_charged: int,
    cap_minutes: int | None,
    now: datetime | None = None,
) -> ChargeResult:
    """Charges every started minute that has not been paid for yet.

    Safe to call as often as anything likes: the ledger's unique key means a
    minute can only be charged once, whoever asks.
    """
    now = now or datetime.now(UTC)
    due = minutes_elapsed(started_at, now)
    if cap_minutes is not None:
        due = min(due, cap_minutes)

    charged = already_charged
    coins_total = 0
    earning_total = 0
    out_of_coins = False

    while charged < due:
        minute = charged + 1
        try:
            await wallet_service.debit(
                user_id=user_id,
                amount_coins=price.coins_per_minute,
                reason=TransactionReason.CONSULTATION,
                idempotency_key=f"session:{session_id}:minute:{minute}",
                ref=TransactionRef(session_id=session_id),
                note=f"{mode.value} · minute {minute}",
            )
        except BadRequestError as exc:
            # The only expected failure here is an empty wallet. Stop at the
            # last minute that was actually paid for — never deliver one that
            # was not.
            if exc.error_code != "insufficient_balance":
                raise
            out_of_coins = True
            break

        gross = price.coins_per_minute * price.coin_value_paise
        commission = round(gross * price.commission_percent / 100)
        earning = gross - commission

        await EarningEntry(
            astrologer_id=astrologer_id,
            astrologer_user_id=astrologer_user_id,
            user_id=user_id,
            mode=mode,
            session_id=session_id,
            minute_index=minute,
            coins_charged=price.coins_per_minute,
            gross_paise=gross,
            commission_percent=price.commission_percent,
            commission_paise=commission,
            earning_paise=earning,
        ).insert()

        charged = minute
        coins_total += price.coins_per_minute
        earning_total += earning

    wallet = await wallet_service.get_or_create_wallet(user_id)
    minutes_left = affordable_minutes(wallet.balance_coins, price.coins_per_minute)

    if coins_total:
        logger.info(
            "Session {} charged minutes {}→{} ({} coins), astrologer earned {} paise",
            session_id,
            already_charged + 1,
            charged,
            coins_total,
            earning_total,
        )

    return ChargeResult(
        minutes_charged=charged,
        coins_charged=coins_total,
        earning_paise=earning_total,
        out_of_coins=out_of_coins,
        minutes_left=minutes_left,
    )

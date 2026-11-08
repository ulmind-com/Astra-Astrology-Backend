"""Reading and changing the platform settings."""

from typing import Any

from beanie import PydanticObjectId
from loguru import logger
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import BadRequestError
from app.models.settings import SETTINGS_KEY, CoinRateChange, PlatformSettings

_in_memory_settings: PlatformSettings | None = None


def _default_platform_settings() -> PlatformSettings:
    defaults = {
        k: v.get_default(call_default_factory=True)
        for k, v in PlatformSettings.model_fields.items()
    }
    return PlatformSettings.model_construct(**defaults)


def invalidate_settings_cache() -> None:
    """Clears the in-memory settings cache so the next access fetches fresh from DB."""
    global _in_memory_settings
    _in_memory_settings = None


def set_cached_settings(doc: PlatformSettings) -> None:
    """Updates the in-memory settings cache directly."""
    global _in_memory_settings
    _in_memory_settings = doc


async def get_settings(*, force_refresh: bool = False) -> PlatformSettings:
    """Returns the singleton platform settings.

    Uses an in-memory cache to guarantee 0ms latency and eliminate repeated
    MongoDB queries during routine requests and heartbeats.
    """
    global _in_memory_settings

    if not force_refresh and _in_memory_settings is not None:
        return _in_memory_settings

    from app.db.mongodb import is_ready

    if not is_ready():
        if _in_memory_settings is None:
            _in_memory_settings = _default_platform_settings()
        return _in_memory_settings

    try:
        existing = await PlatformSettings.find_one(PlatformSettings.key == SETTINGS_KEY)
        if existing is not None:
            _in_memory_settings = existing
            return existing

        created = PlatformSettings()
        try:
            await created.insert()
        except DuplicateKeyError:
            # Two requests raced; the unique index settled it.
            existing = await PlatformSettings.find_one(PlatformSettings.key == SETTINGS_KEY)
            _in_memory_settings = existing or created
            return _in_memory_settings
        _in_memory_settings = created
        return created
    except Exception as exc:
        logger.warning(
            "Could not read platform settings from MongoDB ({}); using in-memory defaults.",
            exc,
        )
        if _in_memory_settings is None:
            _in_memory_settings = _default_platform_settings()
        return _in_memory_settings


async def _publish(doc: PlatformSettings, *, reprice: bool) -> None:
    """Mirrors a settings change to everyone watching.

    `reprice` republishes every astrologer card as well, because the defaults
    feed into the resolved price of everyone who has no rate of their own —
    changing the platform's chat rate silently re-prices most of the directory,
    and those cards have to be rewritten or they would keep showing the old
    number until something else touched them.
    """
    global _in_memory_settings
    _in_memory_settings = doc

    from app.services import realtime

    await realtime.publish_settings(doc)
    if reprice:
        await realtime.publish_all_astrologers()


async def get_coins_per_rupee() -> int:
    return (await get_settings()).coins_per_rupee


async def set_coins_per_rupee(
    *, rate: int, admin_id: PydanticObjectId | None, note: str | None = None
) -> PlatformSettings:
    """Changes the rate and records who did it.

    Coins already bought keep the rate they were bought at — this only affects
    recharges quoted from now on.
    """
    settings_doc = await get_settings()
    previous = settings_doc.coins_per_rupee

    if previous == rate:
        return settings_doc

    settings_doc.coins_per_rupee = rate
    settings_doc.updated_by = admin_id
    await settings_doc.save()

    await CoinRateChange(
        from_rate=previous, to_rate=rate, changed_by=admin_id, note=note
    ).insert()

    logger.warning("Coin rate changed from {} to {} per rupee by {}", previous, rate, admin_id)
    # The rate decides what a rupee buys, not what a minute costs, so the cards
    # do not move.
    await _publish(settings_doc, reprice=False)
    return settings_doc


async def set_recharge_limits(
    *,
    min_paise: int | None,
    max_paise: int | None,
    admin_id: PydanticObjectId | None,
) -> PlatformSettings:
    """Changes what a user may top up."""
    doc = await get_settings()

    new_min = doc.min_recharge_paise if min_paise is None else min_paise
    new_max = doc.max_recharge_paise if max_paise is None else max_paise

    # A minimum above the maximum would leave nothing a user could pay.
    if new_min > new_max:
        raise BadRequestError(
            "The smallest recharge cannot be more than the largest.",
            error_code="invalid_recharge_limits",
        )
    # Whole rupees, for the same reason recharges are: an integer coin rate on
    # a part-rupee minimum would quote a fractional coin.
    if new_min % 100 or new_max % 100:
        raise BadRequestError(
            "Use whole rupees.", error_code="not_whole_rupees"
        )

    doc.min_recharge_paise = new_min
    doc.max_recharge_paise = new_max
    doc.updated_by = admin_id
    await doc.save()

    logger.info("Recharge limits set to {}-{} paise by {}", new_min, new_max, admin_id)
    await _publish(doc, reprice=False)
    return doc


async def set_consultation_defaults(
    *, changes: dict[str, int | float | None], admin_id: PydanticObjectId | None
) -> PlatformSettings:
    """Sets what a consultation costs and what the platform keeps."""
    doc = await get_settings()

    for field, value in changes.items():
        # `None` means the caller did not send the field. `False` is a real
        # value — switching face reading off must not be read as silence.
        if value is not None:
            setattr(doc, field, value)

    if doc.min_session_minutes > doc.max_session_minutes:
        raise BadRequestError(
            "The shortest session cannot be longer than the longest.",
            error_code="invalid_session_minutes",
        )
    if doc.min_appointment_minutes > doc.max_appointment_minutes:
        raise BadRequestError(
            "The shortest appointment cannot be longer than the longest.",
            error_code="invalid_appointment_minutes",
        )
    # Appointments are booked on a five-minute grid, so the limits have to sit
    # on it too — otherwise the shortest bookable length would be unreachable.
    from app.models.appointment import SLOT_MINUTES

    if doc.min_appointment_minutes % SLOT_MINUTES or doc.max_appointment_minutes % SLOT_MINUTES:
        raise BadRequestError(
            f"Appointment lengths must be multiples of {SLOT_MINUTES} minutes.",
            error_code="unaligned_appointment_minutes",
        )

    doc.updated_by = admin_id
    await doc.save()

    # Retention is not just a number for next time: shortening it should also
    # clear out what is already stored, and lengthening it should keep what
    # would otherwise have gone. Both mean re-dating the finished chats.
    if "chat_retention_days" in changes and changes["chat_retention_days"] is not None:
        from app.services import messages as message_service

        await message_service.reschedule_expiry(int(changes["chat_retention_days"]))

    logger.info("Consultation defaults updated by {}: {}", admin_id, changes)
    # These are the numbers every unpriced astrologer charges.
    await _publish(doc, reprice=True)
    return doc


async def set_feature_pricing(
    *, changes: dict[str, Any], admin_id: PydanticObjectId | None
) -> PlatformSettings:
    """Sets coin cost and availability for astrology and scanning features."""
    from app.db.mongodb import is_ready

    doc = await get_settings()

    for field, value in changes.items():
        if value is not None:
            setattr(doc, field, value)

    doc.updated_by = admin_id
    if is_ready():
        await doc.save()

    from app.services import realtime
    await realtime.publish_feature_pricing(doc)
    await _publish(doc, reprice=False)

    logger.info("Feature pricing updated by {}: {}", admin_id, changes)
    return doc


async def rate_history(limit: int = 50) -> list[CoinRateChange]:
    return await CoinRateChange.find().sort(-CoinRateChange.created_at).limit(limit).to_list()


def coins_for(amount_paise: int, coins_per_rupee: int) -> int:
    """Rupees to coins.

    Integer arithmetic throughout: the caller guarantees whole rupees, so this
    can never produce a fraction that would have to be rounded away.
    """
    return (amount_paise // 100) * coins_per_rupee

"""Reading and changing the platform settings."""

from beanie import PydanticObjectId
from loguru import logger
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import BadRequestError
from app.models.settings import SETTINGS_KEY, CoinRateChange, PlatformSettings


async def get_settings() -> PlatformSettings:
    """Returns the singleton, creating it with defaults the first time."""
    existing = await PlatformSettings.find_one(PlatformSettings.key == SETTINGS_KEY)
    if existing is not None:
        return existing

    created = PlatformSettings()
    try:
        await created.insert()
    except DuplicateKeyError:
        # Two requests raced; the unique index settled it.
        existing = await PlatformSettings.find_one(PlatformSettings.key == SETTINGS_KEY)
        if existing is None:  # pragma: no cover - the index guarantees one
            raise
        return existing
    return created


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
    return doc


async def set_consultation_defaults(
    *, changes: dict[str, int | float | None], admin_id: PydanticObjectId | None
) -> PlatformSettings:
    """Sets what a consultation costs and what the platform keeps."""
    doc = await get_settings()

    for field, value in changes.items():
        if value is not None:
            setattr(doc, field, value)

    if doc.min_session_minutes > doc.max_session_minutes:
        raise BadRequestError(
            "The shortest session cannot be longer than the longest.",
            error_code="invalid_session_minutes",
        )

    doc.updated_by = admin_id
    await doc.save()
    logger.info("Consultation defaults updated by {}: {}", admin_id, changes)
    return doc


async def rate_history(limit: int = 50) -> list[CoinRateChange]:
    return await CoinRateChange.find().sort(-CoinRateChange.created_at).limit(limit).to_list()


def coins_for(amount_paise: int, coins_per_rupee: int) -> int:
    """Rupees to coins.

    Integer arithmetic throughout: the caller guarantees whole rupees, so this
    can never produce a fraction that would have to be rounded away.
    """
    return (amount_paise // 100) * coins_per_rupee

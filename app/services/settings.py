"""Reading and changing the platform settings."""

from beanie import PydanticObjectId
from loguru import logger
from pymongo.errors import DuplicateKeyError

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


async def rate_history(limit: int = 50) -> list[CoinRateChange]:
    return await CoinRateChange.find().sort(-CoinRateChange.created_at).limit(limit).to_list()


def coins_for(amount_paise: int, coins_per_rupee: int) -> int:
    """Rupees to coins.

    Integer arithmetic throughout: the caller guarantees whole rupees, so this
    can never produce a fraction that would have to be rounded away.
    """
    return (amount_paise // 100) * coins_per_rupee

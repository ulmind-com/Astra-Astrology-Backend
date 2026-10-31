"""Astrologer favorites service."""

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import NotFoundError
from app.models.astrologer import Astrologer
from app.models.base import utcnow
from app.models.favorite import AstrologerFavorite
from app.models.user import User


async def toggle_favorite(user: User, identifier: str) -> tuple[bool, int]:
    """Toggle favorite status for an astrologer. Returns (is_favorite, count)."""
    astrologer = None
    if PydanticObjectId.is_valid(identifier):
        try:
            astrologer = await Astrologer.get(PydanticObjectId(identifier))
        except Exception:
            pass
    if astrologer is None:
        astrologer = await Astrologer.find_one(Astrologer.slug == identifier)
    if astrologer is None:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    existing = await AstrologerFavorite.find_one(
        {"user_id": user.id, "astrologer_id": astrologer.id}
    )

    if existing is not None:
        await existing.delete()
        is_favorite = False
    else:
        try:
            await AstrologerFavorite(
                user_id=user.id,
                astrologer_id=astrologer.id,
            ).insert()
            is_favorite = True
        except DuplicateKeyError:
            is_favorite = True

    # Count all favorites for this astrologer
    count = await AstrologerFavorite.find(
        {"astrologer_id": astrologer.id}
    ).count()

    # Atomically update followers_count in MongoDB
    await Astrologer.get_pymongo_collection().update_one(
        {"_id": astrologer.id},
        {"$set": {"followers_count": count, "updated_at": utcnow()}},
    )

    return is_favorite, count


async def get_favorite_status(user: User | None, identifier: str) -> tuple[bool, int]:
    """Check if an astrologer is favorited by the user and get total favorites count."""
    astrologer = None
    if PydanticObjectId.is_valid(identifier):
        try:
            astrologer = await Astrologer.get(PydanticObjectId(identifier))
        except Exception:
            pass
    if astrologer is None:
        astrologer = await Astrologer.find_one(Astrologer.slug == identifier)
    if astrologer is None:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    count = await AstrologerFavorite.find(
        {"astrologer_id": astrologer.id}
    ).count()

    is_fav = False
    if user is not None:
        fav = await AstrologerFavorite.find_one(
            {"user_id": user.id, "astrologer_id": astrologer.id}
        )
        is_fav = fav is not None

    return is_fav, count


async def list_user_favorites(user: User) -> list[Astrologer]:
    """Get all astrologers favorited by the current user."""
    favorites = await AstrologerFavorite.find(
        {"user_id": user.id}
    ).sort("-created_at").to_list()

    if not favorites:
        return []

    astrologer_ids = [f.astrologer_id for f in favorites]
    astrologers = await Astrologer.find(
        {"_id": {"$in": astrologer_ids}}
    ).to_list()

    lookup = {a.id: a for a in astrologers}
    return [lookup[aid] for aid in astrologer_ids if aid in lookup]

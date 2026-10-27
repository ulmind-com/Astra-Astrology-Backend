"""Live updates, pushed over our own WebSocket.

Browsers hold one socket to this backend and are told when something they are
looking at changes: an astrologer's price, whether they are at their desk, the
platform's rates, a wallet balance. MongoDB remains the one database and the
one authority — nothing here stores anything, it only forwards what MongoDB
has already accepted.

Deliberately *not* Firestore. Mirroring every change into Firestore so browsers
could subscribe to it meant paying a document write for every minute of every
consultation, and Firebase is kept for the two things only it does here:
authentication, and the chat transcript. A socket we own costs nothing per
message.

**One process.** The registry is in memory, so a broadcast reaches the clients
connected to *this* worker. The app is deployed as a single uvicorn process
(see the Dockerfile), which makes that complete. Running more than one worker
would need a bus between them — MongoDB change streams would do it without new
infrastructure — and this module is the only place that would change.

Nothing here may raise into a request. A client that has gone away, or a socket
that fails mid-write, must never turn someone's recharge into an error: the
REST response is still the truth and the next poll still corrects the screen.
"""

import asyncio
from typing import Any

from loguru import logger

# ------------------------------------------------------------------ registry
# Every open socket, and who is behind it. The user id is None for a visitor
# who is not signed in — they still get the public feed.
_connections: set["Connection"] = set()


class Connection:
    """One browser. Owns its socket and the queue feeding it.

    Messages go through a queue rather than straight to the socket so that a
    slow client cannot hold up whoever is publishing. If a client falls far
    enough behind to fill the queue, its oldest messages are dropped — a stale
    price is worth less than a blocked wallet transaction.
    """

    MAX_QUEUED = 64

    def __init__(self, websocket: Any, user_id: str | None, role: str | None) -> None:
        self.websocket = websocket
        self.user_id = user_id
        self.role = role
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self.MAX_QUEUED)

    def offer(self, message: dict[str, Any]) -> None:
        try:
            self.queue.put_nowait(message)
        except asyncio.QueueFull:
            # Drop the oldest, keep the newest: the latest price is the one
            # that matters, not the one from four updates ago.
            try:
                self.queue.get_nowait()
                self.queue.put_nowait(message)
            except (asyncio.QueueEmpty, asyncio.QueueFull):  # pragma: no cover
                pass


def register(connection: Connection) -> None:
    _connections.add(connection)


def unregister(connection: Connection) -> None:
    _connections.discard(connection)


def connection_count() -> int:
    return len(_connections)


def is_connected(user_id: str) -> bool:
    """Does this person have at least one socket open right now?

    This is what presence is built on: an astrologer with an open panel has a
    socket, and the moment they close the tab the socket closes with it.
    """
    return any(c.user_id == user_id for c in _connections)


# ---------------------------------------------------------------- publishing
def _broadcast(message: dict[str, Any], *, to_user: str | None = None) -> None:
    """Hands a message to every connection that should see it.

    Synchronous and non-blocking by design: publishers call this from the
    middle of a request and must not wait on anyone's network.
    """
    for connection in _connections:
        if to_user is not None and connection.user_id != to_user:
            continue
        connection.offer(message)


def is_enabled() -> bool:
    """Kept so callers read the same as before. A socket needs no configuring."""
    return True


# ------------------------------------------------------------- astrologers
async def astrologer_payload(profile: Any) -> dict[str, Any]:
    """Exactly the fields a directory card and a profile header draw.

    Prices are resolved here — an astrologer with no rate of their own carries
    the platform's — so the browser never has to resolve a null, and never has
    to agree with us about how.
    """
    from app.models.enums import ConsultationMode
    from app.services import billing, presence

    availability = profile.availability
    rates = {}
    for mode, key in (
        (ConsultationMode.CHAT, "chat"),
        (ConsultationMode.CALL, "call"),
        (ConsultationMode.VIDEO, "video"),
    ):
        rates[f"{key}_coins_per_minute"] = (
            await billing.price_for(profile, mode)
        ).coins_per_minute

    last_seen = availability.last_seen_at
    return {
        "id": str(profile.id),
        "slug": profile.slug,
        "display_name": profile.display_name,
        "is_listed": bool(profile.is_listed),
        "is_featured": bool(profile.is_featured),
        "modes_enabled": [m.value for m in profile.modes_enabled],
        "rates": rates,
        "rating": {"average": profile.rating.average, "count": profile.rating.count},
        "total_consultations": profile.total_consultations,
        "availability": {
            # The stored intent, plus the stamp that says whether it is still
            # true. The browser applies the same TTL we do, so a card goes grey
            # on its own even if this backend never sends another word.
            "is_online": bool(availability.is_online),
            "is_busy": bool(availability.is_busy),
            "is_available_for_chat": bool(availability.is_available_for_chat),
            "is_available_for_call": bool(availability.is_available_for_call),
            "is_available_for_video": bool(availability.is_available_for_video),
            "last_seen_at": last_seen.isoformat() if last_seen else None,
            "ttl_seconds": presence.TTL_SECONDS,
        },
    }


async def publish_astrologer(profile: Any) -> None:
    """Tells everyone watching that this astrologer's card changed."""
    try:
        payload = await astrologer_payload(profile)
    except Exception as exc:  # noqa: BLE001 - a missed update is not a failed request
        logger.warning("Could not build the live payload for {}: {}", profile.id, exc)
        return
    _broadcast({"type": "astrologer", "data": payload})


# ------------------------------------------------------------------ settings
def build_feature_pricing_payload(platform: Any) -> dict[str, dict[str, Any]]:
    """Builds a JSON-safe dictionary of all 9 astrology & scanning features."""
    return {
        "daily_horoscope": {
            "feature_id": "daily_horoscope",
            "name": "Daily Horoscope",
            "coins": getattr(platform, "daily_horoscope_coins", 0),
            "is_free": getattr(platform, "daily_horoscope_coins", 0) == 0,
            "enabled": getattr(platform, "daily_horoscope_enabled", True),
            "description": "Daily Transit, Panchang & Planetary Analysis",
        },
        "kundli": {
            "feature_id": "kundli",
            "name": "Kundli Generator",
            "coins": getattr(platform, "kundli_coins", 20),
            "is_free": getattr(platform, "kundli_coins", 20) == 0,
            "enabled": getattr(platform, "kundli_enabled", True),
            "description": "Complete Kundli, D1/D9 Charts, Planetary Table & 3x3 Dasha",
        },
        "kundli_matching": {
            "feature_id": "kundli_matching",
            "name": "Kundli Matching",
            "coins": getattr(platform, "kundli_matching_coins", 20),
            "is_free": getattr(platform, "kundli_matching_coins", 20) == 0,
            "enabled": getattr(platform, "kundli_matching_enabled", True),
            "description": "36 Gunas Ashtakoot Milan & Dosha Check",
        },
        "kp_calculator": {
            "feature_id": "kp_calculator",
            "name": "KP Astrology",
            "coins": getattr(platform, "kp_calculator_coins", 20),
            "is_free": getattr(platform, "kp_calculator_coins", 20) == 0,
            "enabled": getattr(platform, "kp_calculator_enabled", True),
            "description": "Placidus Cusps, Ruling Planets & Sub-Lords",
        },
        "dasha_calculator": {
            "feature_id": "dasha_calculator",
            "name": "Dasha Calculator",
            "coins": getattr(platform, "dasha_calculator_coins", 15),
            "is_free": getattr(platform, "dasha_calculator_coins", 15) == 0,
            "enabled": getattr(platform, "dasha_calculator_enabled", True),
            "description": "Complete Vimshottari Mahadasha/Antardasha Tree",
        },
        "rashi_calculator": {
            "feature_id": "rashi_calculator",
            "name": "Rashi Calculator",
            "coins": getattr(platform, "rashi_calculator_coins", 10),
            "is_free": getattr(platform, "rashi_calculator_coins", 10) == 0,
            "enabled": getattr(platform, "rashi_calculator_enabled", True),
            "description": "Moon Sign, Traits, Remedies & Avakahada",
        },
        "nakshatra_calculator": {
            "feature_id": "nakshatra_calculator",
            "name": "Nakshatra Calculator",
            "coins": getattr(platform, "nakshatra_calculator_coins", 10),
            "is_free": getattr(platform, "nakshatra_calculator_coins", 10) == 0,
            "enabled": getattr(platform, "nakshatra_calculator_enabled", True),
            "description": "Janma Nakshatra, Pada, Tarabala & Sacred Mantras",
        },
        "palm_reading": {
            "feature_id": "palm_reading",
            "name": "Palm Reading",
            "coins": getattr(platform, "palm_reading_coins", 25),
            "is_free": getattr(platform, "palm_reading_coins", 25) == 0,
            "enabled": getattr(platform, "palm_reading_enabled", True),
            "description": "AI Computer Vision Palmistry & Crease Analysis",
        },
        "face_reading": {
            "feature_id": "face_reading",
            "name": "Face Reading",
            "coins": getattr(platform, "face_reading_coins", 25),
            "is_free": getattr(platform, "face_reading_coins", 25) == 0,
            "enabled": getattr(platform, "face_reading_enabled", True),
            "description": "Facial Morphology & Vedic Samudrika Shastra",
        },
        "numerology": {
            "feature_id": "numerology",
            "name": "Numerology",
            "coins": getattr(platform, "numerology_coins", 20),
            "is_free": getattr(platform, "numerology_coins", 20) == 0,
            "enabled": getattr(platform, "numerology_enabled", True),
            "description": "Vedic & Chaldean Numerology, Lo Shu Grid, Dasha & Mobile Audit",
        },
        "vastu": {
            "feature_id": "vastu",
            "name": "Vastu Shastra",
            "coins": getattr(platform, "vastu_coins", 25),
            "is_free": getattr(platform, "vastu_coins", 25) == 0,
            "enabled": getattr(platform, "vastu_enabled", True),
            "description": "16-Zone & 32-Pada Vastu Compass, Ayadi Shadvarga & Remedies",
        },
    }


async def publish_feature_pricing(platform: Any) -> None:
    """Tells all connected clients (web & admin) that feature prices or toggles changed."""
    try:
        payload = build_feature_pricing_payload(platform)
        _broadcast({"type": "feature_pricing", "data": payload})
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not broadcast live feature pricing: {}", exc)


async def publish_settings(platform: Any) -> None:
    """The numbers every price on the site is derived from."""
    _broadcast(
        {
            "type": "settings",
            "data": {
                "coins_per_rupee": platform.coins_per_rupee,
                "min_recharge_paise": platform.min_recharge_paise,
                "max_recharge_paise": platform.max_recharge_paise,
                "default_rates": {
                    "chat_coins_per_minute": platform.default_chat_coins_per_minute,
                    "call_coins_per_minute": platform.default_call_coins_per_minute,
                    "video_coins_per_minute": platform.default_video_coins_per_minute,
                },
                "min_session_minutes": platform.min_session_minutes,
                "max_session_minutes": platform.max_session_minutes,
            },
        }
    )
    await publish_feature_pricing(platform)


async def publish_all_astrologers() -> int:
    """Re-sends every card.

    Used after a platform default changes, because that is the price of
    everyone who has no rate of their own.
    """
    from app.models.astrologer import Astrologer

    sent = 0
    for profile in await Astrologer.find_all().to_list():
        await publish_astrologer(profile)
        sent += 1
    return sent


# ------------------------------------------------------------------- wallet
async def publish_wallet_for_user(user_id: Any, balance_coins: int) -> None:
    """One person's balance, to that person's own sockets and nobody else's."""
    _broadcast(
        {"type": "wallet", "data": {"balance_coins": balance_coins}},
        to_user=str(user_id),
    )


# -------------------------------------------------------------------- chat
async def publish_chat(user_id: Any, message: dict[str, Any]) -> None:
    """A chat message or read receipt, to one participant's sockets.

    Addressed per person rather than per conversation, because a socket
    belongs to a person and may be looking at any screen — the chat window
    does not have to be open for the message to arrive.
    """
    _broadcast(message, to_user=str(user_id))

"""The live socket.

One connection per browser, carrying everything a screen needs to stay true:
astrologer cards, platform rates, and — for whoever is signed in — their own
coin balance.

Two things make it worth its own endpoint rather than polling:

  * **Presence is the connection.** An astrologer with the panel open holds a
    socket. Close the tab, shut the laptop, lose wifi, and the socket dies with
    it — which is the honest signal that they have gone. No heartbeat request
    every twenty seconds, and nothing to leave a flag stuck on.
  * **Coins move while you watch them.** A consultation spends them a minute at
    a time, and a balance that only refreshes on navigation is wrong for most
    of a call.

Authentication is optional. A visitor who is not signed in still gets the
public feed, because the directory is public; only the wallet is filtered to
its owner.
"""

import asyncio
import contextlib
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from loguru import logger

from app.services import realtime

router = APIRouter(tags=["live"])

# How long to wait for a client to say something before assuming the socket is
# half-open. Browsers send a ping well inside this; a laptop that was closed
# mid-connection sends nothing, and some networks never deliver the FIN.
IDLE_TIMEOUT_SECONDS = 70


async def _identify(token: str | None) -> tuple[str | None, str | None]:
    """Who is on the other end, if anyone. Never raises on a bad token."""
    if not token:
        return None, None
    try:
        from app.core.security import decode_token

        payload = decode_token(token)
        return str(payload.get("sub")), payload.get("role")
    except Exception:  # noqa: BLE001 - an unreadable token is just a visitor
        return None, None


async def _pump(connection: realtime.Connection) -> None:
    """Sends whatever has been queued for this client, in order."""
    while True:
        message = await connection.queue.get()
        await connection.websocket.send_json(message)


@router.websocket("/live")
async def live(websocket: WebSocket, token: str | None = Query(default=None)) -> None:
    await websocket.accept()

    user_id, role = await _identify(token)
    connection = realtime.Connection(websocket, user_id, role)
    realtime.register(connection)

    # An astrologer holding this socket is an astrologer at their desk.
    await _set_presence(user_id, role, online=True)

    sender = asyncio.create_task(_pump(connection))
    try:
        await websocket.send_json({"type": "ready", "data": {"signed_in": bool(user_id)}})

        # Deliver current feature pricing immediately upon connection
        try:
            from app.services import settings as settings_service

            platform = await settings_service.get_settings()
            connection.offer(
                {
                    "type": "feature_pricing",
                    "data": realtime.build_feature_pricing_payload(platform),
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Could not queue initial feature pricing: {}", exc)

        while True:
            # The client pings; anything arriving proves the socket is alive.
            # Nothing arriving for longer than the timeout means it is not.
            await asyncio.wait_for(websocket.receive_text(), timeout=IDLE_TIMEOUT_SECONDS)
            connection.offer({"type": "pong"})
            await _touch_presence(user_id, role)

    except (TimeoutError, WebSocketDisconnect):
        pass
    except Exception as exc:  # noqa: BLE001 - a dropped socket is normal
        logger.debug("Live socket ended: {}", exc)
    finally:
        sender.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sender
        realtime.unregister(connection)
        # Only the *last* tab closing takes them offline — an astrologer with
        # the panel open twice is still at their desk.
        if not (user_id and realtime.is_connected(user_id)):
            await _set_presence(user_id, role, online=False)


# -------------------------------------------------------------- presence
async def _profile_for(user_id: str | None, role: str | None) -> Any:
    if not user_id or role != "astrologer":
        return None
    from beanie import PydanticObjectId

    from app.models.astrologer import Astrologer

    if not PydanticObjectId.is_valid(user_id):
        return None
    return await Astrologer.find_one(Astrologer.user_id == PydanticObjectId(user_id))


async def _set_presence(user_id: str | None, role: str | None, *, online: bool) -> None:
    """Opening the panel is going online; closing it is going offline."""
    try:
        profile = await _profile_for(user_id, role)
        if profile is None:
            return
        from app.services import presence

        if online:
            await presence.beat(profile)
        else:
            await presence.go_offline(profile, reason="panel closed")
    except Exception as exc:  # noqa: BLE001 - presence must never break the socket
        logger.warning("Could not update presence for {}: {}", user_id, exc)


async def _touch_presence(user_id: str | None, role: str | None) -> None:
    """Refreshes the stamp, so the read-time TTL keeps agreeing they are here."""
    try:
        profile = await _profile_for(user_id, role)
        if profile is None:
            return
        from app.services import presence

        await presence.beat(profile)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Presence refresh skipped for {}: {}", user_id, exc)

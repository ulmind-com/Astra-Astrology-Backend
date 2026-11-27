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
    try:
        while True:
            message = await connection.queue.get()
            await connection.websocket.send_json(message)
    except (WebSocketDisconnect, RuntimeError, Exception):
        # A disconnected client or cancelled task is a normal end of the stream
        pass


async def _verify_whiteboard_peer(user_id: str, to_user: str, call_id: str | None) -> bool:
    """Confirm user_id and to_user share an active/scheduled consultation session."""
    from beanie import PydanticObjectId

    from app.models.appointment import Appointment
    from app.models.call import CallSession
    from app.models.chat import ChatSession
    from app.models.enums import AppointmentStatus, CallStatus, ChatStatus

    if not (PydanticObjectId.is_valid(user_id) and PydanticObjectId.is_valid(to_user)):
        return False
    if user_id == to_user:
        return False

    u1 = PydanticObjectId(user_id)
    u2 = PydanticObjectId(to_user)
    pair_filter = {
        "$or": [
            {"user_id": u1, "astrologer_user_id": u2},
            {"user_id": u2, "astrologer_user_id": u1},
        ]
    }

    if call_id and PydanticObjectId.is_valid(call_id):
        cid = PydanticObjectId(call_id)
        call = await CallSession.find_one(
            {
                "_id": cid,
                "status": {"$in": [CallStatus.RINGING, CallStatus.ACTIVE]},
                **pair_filter,
            }
        )
        if call is not None:
            return True
        appt = await Appointment.find_one(
            {
                "_id": cid,
                "status": AppointmentStatus.BOOKED,
                **pair_filter,
            }
        )
        return appt is not None

    # Fallback when call_id is omitted: require an active call/chat or booked appointment
    active_call = await CallSession.find_one(
        {"status": {"$in": [CallStatus.RINGING, CallStatus.ACTIVE]}, **pair_filter}
    )
    if active_call is not None:
        return True
    active_chat = await ChatSession.find_one(
        {"status": {"$in": [ChatStatus.REQUESTED, ChatStatus.ACTIVE]}, **pair_filter}
    )
    if active_chat is not None:
        return True
    booked_appt = await Appointment.find_one(
        {"status": AppointmentStatus.BOOKED, **pair_filter}
    )
    return booked_appt is not None


@router.websocket("/live")
async def live(websocket: WebSocket, token: str | None = Query(default=None)) -> None:
    await websocket.accept()

    user_id, role = await _identify(token)
    connection = realtime.Connection(websocket, user_id, role)
    realtime.register(connection)
    verified_peers: set[tuple[str | None, str]] = set()

    # An astrologer or purohit holding this socket is live at their desk.
    panel_profile = await _profile_for(user_id, role)
    await _set_presence(panel_profile, online=True)

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
            raw_text = await asyncio.wait_for(websocket.receive_text(), timeout=IDLE_TIMEOUT_SECONDS)
            connection.offer({"type": "pong"})
            await _touch_presence(panel_profile)

            # Handle live collaborative whiteboard broadcast frames if sent over websocket
            if raw_text and raw_text.startswith("{"):
                try:
                    import json
                    msg = json.loads(raw_text)
                    event_type = msg.get("type") or msg.get("action")
                    if event_type in ("whiteboard_live", "whiteboard_event", "whiteboard_sync"):
                        to_user_raw = msg.get("to_user")
                        if not user_id or not to_user_raw:
                            continue
                        to_user_id = str(to_user_raw)
                        raw_data = msg.get("data")
                        msg_data = raw_data if isinstance(raw_data, dict) else {}
                        raw_call_id = msg.get("call_id") or msg_data.get("call_id")
                        call_id_str = str(raw_call_id) if raw_call_id else None
                        peer_key = (call_id_str, to_user_id)
                        if peer_key not in verified_peers:
                            if not await _verify_whiteboard_peer(user_id, to_user_id, call_id_str):
                                continue
                            verified_peers.add(peer_key)
                        payload = {
                            "type": event_type,
                            "data": msg_data,
                        }
                        realtime._broadcast(payload, to_user=to_user_id)
                except Exception:
                    pass

    except (TimeoutError, WebSocketDisconnect):
        pass
    except Exception as exc:  # noqa: BLE001 - a dropped socket is normal
        logger.debug("Live socket ended: {}", exc)
    finally:
        sender.cancel()
        with contextlib.suppress(asyncio.CancelledError, WebSocketDisconnect, Exception):
            await sender
        realtime.unregister(connection)
        # Only the *last* tab closing takes them offline — a panel user with
        # the panel open twice is still at their desk.
        if not (user_id and realtime.is_connected(user_id)):
            await _set_presence(panel_profile, online=False)


# -------------------------------------------------------------- presence
async def _profile_for(user_id: str | None, role: str | None) -> tuple[str, Any] | None:
    if not user_id or role not in ("astrologer", "purohit"):
        return None
    from beanie import PydanticObjectId

    if not PydanticObjectId.is_valid(user_id):
        return None
    oid = PydanticObjectId(user_id)

    if role == "astrologer":
        from app.models.astrologer import Astrologer

        profile = await Astrologer.find_one(Astrologer.user_id == oid)
        return ("astrologer", profile) if profile is not None else None

    from app.models.purohit import Purohit

    profile = await Purohit.find_one(Purohit.user_id == oid)
    return ("purohit", profile) if profile is not None else None


async def _set_presence(entry: tuple[str, Any] | None, *, online: bool) -> None:
    """Opening the panel is going online; closing it is going offline."""
    if entry is None:
        return
    kind, profile = entry
    try:
        if kind == "purohit":
            from app.services import purohit_presence

            if online:
                await purohit_presence.beat(profile, force_online=True)
            else:
                await purohit_presence.go_offline(profile, reason="panel closed")
            return

        from app.services import presence

        if online:
            await presence.beat(profile)
        else:
            await presence.go_offline(profile, reason="panel closed")
    except Exception as exc:  # noqa: BLE001 - presence must never break the socket
        logger.warning("Could not update presence ({}): {}", kind, exc)


async def _touch_presence(entry: tuple[str, Any] | None) -> None:
    """Refreshes the stamp, so the read-time TTL keeps agreeing they are here.

    Throttled to only write to MongoDB every 25 seconds instead of every ping.
    """
    if entry is None:
        return
    kind, profile = entry
    try:
        from app.models.base import utcnow

        if kind == "purohit":
            from app.services import purohit_presence

            last_seen = getattr(profile, "last_seen_at", None)
            if last_seen and (utcnow() - purohit_presence._as_utc(last_seen)).total_seconds() < 25:
                return
            await purohit_presence.beat(profile, force_online=False)
            return

        from app.services import presence

        last_seen = getattr(profile.availability, "last_seen_at", None)
        if last_seen and (utcnow() - last_seen).total_seconds() < 25:
            return

        await presence.beat(profile)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Presence refresh skipped: {}", exc)

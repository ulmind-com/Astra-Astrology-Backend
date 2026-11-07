"""Two-Way Bidirectional Google Calendar Sync Service.

Features:
1. Google OAuth 2.0 Authorization URL generation & code exchange for tokens.
2. Automatic token refresh when access tokens expire.
3. FreeBusy API queries to detect astrologer's external commitments (e.g. Doctor visits, personal events).
4. Automatic blocking of colliding slots on Astra platform so seekers cannot book overlapping times.
5. Push Astra booked consultations directly into astrologer's Google Calendar.
6. Automatic deletion/cancellation of Google events upon Astra appointment cancellation.
7. Development / mock fallback mode when GOOGLE_CLIENT_ID is not configured.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from beanie import PydanticObjectId
import httpx
from loguru import logger

from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.models.appointment import Appointment
from app.models.astrologer import Astrologer
from app.models.base import utcnow
from app.models.user import User

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_CALENDAR_FREEBUSY_ENDPOINT = "https://www.googleapis.com/calendar/v3/freeBusy"
GOOGLE_CALENDAR_EVENTS_ENDPOINT = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
]


def is_google_configured() -> bool:
    """Returns True if Google OAuth client ID and secret are set."""
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def get_auth_url(astrologer_id: PydanticObjectId, redirect_uri: str | None = None) -> dict[str, Any]:
    """Generates the Google OAuth authorization URL for the astrologer."""
    r_uri = redirect_uri or settings.GOOGLE_CALENDAR_REDIRECT_URI
    if not is_google_configured():
        # Demo simulation URL for development/staging
        mock_code = f"mock_google_code_{astrologer_id}"
        mock_target = f"{r_uri}{'&' if '?' in r_uri else '?'}code={mock_code}&state={astrologer_id}"
        return {
            "configured": False,
            "auth_url": mock_target,
            "mode": "simulation",
            "message": "Google Client ID not configured in environment. Using simulation mode.",
        }

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": r_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": str(astrologer_id),
    }
    return {
        "configured": True,
        "auth_url": f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}",
        "mode": "live",
        "message": "Redirect astrologer to this Google OAuth consent screen.",
    }


async def exchange_code_for_tokens(
    astrologer: Astrologer, code: str, redirect_uri: str | None = None
) -> dict[str, Any]:
    """Exchanges Google authorization code for access and refresh tokens."""
    r_uri = redirect_uri or settings.GOOGLE_CALENDAR_REDIRECT_URI

    # 1. Handle Mock/Simulation Code
    if code.startswith("mock_google_code_") or not is_google_configured():
        email = f"{astrologer.slug or 'astrologer'}@gmail.com"
        astrologer.google_calendar.connected = True
        astrologer.google_calendar.email = email
        astrologer.google_calendar.access_token = f"mock_token_{uuid_hex()}"
        astrologer.google_calendar.refresh_token = f"mock_refresh_{uuid_hex()}"
        astrologer.google_calendar.token_expiry = utcnow() + timedelta(days=30)
        astrologer.google_calendar.sync_enabled = True
        astrologer.google_calendar.last_synced_at = utcnow()
        await astrologer.save()

        # Generate realistic simulated personal blocks for tomorrow
        await sync_astrologer_calendar(astrologer.id)
        return {
            "connected": True,
            "email": email,
            "mode": "simulation",
            "message": "Google Calendar successfully connected in simulation mode.",
        }

    # 2. Live Exchange with Google OAuth Endpoint
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": r_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(GOOGLE_TOKEN_ENDPOINT, data=payload)
        if res.status_code != 200:
            logger.error("Failed to exchange code with Google: {}", res.text)
            raise BadRequestError(
                "Google authorization failed. Could not verify OAuth code.",
                error_code="google_auth_failed",
            )
        token_data = res.json()

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)

        # Fetch Google user email
        userinfo_res = await client.get(
            GOOGLE_USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        email = userinfo_res.json().get("email", "connected-astrologer@gmail.com") if userinfo_res.status_code == 200 else "google-user@gmail.com"

    astrologer.google_calendar.connected = True
    astrologer.google_calendar.email = email
    astrologer.google_calendar.access_token = access_token
    if refresh_token:
        astrologer.google_calendar.refresh_token = refresh_token
    astrologer.google_calendar.token_expiry = utcnow() + timedelta(seconds=expires_in)
    astrologer.google_calendar.sync_enabled = True
    astrologer.google_calendar.last_synced_at = utcnow()
    await astrologer.save()

    # Trigger initial freeBusy sync
    await sync_astrologer_calendar(astrologer.id)

    return {
        "connected": True,
        "email": email,
        "mode": "live",
        "message": f"Successfully connected Google Calendar ({email}). External commitments will now shield Astra slots.",
    }


async def refresh_token_if_needed(astrologer: Astrologer) -> str | None:
    """Ensures a valid Google access token is active, refreshing if expired."""
    gc = astrologer.google_calendar
    if not gc.connected:
        return None
    if not is_google_configured() or (gc.access_token and gc.access_token.startswith("mock_token_")):
        return gc.access_token or "mock_token"

    now = utcnow()
    if gc.token_expiry and gc.token_expiry > now + timedelta(minutes=5):
        return gc.access_token

    if not gc.refresh_token:
        logger.warning("No refresh token available for astrologer {}. Cannot refresh Google token.", astrologer.id)
        return gc.access_token

    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": gc.refresh_token,
        "grant_type": "refresh_token",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(GOOGLE_TOKEN_ENDPOINT, data=payload)
            if res.status_code == 200:
                data = res.json()
                gc.access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                gc.token_expiry = now + timedelta(seconds=expires_in)
                await astrologer.save()
                return gc.access_token
            else:
                logger.error("Failed to refresh Google token for {}: {}", astrologer.id, res.text)
    except Exception as exc:
        logger.error("Exception during Google token refresh for {}: {}", astrologer.id, exc)

    return gc.access_token


async def fetch_google_busy_intervals(
    astrologer: Astrologer, time_min: datetime, time_max: datetime
) -> list[dict[str, Any]]:
    """Queries Google Calendar FreeBusy API or returns simulation busy slots."""
    gc = astrologer.google_calendar
    if not gc.connected or not gc.sync_enabled:
        return []

    # Simulation / Mock Mode
    if not is_google_configured() or (gc.access_token and gc.access_token.startswith("mock_token_")):
        # Generate predictable sample external busy block on tomorrow (e.g. 14:00 - 15:30 IST = 08:30 - 10:00 UTC)
        tomorrow = utcnow().date() + timedelta(days=1)
        sim_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 8, 30, tzinfo=UTC)
        sim_end = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0, tzinfo=UTC)
        if time_min <= sim_end and time_max >= sim_start:
            return [
                {
                    "starts_at": sim_start.isoformat(),
                    "ends_at": sim_end.isoformat(),
                    "title": "Google Calendar: Dr. Appointment / Family Commitment",
                    "source": "google_calendar",
                    "is_external": True,
                }
            ]
        return []

    # Live Google FreeBusy Call
    token = await refresh_token_if_needed(astrologer)
    if not token:
        return []

    body = {
        "timeMin": time_min.isoformat(),
        "timeMax": time_max.isoformat(),
        "items": [{"id": "primary"}],
    }

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.post(
                GOOGLE_CALENDAR_FREEBUSY_ENDPOINT,
                json=body,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
            if res.status_code != 200:
                logger.warning("Google FreeBusy query failed ({}) for {}: {}", res.status_code, astrologer.id, res.text)
                return []

            busy_data = res.json().get("calendars", {}).get("primary", {}).get("busy", [])
            intervals = []
            for item in busy_data:
                intervals.append({
                    "starts_at": item.get("start"),
                    "ends_at": item.get("end"),
                    "title": "Google Calendar: Busy / Private Event",
                    "source": "google_calendar",
                    "is_external": True,
                })
            return intervals
    except Exception as exc:
        logger.error("Exception fetching Google FreeBusy for {}: {}", astrologer.id, exc)
        return []


async def sync_astrologer_calendar(astrologer_id: PydanticObjectId, horizon_days: int = 14) -> dict[str, Any]:
    """Performs bidirectional synchronization: refreshes external busy blocks from Google."""
    astrologer = await Astrologer.get(astrologer_id)
    if not astrologer or not astrologer.google_calendar.connected:
        return {"connected": False, "synced": False, "message": "Google Calendar not connected."}

    start = utcnow()
    end = start + timedelta(days=horizon_days)

    busy = await fetch_google_busy_intervals(astrologer, start, end)
    astrologer.google_calendar.busy_intervals = busy
    astrologer.google_calendar.last_synced_at = utcnow()
    await astrologer.save()

    return {
        "connected": True,
        "email": astrologer.google_calendar.email,
        "busy_count": len(busy),
        "last_synced_at": astrologer.google_calendar.last_synced_at.isoformat(),
        "message": f"Synced {len(busy)} external Google Calendar commitments.",
    }


async def push_appointment_to_google(appointment: Appointment, astrologer: Astrologer) -> str | None:
    """Creates a new event in the astrologer's Google Calendar for an Astra booking."""
    gc = astrologer.google_calendar
    if not gc.connected or not gc.sync_enabled:
        return None

    user = await User.get(appointment.user_id)
    client_name = user.full_name or user.first_name if user else "Seeker"
    pillar = (appointment.consultation_pillar or "Vedic Consultation").replace("_", " ").title()

    # Simulation / Mock Mode
    if not is_google_configured() or (gc.access_token and gc.access_token.startswith("mock_token_")):
        event_id = f"gcal_mock_event_{appointment.id}"
        appointment.google_calendar_event_id = event_id
        await appointment.save()
        logger.info("Created simulated Google Calendar event {} for appointment {}", event_id, appointment.id)
        return event_id

    token = await refresh_token_if_needed(astrologer)
    if not token:
        return None

    body = {
        "summary": f"Astra Astrology Consultation: {client_name}",
        "description": (
            f"Vedic Consultation with {client_name}\n"
            f"Focus Area: {pillar}\n"
            f"Duration: {appointment.minutes} minutes\n"
            f"Status: Confirmed / Escrow Protected\n"
            f"Astra Appointment ID: {appointment.id}"
        ),
        "start": {"dateTime": appointment.starts_at.isoformat()},
        "end": {"dateTime": appointment.ends_at.isoformat()},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 15},
                {"method": "email", "minutes": 60},
            ],
        },
    }

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.post(
                GOOGLE_CALENDAR_EVENTS_ENDPOINT,
                json=body,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
            if res.status_code in (200, 201):
                event_id = res.json().get("id")
                appointment.google_calendar_event_id = event_id
                await appointment.save()
                logger.info("Successfully pushed appointment {} to Google Calendar (Event ID: {})", appointment.id, event_id)
                return event_id
            else:
                logger.warning("Failed to push event to Google Calendar for {}: {}", appointment.id, res.text)
    except Exception as exc:
        logger.error("Exception pushing appointment {} to Google Calendar: {}", appointment.id, exc)

    return None


async def delete_google_event(appointment: Appointment, astrologer: Astrologer) -> bool:
    """Removes an event from Google Calendar when appointment is cancelled."""
    gc = astrologer.google_calendar
    event_id = getattr(appointment, "google_calendar_event_id", None)
    if not gc.connected or not event_id:
        return False

    if not is_google_configured() or (gc.access_token and gc.access_token.startswith("mock_token_")):
        appointment.google_calendar_event_id = None
        await appointment.save()
        logger.info("Removed simulated Google Calendar event {} for appointment {}", event_id, appointment.id)
        return True

    token = await refresh_token_if_needed(astrologer)
    if not token:
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.delete(
                f"{GOOGLE_CALENDAR_EVENTS_ENDPOINT}/{event_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if res.status_code in (200, 204):
                appointment.google_calendar_event_id = None
                await appointment.save()
                logger.info("Deleted Google Calendar event {} for appointment {}", event_id, appointment.id)
                return True
    except Exception as exc:
        logger.error("Exception deleting Google event {} for {}: {}", event_id, appointment.id, exc)

    return False


async def disconnect_google_calendar(astrologer: Astrologer) -> None:
    """Disconnects Google Calendar integration and clears external blocks."""
    from app.models.astrologer import GoogleCalendarSync

    astrologer.google_calendar = GoogleCalendarSync(connected=False)
    await astrologer.save()
    logger.info("Disconnected Google Calendar for astrologer {}", astrologer.id)


def uuid_hex() -> str:
    import uuid
    return uuid.uuid4().hex[:12]

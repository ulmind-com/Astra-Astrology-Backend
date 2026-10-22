"""Exact UTC offset for a birth place and birth instant.

Replaces the previous `round(lon / 15) / 2` guess, which produced offsets that do
not exist (London, Ontario resolved to UTC-5.5) and forced every point inside a
crude 68E-97.5E box to +05:30, swallowing Bangladesh (+06:00), Nepal (+05:45),
Bhutan (+06:00), Pakistan (+05:00) and Myanmar (+06:30).

Offsets are resolved in two steps:

  1. latitude/longitude -> IANA zone name, via timezonefinder's offline polygon set.
     No network call, so this cannot fail or stall on a third-party geocoder.
  2. zone name + birth instant -> exact offset, via zoneinfo and the system tz
     database. This is what makes historical births correct: the tz database carries
     every transition a zone has been through, so a birth in Kolkata resolves to
     +05:53:20 (Howrah Mean Time) before 1870, +05:21:10 (Madras Mean Time) to 1906,
     +05:30 after, and +06:30 through the 1942-1945 wartime advance. Likewise London
     gets BST in summer and GMT in winter, New York EDT or EST, and so on.

A birth time is a local wall-clock reading, so the offset must be looked up at that
local time, not at UTC. Two wall-clock readings each year are ambiguous or
non-existent where DST shifts; `fold` is pinned so the result is deterministic, and
the caller is told which case it hit.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from loguru import logger

try:
    from timezonefinder import TimezoneFinder

    _FINDER: TimezoneFinder | None = TimezoneFinder()
except Exception as exc:  # pragma: no cover - import guard only
    _FINDER = None
    logger.warning(
        f"timezonefinder unavailable ({exc}); birth-place timezone lookup will fall "
        "back to the caller-supplied offset."
    )


@dataclass(frozen=True)
class ResolvedTimezone:
    """The offset to apply, and an audit trail of how it was arrived at."""

    offset_hours: float
    zone_name: str | None
    abbreviation: str | None
    source: str
    is_dst: bool
    note: str | None = None

    @property
    def offset_label(self) -> str:
        total = int(round(self.offset_hours * 3600))
        sign = "+" if total >= 0 else "-"
        total = abs(total)
        return f"UTC{sign}{total // 3600:02d}:{(total % 3600) // 60:02d}"


def zone_for_coordinates(latitude: float, longitude: float) -> str | None:
    """IANA zone name containing a point, or None over open ocean / no data."""
    if _FINDER is None:
        return None
    try:
        return _FINDER.timezone_at(lat=latitude, lng=longitude) or _FINDER.timezone_at_land(
            lat=latitude, lng=longitude
        )
    except Exception as exc:
        logger.warning(f"timezone lookup failed for ({latitude}, {longitude}): {exc}")
        return None


def offset_for_zone_at(
    zone_name: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    second: int = 0,
) -> ResolvedTimezone:
    """Exact offset a zone was running at one local wall-clock instant."""
    try:
        zone = ZoneInfo(zone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"unknown timezone {zone_name!r}") from exc

    naive = datetime(year, month, day, hour, minute, second)
    local = naive.replace(tzinfo=zone)
    utcoffset = local.utcoffset() or timedelta(0)

    note: str | None = None
    # A wall-clock reading that repeats (clocks went back) or never happened
    # (clocks went forward) is reported so the UI can say so instead of pretending
    # to a precision it does not have.
    alt = naive.replace(tzinfo=zone, fold=1)
    if (alt.utcoffset() or timedelta(0)) != utcoffset:
        note = (
            "This wall-clock time occurs twice locally because the clocks went back; "
            "the earlier of the two instants was used."
        )

    dst = local.dst() or timedelta(0)
    return ResolvedTimezone(
        offset_hours=utcoffset.total_seconds() / 3600.0,
        zone_name=zone_name,
        abbreviation=local.tzname(),
        source="iana",
        is_dst=dst != timedelta(0),
        note=note,
    )


def resolve(
    *,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    second: int = 0,
    latitude: float | None = None,
    longitude: float | None = None,
    zone_name: str | None = None,
    fallback_offset_hours: float | None = None,
) -> ResolvedTimezone:
    """Best available offset for a birth, preferring exactness over convenience.

    Order of preference:
      1. an explicit IANA zone name, resolved at the birth instant;
      2. the zone the birth coordinates fall in, resolved at the birth instant;
      3. the offset the caller supplied, used as given.

    An explicit zone name wins over coordinates so an astrologer correcting a
    mis-geocoded birthplace is not overridden. The caller-supplied offset is last
    because it is the only one that cannot account for DST or historical changes.
    """
    if zone_name:
        try:
            return offset_for_zone_at(zone_name, year, month, day, hour, minute, second)
        except ValueError:
            logger.warning(f"ignoring unusable timezone name {zone_name!r}")

    if latitude is not None and longitude is not None:
        found = zone_for_coordinates(latitude, longitude)
        if found:
            try:
                return offset_for_zone_at(found, year, month, day, hour, minute, second)
            except ValueError:
                logger.warning(f"coordinate lookup produced unusable zone {found!r}")

    if fallback_offset_hours is not None:
        return ResolvedTimezone(
            offset_hours=fallback_offset_hours,
            zone_name=None,
            abbreviation=None,
            source="manual",
            is_dst=False,
            note=(
                "Offset taken as supplied. No timezone could be derived from the birth "
                "place, so daylight saving and historical changes are not accounted for."
            ),
        )

    # Nothing usable at all. IST keeps the calculator serving the audience it was
    # built for rather than failing, and the note makes the assumption visible.
    return ResolvedTimezone(
        offset_hours=5.5,
        zone_name="Asia/Kolkata",
        abbreviation="IST",
        source="default",
        is_dst=False,
        note=(
            "No birth place or offset was supplied, so Indian Standard Time was assumed. "
            "Set the birth place to get an exact offset."
        ),
    )

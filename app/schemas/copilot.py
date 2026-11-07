"""Schemas for the astrologer's live Co-Pilot panel.

Everything here is read-only and derived: nothing in this file is stored. The
panel exists to save the astrologer from looking a chart up mid-conversation,
so the shapes are deliberately flat and small.
"""

from pydantic import BaseModel, Field


class CoPilotDashaPeriod(BaseModel):
    """One running Vimshottari period."""

    lord: str = Field(description="The ruling planet, in English, e.g. 'Jupiter'")
    lord_label: str = Field(description="The same planet in the requested language")
    starts_on: str = Field(description="DD-MM-YYYY")
    ends_on: str = Field(description="DD-MM-YYYY")
    percent_complete: float = Field(ge=0, le=100)
    days_remaining: int = Field(ge=0)


class CoPilotSadeSati(BaseModel):
    """Saturn's position relative to the natal Moon, right now."""

    is_active: bool = Field(description="True during Sade Sati or either Dhaiya")
    phase_code: str = Field(description="rising | peak | setting | kantaka | ashtama | none")
    phase_title: str
    impact_level: str = Field(description="high | medium | favorable")
    saturn_sign: str
    saturn_house_from_moon: int = Field(ge=1, le=12)
    description: str
    remedy_summary: str


class CoPilotRemedyFocus(BaseModel):
    """The one planet to speak about, and what to prescribe for it."""

    planet: str = Field(description="In English, e.g. 'Saturn'")
    planet_label: str = Field(description="The same planet in the requested language")
    reason: str = Field(description="Why this planet and not another, in the requested language")
    remedies: list[str] = Field(default_factory=list)
    beej_mantra: str = ""
    deity: str = ""
    lucky_day: str = ""
    # Only the seven classical planets have a stone; Rahu and Ketu leave these empty.
    gemstone: str = ""
    gemstone_metal: str = ""
    gemstone_finger: str = ""
    gemstone_day: str = ""


class CoPilotPlanetPosition(BaseModel):
    """Vedic planetary placement for the astrologer's quick cheat-sheet."""

    name: str = Field(description="Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu")
    label: str = Field(description="Localized planet name")
    sign: str = Field(description="Aries, Taurus, etc.")
    sign_label: str = Field(description="Localized sign name")
    house: int = Field(ge=1, le=12, description="Vedic Bhava (1 to 12)")
    degree_formatted: str = Field(default="", description="e.g. 14° 22'")
    is_retrograde: bool = False


class CoPilotBirthDetailsInput(BaseModel):
    """Input payload from astrologer to update or rectify client birth details in-session."""

    date_of_birth: str = Field(description="YYYY-MM-DD or DD-MM-YYYY")
    time_of_birth: str | None = Field(default=None, description="HH:MM (24-hour local time)")
    is_time_known: bool = True
    place: str = Field(min_length=2, max_length=200, description="Birthplace city or district")
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None
    timezone_offset: float | None = None


class CoPilotSummary(BaseModel):
    """What the panel shows for one session.

    `is_ready` is false when the client's saved birth details cannot produce a
    chart. Nothing is guessed in that case: an astrologer repeating a dasha
    taken from a placeholder birth date would be worse than an empty panel.
    """

    session_id: str
    client_name: str
    language: str

    is_ready: bool
    unavailable_reason: str = ""

    # False when the client never gave a birth time. The Moon moves about half
    # a degree an hour, so the dasha below is then only indicative and the
    # panel must say so rather than let it be read out as fact.
    is_birth_time_known: bool = True
    accuracy_note: str = ""

    ascendant: str = ""
    ascendant_degree: str = ""
    birth_date_str: str = ""
    birth_time_str: str = ""
    birth_place_str: str = ""

    moon_sign: str = ""
    nakshatra: str = ""

    planets: list[CoPilotPlanetPosition] = Field(default_factory=list)

    mahadasha: CoPilotDashaPeriod | None = None
    antardasha: CoPilotDashaPeriod | None = None
    sade_sati: CoPilotSadeSati | None = None
    remedy_focus: CoPilotRemedyFocus | None = None

    computed_at: str = Field(default="", description="UTC ISO-8601, when this was calculated")

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

    moon_sign: str = ""
    nakshatra: str = ""

    mahadasha: CoPilotDashaPeriod | None = None
    antardasha: CoPilotDashaPeriod | None = None
    sade_sati: CoPilotSadeSati | None = None
    remedy_focus: CoPilotRemedyFocus | None = None

    computed_at: str = Field(default="", description="UTC ISO-8601, when this was calculated")

"""Dosha assessment, defined once and shared by every feature.

WHY THIS MODULE EXISTS
----------------------
Manglik was implemented separately in `kundli_service.py` and
`kundli_matching_service.py`. The two copies happened to agree, but nothing kept
them in step, and a tester hit exactly the failure that invites: one page of the
site calling them Manglik while another did not. Defining the rule once removes
the class of bug rather than the instance.

THE RULE, AND WHERE IT COMES FROM
---------------------------------
The client supplied a reference matchmaking report
(`Resource Documents/_extracted/matchmaking-sample-report.txt`) which states the
definition they expect, verbatim:

    "In the boy or the girls horoscope when Mars, Sun, Saturn, Rahu Or Ketu is in
     ascendant, fourth house, seventh house, eighth house or twelth house then it
     is called Manglik dosh."

and then lists the effect of Mars in the 1st, 2nd, 4th, 7th, 8th and 12th.

Two things follow that the previous implementation got wrong:

1. It tested **Mars alone**. The client's definition covers five planets - Mars,
   Sun, Saturn, Rahu and Ketu.
2. The client's report grades the dosha as a **strength**, not a yes/no. Its two
   worked charts come out at 10.5% and 16%, and at 10.5% it concludes in so many
   words "Therefore, you are not manglik." A bare boolean reports those same two
   charts as afflicted, which is precisely the complaint that prompted this work.

The report also separates the contributing factors into "Based On House" and
"Based On Aspects", so both are computed here and both are returned.

WHAT COULD NOT BE DERIVED
-------------------------
The reference prints a percentage but not the weights behind it, and two worked
charts cannot determine a per-planet, per-house weighting - the first has nine
contributing factors and scores 10.5%, the second has eleven and scores 16%, so it
is not a count. The weighting below is therefore **ours**, built to be transparent
and explainable rather than to reproduce their number, and `weighting_is_client_sourced`
is returned as False so no caller can mistake it for theirs. See the open question
raised in RESOURCES-MASTER.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Lang = Literal["en", "bn", "hi"]

# The client's definition names these five. [matchmaking-sample-report.txt p.8]
DOSHA_PLANETS = ("Mars", "Sun", "Saturn", "Rahu", "Ketu")

# The definition names 1, 4, 7, 8 and 12; the effects section that follows it also
# covers the 2nd, which is the common reading, so the 2nd is included and weighted
# lower than the houses the definition states outright.
DOSHA_HOUSES = (1, 2, 4, 7, 8, 12)

# Relative weight of an occupying planet. Mars is the graha the dosha is named for
# and carries the most; the nodes and the two malefic luminaries carry less.
PLANET_WEIGHT = {"Mars": 1.0, "Saturn": 0.55, "Rahu": 0.5, "Ketu": 0.5, "Sun": 0.35}

# Relative weight of the house. The 7th and 8th bear most directly on marriage and
# longevity of the union; the 2nd is the house the client's own definition omits.
HOUSE_WEIGHT = {7: 1.0, 8: 0.9, 1: 0.85, 4: 0.7, 12: 0.7, 2: 0.45}

# An aspect onto an afflicted house counts for less than occupying it. The client's
# report lists the two separately and treats occupation as the stronger signal.
ASPECT_SCALE = 0.45

# Houses counted from the Moon are assessed as well as from the lagna, at a lower
# weight: the classical rule is lagna-first, with the Moon as corroboration.
FROM_MOON_SCALE = 0.6

# Divisor that turns summed factor weight into a percentage. See assess_manglik.
SCALE_DIVISOR = 22.0

# Verdict bands. The client's report calls 10.5% "very minor ... therefore you are
# not manglik" and 16% "present, however it is less effective", which puts the
# boundary between them and a second boundary well above.
BAND_NONE = 12.0
BAND_MILD = 25.0
BAND_MODERATE = 45.0

# Special Vedic aspects, as houses counted forward from the planet's own position.
# Every graha aspects the 7th from itself; these are the additional ones.
SPECIAL_ASPECTS = {
    "Mars": (4, 8),
    "Saturn": (3, 10),
    "Jupiter": (5, 9),
    "Rahu": (5, 9),
    "Ketu": (5, 9),
}

SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]

# Sign indices, 0 = Aries.
ARIES, TAURUS, GEMINI, CANCER, LEO, VIRGO = 0, 1, 2, 3, 4, 5
LIBRA, SCORPIO, SAGITTARIUS, CAPRICORN, AQUARIUS, PISCES = 6, 7, 8, 9, 10, 11


@dataclass
class DoshaFactor:
    """One thing in the chart that contributes to the dosha."""

    planet: str
    house: int
    basis: Literal["occupies", "aspects"]
    reference: Literal["lagna", "moon"]
    weight: float

    def describe(self) -> str:
        where = "from the ascendant" if self.reference == "lagna" else "from the Moon"
        verb = "is placed in" if self.basis == "occupies" else "aspects"
        return f"{self.planet} {verb} house {self.house} {where}"


@dataclass
class ManglikResult:
    is_manglik: bool
    severity: Literal["none", "mild", "moderate", "strong"]
    percentage: float
    factors: list[DoshaFactor] = field(default_factory=list)
    cancellations: list[str] = field(default_factory=list)
    summary: str = ""
    weighting_is_client_sourced: bool = False

    def factor_lines(self) -> list[str]:
        return [f.describe() for f in self.factors]


def _house_of(sign_index: int, reference_sign_index: int) -> int:
    """Whole-sign house number, the frame Vedic dosha rules assume."""
    return ((sign_index - reference_sign_index) % 12) + 1


def _aspected_houses(planet: str, planet_sign: int, reference_sign: int) -> set[int]:
    """Houses a planet casts a Vedic aspect onto, counted from a reference sign."""
    offsets = {7, *SPECIAL_ASPECTS.get(planet, ())}
    return {_house_of((planet_sign + offset - 1) % 12, reference_sign) for offset in offsets}


def _cancellations(
    planet_signs: dict[str, int],
    asc_sign: int,
    mars_house_lagna: int,
) -> list[str]:
    """Classical Manglik Bhanga conditions that are actually present.

    Only conditions this chart satisfies are returned, so the explanation shown to
    the user names the real reason rather than a stock sentence. The previous
    implementation printed "Mars is neutralized through Cancer debilitation &
    Kendra Jupiter aspect" on every chart, including charts where neither was true
    and including charts it had just declared afflicted.
    """
    found: list[str] = []
    mars_sign = planet_signs.get("Mars")
    if mars_sign is None:
        return found

    # Mars in its own sign or exalted does not afflict.
    if mars_sign in (ARIES, SCORPIO):
        found.append("Mars is in its own sign, so the affliction does not take effect.")
    elif mars_sign == CAPRICORN:
        found.append("Mars is exalted in Capricorn, so the affliction does not take effect.")

    # House-specific sign exemptions, the standard set.
    exemptions = {
        1: (ARIES, SCORPIO, CANCER, CAPRICORN),
        2: (GEMINI, VIRGO),
        4: (ARIES, SCORPIO),
        7: (CANCER, CAPRICORN),
        8: (CANCER, CAPRICORN),
        12: (TAURUS, LIBRA),
    }
    allowed = exemptions.get(mars_house_lagna, ())
    if mars_sign in allowed:
        found.append(
            f"Mars sits in house {mars_house_lagna} in a sign that is exempt there, "
            "so the affliction is not counted."
        )

    # Jupiter's aspect on Mars, or conjunction with it, is the classical relief.
    # The previous rule cancelled whenever Jupiter merely occupied a kendra from the
    # ascendant, which is true of roughly a third of all charts and cleared genuine
    # afflictions wholesale.
    jupiter_sign = planet_signs.get("Jupiter")
    if jupiter_sign is not None:
        if jupiter_sign == mars_sign:
            found.append("Jupiter is conjunct Mars, which relieves the affliction.")
        else:
            jupiter_aspects = {
                (jupiter_sign + offset - 1) % 12 for offset in (7, 5, 9)
            }
            if mars_sign in jupiter_aspects:
                found.append("Jupiter aspects Mars, which relieves the affliction.")

    return found


def assess_manglik(
    planet_signs: dict[str, int],
    ascendant_sign: int,
    moon_sign: int,
    lang: Lang = "en",
) -> ManglikResult:
    """Grade the Manglik dosha for one chart.

    `planet_signs` maps a graha name to its sign index, 0 = Aries.
    """
    factors: list[DoshaFactor] = []

    for reference, ref_sign, scale in (
        ("lagna", ascendant_sign, 1.0),
        ("moon", moon_sign, FROM_MOON_SCALE),
    ):
        for planet in DOSHA_PLANETS:
            sign = planet_signs.get(planet)
            if sign is None:
                continue

            house = _house_of(sign, ref_sign)
            if house in DOSHA_HOUSES:
                factors.append(
                    DoshaFactor(
                        planet=planet,
                        house=house,
                        basis="occupies",
                        reference=reference,  # type: ignore[arg-type]
                        weight=PLANET_WEIGHT[planet] * HOUSE_WEIGHT[house] * scale,
                    )
                )

            for aspected in _aspected_houses(planet, sign, ref_sign):
                if aspected in DOSHA_HOUSES and aspected != house:
                    factors.append(
                        DoshaFactor(
                            planet=planet,
                            house=aspected,
                            basis="aspects",
                            reference=reference,  # type: ignore[arg-type]
                            weight=PLANET_WEIGHT[planet]
                            * HOUSE_WEIGHT[aspected]
                            * ASPECT_SCALE
                            * scale,
                        )
                    )

    raw = sum(f.weight for f in factors)
    # Calibrated against the client's two reference charts. Their report scores them
    # 10.5% and 16%, calling the first "not manglik" and the second "present,
    # however it is less effective". The divisor is set so both land in the band
    # their report's own wording puts them in. It is a calibration to their
    # verdicts, not a reconstruction of their arithmetic - see the module docstring.
    percentage = min(100.0, (raw / SCALE_DIVISOR) * 100.0)

    mars_sign = planet_signs.get("Mars", ascendant_sign)
    mars_house_lagna = _house_of(mars_sign, ascendant_sign)
    cancellations = _cancellations(planet_signs, ascendant_sign, mars_house_lagna)

    # Each cancellation takes a quarter off, so several together can clear a chart
    # while one alone only softens it.
    if cancellations:
        percentage *= max(0.25, 1.0 - 0.25 * len(cancellations))

    percentage = round(percentage, 1)

    if percentage < BAND_NONE:
        severity: Literal["none", "mild", "moderate", "strong"] = "none"
    elif percentage < BAND_MILD:
        severity = "mild"
    elif percentage < BAND_MODERATE:
        severity = "moderate"
    else:
        severity = "strong"

    is_manglik = severity != "none"

    summaries = {
        "none": {
            "en": "The Manglik influence in this chart is too slight to count. This chart is not Manglik.",
            "bn": "এই কুণ্ডলীতে মাঙ্গলিক প্রভাব এতই সামান্য যে তা ধর্তব্য নয়। এই কুণ্ডলী মাঙ্গলিক নয়।",
            "hi": "इस कुंडली में मांगलिक प्रभाव इतना अल्प है कि गणनीय नहीं। यह कुंडली मांगलिक नहीं है।",
        },
        "mild": {
            "en": "A Manglik influence is present but mild, and is usually addressed with ordinary remedies.",
            "bn": "মাঙ্গলিক প্রভাব রয়েছে তবে মৃদু, সাধারণ প্রতিকারেই তা প্রশমিত হয়।",
            "hi": "मांगलिक प्रभाव है किंतु मंद, सामान्य उपायों से ही शांत हो जाता है।",
        },
        "moderate": {
            "en": "A clear Manglik influence is present and is worth discussing with an astrologer before marriage.",
            "bn": "স্পষ্ট মাঙ্গলিক প্রভাব রয়েছে; বিবাহের পূর্বে জ্যোতিষীর সঙ্গে আলোচনা করা বাঞ্ছনীয়।",
            "hi": "स्पष्ट मांगलिक प्रभाव है; विवाह से पूर्व ज्योतिषी से परामर्श उचित है।",
        },
        "strong": {
            "en": "A strong Manglik influence is present across several placements.",
            "bn": "একাধিক অবস্থানে প্রবল মাঙ্গলিক প্রভাব রয়েছে।",
            "hi": "अनेक स्थितियों में प्रबल मांगलिक प्रभाव है।",
        },
    }

    return ManglikResult(
        is_manglik=is_manglik,
        severity=severity,
        percentage=percentage,
        factors=sorted(factors, key=lambda f: -f.weight),
        cancellations=cancellations,
        summary=summaries[severity].get(lang) or summaries[severity]["en"],
        weighting_is_client_sourced=False,
    )


def manglik_match(groom: ManglikResult, bride: ManglikResult, lang: Lang = "en") -> dict[str, Any]:
    """Compare two charts' Manglik standing.

    The client's reference states the principle plainly: when the dosha is cancelled
    on both sides, or absent on both, the match is unaffected.
    """
    both_clear = not groom.is_manglik and not bride.is_manglik
    both_manglik = groom.is_manglik and bride.is_manglik
    one_sided = groom.is_manglik != bride.is_manglik

    if both_clear:
        key = "both_clear"
    elif both_manglik:
        key = "both_manglik"
    else:
        key = "one_sided"

    text = {
        "both_clear": {
            "en": "Neither chart carries a Manglik affliction, so it has no bearing on this match.",
            "bn": "কোনো কুণ্ডলীতেই মাঙ্গলিক দোষ নেই, তাই এই মিলনে এর কোনো প্রভাব নেই।",
            "hi": "किसी भी कुंडली में मांगलिक दोष नहीं है, अतः इस मिलन पर इसका कोई प्रभाव नहीं।",
        },
        "both_manglik": {
            "en": "Both charts carry the affliction. Classically a Manglik pairing offsets itself, so it is not treated as an obstacle here.",
            "bn": "উভয় কুণ্ডলীতেই দোষ রয়েছে। শাস্ত্রমতে উভয়েই মাঙ্গলিক হলে দোষ পরস্পর প্রশমিত হয়, তাই এটি বাধা নয়।",
            "hi": "दोनों कुंडलियों में दोष है। शास्त्रानुसार दोनों मांगलिक होने पर दोष परस्पर शांत हो जाता है, अतः यह बाधा नहीं।",
        },
        "one_sided": {
            "en": "The affliction falls on one side only. An astrologer should weigh its strength against the rest of the match.",
            "bn": "দোষ কেবল একপক্ষে রয়েছে। জ্যোতিষী এর প্রাবল্য মিলনের অন্যান্য দিকের সঙ্গে বিচার করবেন।",
            "hi": "दोष केवल एक पक्ष में है। ज्योतिषी इसकी प्रबलता का मिलन के अन्य पक्षों के साथ विचार करेंगे।",
        },
    }[key]

    return {
        "status": key,
        "is_obstacle": one_sided,
        "groom_percentage": groom.percentage,
        "bride_percentage": bride.percentage,
        "summary": text.get(lang) or text["en"],
    }

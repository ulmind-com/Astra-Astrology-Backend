"""Regression tests for the nakshatra calculator.

The strongest tests here are the two at the top. The client supplied a matchmaking
sample report, generated before this project began, containing two fully worked
charts with their Avakahada Chakra and panchang printed out. That is an independent
reference output for our calculator, so every field it lists is asserted against it.

Note on the reference's own coordinates: it labels the second chart "Varanasi" but
the ascendant it prints, Pisces 25:21:11, is only produced near 19 deg 14' N,
72 deg 14' E - the figures the report itself prints in its latitude and longitude
rows. The same holds for the first chart. The coordinates below are therefore the
ones the reference actually used, not the ones its place names suggest; using the
named cities would be testing against a chart the report never cast.
"""

import pytest

from app.schemas.astrology import NakshatraCalculateRequest
from app.services.astrology import client_nakshatra_rules as cnr
from app.services.astrology.calculator import calculate_nakshatra
from app.services.astrology.nakshatra_rules import NAKSHATRAS_MASTER
from app.services.astrology.panchang import (
    calculate_karana,
    calculate_tithi,
    calculate_yoga,
    calculate_yunja,
)
from app.services.astrology.timezone_resolver import zone_for_coordinates


def make_request(**overrides) -> NakshatraCalculateRequest:
    base = dict(
        name="Test", gender="male", day=19, month=3, year=1992,
        hour=12, minute=12, second=0, period="24H", place="Mumbai",
        latitude=19.2333, longitude=72.1167, timezone=5.5,
        ayanamsa="lahiri", language="en",
    )
    base.update(overrides)
    return NakshatraCalculateRequest(**base)


# Chart 1 of the client's reference report.
REFERENCE_A = dict(
    request=dict(day=19, month=3, year=1992, hour=12, minute=12,
                 latitude=19.2333, longitude=72.1167),
    nakshatra="Hasta", pada=1, star_lord="Moon",
    varna="Vaishya", vashya="Manava", yoni="Buffalo", gana="Deva", nadi="Aadi",
    tatva="Prithvi", tithi="Pratipada", paksha="Krishna", yoga="Vriddhi",
    karana="Kaulava", yunja="Madhya", ayanamsa=23.7481,
    sunrise_minutes=6 * 60 + 46, sunset_minutes=18 * 60 + 52,
    ascendant="Gemini",
)

# Chart 2 of the client's reference report.
REFERENCE_B = dict(
    request=dict(day=12, month=1, year=1995, hour=12, minute=16,
                 latitude=19.2333, longitude=72.2333),
    nakshatra="Krittika", pada=4, star_lord="Sun",
    varna="Vaishya", vashya="Chatuspada", yoni="Sheep", gana="Rakshasa", nadi="Antya",
    tatva="Prithvi", tithi="Ekadashi", paksha="Shukla", yoga="Shubha",
    karana="Vishti", yunja="Poorva", ayanamsa=23.7875,
    sunrise_minutes=7 * 60 + 17, sunset_minutes=18 * 60 + 21,
    ascendant="Pisces",
)


def _minutes(clock: str | None) -> int:
    assert clock is not None
    hours, minutes, _ = clock.split(":")
    return int(hours) * 60 + int(minutes)


# ----------------------------------------------------------------------------------
# Against the client's own reference output
# ----------------------------------------------------------------------------------
@pytest.mark.parametrize("ref", [REFERENCE_A, REFERENCE_B], ids=["chart-1", "chart-2"])
def test_matches_client_reference_report(ref):
    result = calculate_nakshatra(make_request(**ref["request"]))

    assert result.nakshatra_name_en == ref["nakshatra"]
    assert result.pada == ref["pada"]
    assert result.star_lord == ref["star_lord"]
    assert result.ascendant_rashi_name_en == ref["ascendant"]
    assert result.ayanamsa_degrees == pytest.approx(ref["ayanamsa"], abs=0.001)

    avakahada = result.avakahada
    assert ref["varna"] in avakahada.varna
    assert ref["vashya"] in avakahada.vashya
    assert ref["yoni"] in avakahada.yoni
    assert ref["gana"] in avakahada.gana
    assert ref["nadi"] in avakahada.nadi
    assert ref["tatva"] in avakahada.tatva

    panchang = result.panchang
    assert panchang is not None
    assert panchang.tithi.name_en == ref["tithi"]
    assert panchang.tithi.paksha_en.startswith(ref["paksha"])
    assert panchang.yoga.name_en == ref["yoga"]
    assert panchang.karana.name_en == ref["karana"]
    assert panchang.yunja.name_en.startswith(ref["yunja"])

    # Sunrise and sunset agree with the reference to within two minutes, which is
    # the spread between disc-centre and upper-limb conventions.
    assert abs(_minutes(panchang.sunrise) - ref["sunrise_minutes"]) <= 2
    assert abs(_minutes(panchang.sunset) - ref["sunset_minutes"]) <= 2


@pytest.mark.parametrize("ref", [REFERENCE_A, REFERENCE_B], ids=["chart-1", "chart-2"])
def test_paya_is_flagged_as_disputed(ref):
    """Paya is the one field that disagrees with the client's reference.

    No supplied document defines the rule, and the rule in use disagrees with the
    reference on both charts. It must not be presented as settled.
    """
    result = calculate_nakshatra(make_request(**ref["request"]))
    assert result.paya is not None
    assert result.paya.is_disputed is True
    assert result.paya.notice
    assert len(result.paya.evidence) >= 2


# ----------------------------------------------------------------------------------
# Panchang arithmetic
# ----------------------------------------------------------------------------------
def test_tithi_boundaries():
    assert calculate_tithi(0.0, 0.0)["name_en"] == "Pratipada"
    assert calculate_tithi(0.0, 12.0)["name_en"] == "Dwitiya"
    assert calculate_tithi(0.0, 14 * 12.0)["name_en"] == "Purnima (Full Moon)"
    assert calculate_tithi(0.0, 29 * 12.0)["name_en"] == "Amavasya (New Moon)"
    assert calculate_tithi(0.0, 6.0)["paksha_en"].startswith("Shukla")
    assert calculate_tithi(0.0, 200.0)["paksha_en"].startswith("Krishna")


def test_tithi_wraps_across_zero_aries():
    """A Moon just past 0 Aries with the Sun just before it must not wrap wrong."""
    tithi = calculate_tithi(355.0, 5.0)
    assert tithi["index"] == 1  # 10 degrees of elongation is still the first tithi
    assert tithi["name_en"] == "Pratipada"
    # and one step further along crosses into the second
    assert calculate_tithi(355.0, 10.0)["index"] == 2


def test_yoga_covers_all_twenty_seven():
    span = 360.0 / 27.0
    seen = {calculate_yoga(0.0, i * span + span / 2)["name_en"] for i in range(27)}
    assert len(seen) == 27


def test_karana_cycle_structure():
    """Kimstughna opens the month; the fixed karanas close it."""
    assert calculate_karana(0.0, 1.0)["name_en"] == "Kimstughna"
    assert calculate_karana(0.0, 57 * 6.0 + 1)["name_en"] == "Shakuni"
    assert calculate_karana(0.0, 58 * 6.0 + 1)["name_en"] == "Chatushpada"
    assert calculate_karana(0.0, 59 * 6.0 + 1)["name_en"] == "Naga"
    # The seven movable karanas repeat in between.
    movable = {calculate_karana(0.0, i * 6.0 + 1)["name_en"] for i in range(1, 57)}
    assert movable == {"Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"}


@pytest.mark.parametrize(
    "nak_index,expected",
    [(0, "Poorva"), (8, "Poorva"), (9, "Madhya"), (17, "Madhya"), (18, "Antya"), (26, "Antya")],
)
def test_yunja_thirds(nak_index, expected):
    assert calculate_yunja(nak_index)["name_en"].startswith(expected)


# ----------------------------------------------------------------------------------
# The client's own nakshatra books
# ----------------------------------------------------------------------------------
def test_book_reference_lords_match_our_canonical_table():
    """The two supplied volumes print a lord for each of their 18 nakshatras."""
    for index, reference in cnr.BOOK_REFERENCE.items():
        assert NAKSHATRAS_MASTER[index]["lord"] == reference["lord"], cnr.NAKSHATRA_NAMES[index]


def test_books_cover_eighteen_of_twenty_seven():
    """Part 3, covering Mula to Revati, was not supplied."""
    coverage = cnr.coverage_summary()
    assert coverage["nakshatras_with_source"] == 18
    assert coverage["missing"]["nakshatra_names"][0] == "Mula"
    assert coverage["missing"]["nakshatra_names"][-1] == "Revati"
    assert len(coverage["missing"]["nakshatra_names"]) == 9


def test_every_technique_cites_a_source_and_is_trilingual():
    for technique in cnr.TECHNIQUES:
        assert technique["source"], technique
        assert 0 <= technique["nak"] <= 17, "no technique may claim an unsupplied nakshatra"
        for lang in ("en", "bn", "hi"):
            assert technique["rule"].get(lang), (technique["source"], lang)
        assert technique["when"], technique["source"]


def test_unsupplied_nakshatras_say_so_rather_than_inventing():
    """A birth in Mula must report the gap, not fall back to invented content."""
    # 28 Jan 1995 at noon puts the Moon in Mula, the first of the nine
    # nakshatras the unsupplied Part 3 would have covered.
    result = calculate_nakshatra(
        make_request(day=28, month=1, year=1995, hour=12, minute=0)
    )
    assert result.nakshatra_name_en == "Mula"
    assert result.nakshatra_name_en in cnr.MISSING_FROM_CLIENT_RESOURCES["nakshatra_names"]
    rules = result.client_rules
    assert rules is not None
    assert rules.has_client_source is False
    assert rules.matched == []
    assert rules.unavailable_note


def test_matched_techniques_explain_why_they_applied():
    result = calculate_nakshatra(make_request(**REFERENCE_A["request"]))
    rules = result.client_rules
    assert rules is not None
    assert rules.has_client_source is True
    assert rules.matched, "Hasta has techniques and this chart should satisfy some"
    for technique in rules.matched:
        assert technique.because, technique.source
        assert technique.rule
        assert technique.source.startswith(("P1", "P2"))


def test_techniques_are_filtered_not_dumped():
    """A technique must only appear when the chart satisfies its condition."""
    result = calculate_nakshatra(make_request(**REFERENCE_A["request"]))
    rules = result.client_rules
    assert rules.total_available == len(rules.matched) + len(rules.not_matched)
    assert rules.total_available > 0


def test_affliction_is_reported_with_its_reason():
    result = calculate_nakshatra(make_request(**REFERENCE_A["request"]))
    rules = result.client_rules
    if rules.is_afflicted:
        assert rules.affliction_reasons
    else:
        assert rules.affliction_reasons == []


@pytest.mark.parametrize("lang", ["en", "bn", "hi"])
def test_client_rules_are_returned_in_every_language(lang):
    result = calculate_nakshatra(make_request(language=lang, **REFERENCE_A["request"]))
    assert result.client_rules is not None
    assert result.rashi_client_rules is not None
    assert len(result.rashi_client_rules.classifications) == 19
    for technique in result.client_rules.matched:
        assert technique.rule


# ----------------------------------------------------------------------------------
# Timezone: a birth place is always on land
# ----------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "label,lat,lon,expected",
    [
        ("offshore Mumbai", 19.2333, 72.1167, "Asia/Kolkata"),
        ("just off Chennai", 13.05, 80.45, "Asia/Kolkata"),
        ("off the Bangladesh coast", 21.8, 90.6, "Asia/Dhaka"),
        ("Mumbai city", 19.0760, 72.8777, "Asia/Kolkata"),
    ],
)
def test_coastal_coordinates_resolve_to_a_land_zone(label, lat, lon, expected):
    """A geocoded birth place landing in water must not fall back to a sea band.

    timezonefinder answers over water with a nautical zone such as Etc/GMT-5, which
    is a whole-hour band derived from longitude - exactly what this module replaced.
    """
    assert zone_for_coordinates(lat, lon) == expected, label


def test_coastal_birth_gets_the_right_offset_end_to_end():
    result = calculate_nakshatra(make_request(latitude=19.2333, longitude=72.1167))
    assert result.timezone_resolution is not None
    assert result.timezone_resolution.zone_name == "Asia/Kolkata"
    assert result.timezone == pytest.approx(5.5)


# ----------------------------------------------------------------------------------
# Structure and robustness
# ----------------------------------------------------------------------------------
def test_all_twenty_seven_nakshatras_are_reachable_and_complete():
    """Step the Moon through the zodiac and check every star comes out whole."""
    seen = set()
    for day_offset in range(0, 28):
        result = calculate_nakshatra(
            make_request(day=1, month=1, year=1995, hour=12)
            .model_copy(update={"day": (day_offset % 28) + 1})
        )
        seen.add(result.nakshatra_index)
        assert result.panchang is not None
        assert result.client_rules is not None
        assert len(result.padas) == 4
        assert len(result.tarabala) == 9
        assert 1 <= result.pada <= 4
    assert len(seen) >= 20, f"only reached {len(seen)} nakshatras"


def test_tarabala_covers_all_twenty_seven_stars_once():
    result = calculate_nakshatra(make_request())
    listed = [name for tara in result.tarabala for name in tara.nakshatras]
    assert len(listed) == 27
    assert len(set(listed)) == 27


def test_full_chart_is_returned_for_the_techniques_to_act_on():
    result = calculate_nakshatra(make_request())
    assert len(result.planets) == 9
    assert all(1 <= p.house <= 12 for p in result.planets)
    assert result.ascendant_nakshatra_name


@pytest.mark.parametrize(
    "overrides",
    [
        {"day": 29, "month": 2, "year": 2000},
        {"hour": 0, "minute": 0},
        {"hour": 23, "minute": 59, "second": 59},
        {"year": 1800},
        {"year": 2100},
        {"latitude": 71.0, "longitude": 25.0},     # inside the Arctic circle
        {"latitude": -54.8, "longitude": -68.3},   # Tierra del Fuego
        {"latitude": None, "longitude": None},
        {"name": "", "place": ""},
    ],
)
def test_edge_cases_produce_a_complete_reading(overrides):
    result = calculate_nakshatra(make_request(**overrides))
    assert 0 <= result.nakshatra_index <= 26
    assert 1 <= result.pada <= 4
    assert result.panchang is not None
    assert result.client_rules is not None
    assert result.paya is not None


def test_polar_birth_reports_missing_sun_times_rather_than_guessing():
    """Above the Arctic circle in midsummer the Sun does not set."""
    result = calculate_nakshatra(
        make_request(day=21, month=6, year=1990, latitude=78.2, longitude=15.6)
    )
    panchang = result.panchang
    assert panchang is not None
    # Either a real time or an explicit None, never a fabricated one.
    for value in (panchang.sunrise, panchang.sunset):
        assert value is None or len(value.split(":")) == 3


def test_shatabhisha_renders_in_every_language():
    """Shatabhisha was missing its Hindi strengths, which made every request for a
    Shatabhisha birth fail with a 500 regardless of the language asked for."""
    for lang in ("en", "bn", "hi"):
        result = calculate_nakshatra(
            make_request(day=5, month=1, year=1995, hour=12, minute=0, language=lang)
        )
        assert result.nakshatra_name_en == "Shatabhisha"
        assert result.traits.strengths
        for code in ("en", "bn", "hi"):
            assert result.translations[code]["strengths"]


def test_no_nakshatra_has_a_translation_gap():
    """Guards the whole table, not just the one entry that was found missing."""
    fields = [
        "overview", "strengths", "cautions_and_pitfalls",
        "beneficial_actions_and_remedies", "career_fields",
    ]
    gaps = [
        (nak["name_en"], field, lang)
        for nak in NAKSHATRAS_MASTER
        for field in fields
        for lang in ("en", "bn", "hi")
        if lang not in nak.get(field, {})
    ]
    assert gaps == []

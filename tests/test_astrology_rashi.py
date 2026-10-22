"""Regression tests for the rashi calculator.

Each test here pins a defect that was found in the deployed calculator, so a
regression shows up as a failing test rather than as a wrong horoscope.
"""

import pytest

from app.schemas.astrology import RashiCalculateRequest
from app.services.astrology import client_rules
from app.services.astrology.calculator import calculate_rashi
from app.services.astrology.timezone_resolver import resolve

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def make_request(**overrides) -> RashiCalculateRequest:
    base = dict(
        name="Test",
        gender="male",
        day=10,
        month=3,
        year=1995,
        hour=14,
        minute=20,
        second=0,
        period="24H",
        place="Dhaka",
        latitude=23.8103,
        longitude=90.4125,
        timezone=5.5,
        ayanamsa="lahiri",
        house_system="placidus",
        chart_style="north_indian",
        language="en",
    )
    base.update(overrides)
    return RashiCalculateRequest(**base)


# ----------------------------------------------------------------------------------
# Astronomy: the positions themselves
# ----------------------------------------------------------------------------------
def test_matches_published_india_independence_chart():
    """15 Aug 1947, 00:01 IST, New Delhi: Taurus ascendant, Moon in Pushya."""
    result = calculate_rashi(
        make_request(
            day=15, month=8, year=1947, hour=0, minute=1,
            place="New Delhi", latitude=28.6139, longitude=77.2090,
        )
    )
    assert result.ascendant_rashi_name_en == "Taurus"
    assert result.rashi_name_en == "Cancer"
    assert result.nakshatra_name == "Pushya"
    assert result.nakshatra_pada == 1
    # Lahiri ayanamsa for 1947 is 23 degrees 07 minutes.
    assert 23.12 < result.ayanamsa_degrees < 23.13


def test_returns_all_nine_grahas():
    result = calculate_rashi(make_request())
    names = [p.name for p in result.planets]
    assert names == [
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ]


def test_rahu_and_ketu_are_exactly_opposite_and_retrograde():
    result = calculate_rashi(make_request())
    rahu = next(p for p in result.planets if p.name == "Rahu")
    ketu = next(p for p in result.planets if p.name == "Ketu")
    rahu_lon = rahu.sign_index * 30 + rahu.degree_in_sign
    ketu_lon = ketu.sign_index * 30 + ketu.degree_in_sign
    assert abs((ketu_lon - rahu_lon) % 360 - 180.0) < 1e-6
    assert rahu.is_retrograde and ketu.is_retrograde


# ----------------------------------------------------------------------------------
# Defect 1: the House System selector had no effect at all
# ----------------------------------------------------------------------------------
def test_house_system_changes_the_cusps():
    """Placidus, Koch and Equal must produce genuinely different cusps.

    The previous build computed real cusps then discarded them, assigning houses by
    whole sign regardless of the selection, so all four options returned identical
    charts.
    """
    cusps = {}
    for system in ("placidus", "koch", "equal", "whole_sign"):
        result = calculate_rashi(make_request(house_system=system))
        assert len(result.house_cusps) == 12
        cusps[system] = [c.longitude for c in result.house_cusps]

    assert cusps["placidus"] != cusps["koch"]
    assert cusps["placidus"] != cusps["equal"]
    assert cusps["equal"] != cusps["whole_sign"]
    # Whole-sign cusps always sit exactly on a sign boundary.
    assert all(abs(c % 30.0) < 1e-9 for c in cusps["whole_sign"])


def test_houses_are_derived_from_the_selected_cusps():
    result = calculate_rashi(make_request(house_system="placidus"))
    boundaries = [c.longitude for c in result.house_cusps]
    for planet in result.planets:
        longitude = planet.sign_index * 30 + planet.degree_in_sign
        start = boundaries[planet.house - 1]
        end = boundaries[planet.house % 12]
        span = (end - start) % 360.0 or 360.0
        assert (longitude - start) % 360.0 < span + 1e-6


def test_polar_birth_reports_house_system_substitution():
    """Placidus is undefined inside the polar circles; say so rather than pretend."""
    result = calculate_rashi(
        make_request(latitude=78.2, longitude=15.6, place="Longyearbyen")
    )
    assert any("undefined above 66" in w for w in result.calculation.warnings)


# ----------------------------------------------------------------------------------
# Defect 2: timezone was guessed from longitude
# ----------------------------------------------------------------------------------
def test_bangladesh_birth_uses_bangladesh_time():
    """The old 68E-97.5E box forced Dhaka to +05:30, which moved the sub-lord."""
    result = calculate_rashi(make_request())
    assert result.timezone_resolution.zone_name == "Asia/Dhaka"
    assert result.timezone == pytest.approx(6.0)
    assert result.timezone_resolution.source == "iana"


@pytest.mark.parametrize(
    "zone,lat,lon,expected",
    [
        ("Asia/Kolkata", 22.5726, 88.3639, 5.5),
        ("Asia/Dhaka", 23.8103, 90.4125, 6.0),
        ("Asia/Kathmandu", 27.7172, 85.3240, 5.75),
        ("Asia/Karachi", 24.8607, 67.0011, 5.0),
        ("Asia/Yangon", 16.8661, 96.1951, 6.5),
        ("Asia/Thimphu", 27.4728, 89.6390, 6.0),
    ],
)
def test_south_asian_neighbours_get_their_own_offsets(zone, lat, lon, expected):
    result = calculate_rashi(make_request(latitude=lat, longitude=lon))
    assert result.timezone_resolution.zone_name == zone
    assert result.timezone == pytest.approx(expected)


@pytest.mark.parametrize(
    "year,expected,label",
    [
        (1860, 5.888889, "Howrah Mean Time"),
        (1900, 5.352778, "Madras Mean Time"),
        (1930, 5.5, "IST"),
        (1944, 6.5, "wartime advance"),
        (1995, 5.5, "IST"),
    ],
)
def test_historical_india_offsets(year, expected, label):
    """A birth in Kolkata must use the offset actually in force that year."""
    result = calculate_rashi(
        make_request(year=year, latitude=22.5726, longitude=88.3639, place="Kolkata")
    )
    assert result.timezone == pytest.approx(expected, abs=1e-4), label


def test_daylight_saving_is_applied():
    summer = calculate_rashi(
        make_request(month=7, latitude=51.5074, longitude=-0.1278, place="London")
    )
    winter = calculate_rashi(
        make_request(month=1, latitude=51.5074, longitude=-0.1278, place="London")
    )
    assert summer.timezone == pytest.approx(1.0)
    assert winter.timezone == pytest.approx(0.0)
    assert summer.timezone_resolution.is_dst
    assert not winter.timezone_resolution.is_dst


def test_no_impossible_half_hour_offsets_in_north_america():
    """London, Ontario used to come back as UTC-5.5, which exists nowhere."""
    result = calculate_rashi(
        make_request(latitude=42.9837, longitude=-81.2497, place="London, Ontario")
    )
    assert result.timezone_resolution.zone_name == "America/Toronto"
    assert result.timezone in (-5.0, -4.0)


def test_explicit_zone_name_overrides_coordinates():
    """An astrologer correcting a mis-geocoded birthplace must not be overridden."""
    result = calculate_rashi(
        make_request(timezone_name="Asia/Kolkata", latitude=23.8103, longitude=90.4125)
    )
    assert result.timezone == pytest.approx(5.5)


def test_unknown_zone_name_falls_back_without_raising():
    result = calculate_rashi(make_request(timezone_name="Not/AZone"))
    assert result.timezone == pytest.approx(6.0)  # derived from the coordinates


def test_ambiguous_wall_clock_time_is_flagged():
    resolved = resolve(
        year=1995, month=10, day=29, hour=1, minute=30,
        latitude=40.7128, longitude=-74.0060,
    )
    assert resolved.note and "twice" in resolved.note


# ----------------------------------------------------------------------------------
# Defect 3: the KP sub-lord was cast on Lahiri while being labelled KP
# ----------------------------------------------------------------------------------
def test_ayanamsa_mismatch_is_disclosed_for_kp_sublord():
    lahiri = calculate_rashi(make_request(ayanamsa="lahiri"))
    assert any("Krishnamurti ayanamsa" in w for w in lahiri.calculation.warnings)

    kp = calculate_rashi(make_request(ayanamsa="krishnamurti"))
    assert not any("Krishnamurti ayanamsa" in w for w in kp.calculation.warnings)


def test_sub_lord_divisions_are_proportional_to_vimshottari_years():
    from app.services.astrology.rashi_rules import (
        DASHA_YEARS,
        TOTAL_DASHA_YEARS,
        calculate_kp_sub_lord,
    )

    span = 360.0 / 27.0
    # Ashwini is ruled by Ketu, so its nine subs run Ketu, Venus, Sun, ...
    order = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    accumulated = 0.0
    for lord in order:
        width = (DASHA_YEARS[lord] / TOTAL_DASHA_YEARS) * span
        midpoint = accumulated + width / 2
        assert calculate_kp_sub_lord("Ketu", midpoint) == lord
        accumulated += width
    assert accumulated == pytest.approx(span)


# ----------------------------------------------------------------------------------
# Defect 4: the rules shown were largely not the client's
# ----------------------------------------------------------------------------------
def test_every_client_classification_group_is_returned():
    result = calculate_rashi(make_request())
    assert result.client_rules is not None
    keys = {entry.key for entry in result.client_rules.classifications}
    assert keys == {
        "quality", "triplicity", "quadruplicity", "fruitfulness", "voice",
        "violent", "form", "double_bodied", "ascension", "hemisphere",
        "equinoctial_tropical", "dosha", "varna", "day_night", "rising",
        "footedness", "direction", "colour", "kalapurusha",
    }


def test_every_classification_cites_its_source():
    result = calculate_rashi(make_request())
    for entry in result.client_rules.classifications:
        assert entry.source, f"{entry.key} has no source citation"
        assert entry.definition, f"{entry.key} has no definition"


def test_ascendant_sign_also_gets_its_client_rules():
    result = calculate_rashi(make_request())
    assert result.ascendant_client_rules is not None
    assert result.ascendant_client_rules.index == result.ascendant_rashi_index


@pytest.mark.parametrize(
    "sign_index,expected",
    [
        (0, "Night"), (1, "Night"), (2, "Night"), (3, "Night"),
        (4, "Day"), (5, "Day"), (6, "Day"), (7, "Day"),
        (8, "Night"), (9, "Night"), (10, "Day"), (11, "Day"),
    ],
)
def test_day_night_matches_the_client_document(sign_index, expected):
    """01.pdf states twice: nishaa = Ar Ta Ge Cn Sg Cp, divaa = Le Vi Li Sc Aq Pi.

    The previous build derived this from the Western "masculine = diurnal" rule and
    got six of the twelve signs wrong.
    """
    profile = client_rules.get_sign_profile(sign_index, "en")
    value = next(
        e["value"] for e in profile["classifications"] if e["key"] == "day_night"
    )
    assert value.startswith(expected)


def test_polarity_no_longer_claims_a_day_night_value():
    """Gender and day/night are separate classifications in the client's document."""
    for sign_index in range(12):
        for lang in ("en", "bn", "hi"):
            from app.services.astrology.rashi_translations import get_rashi_translations

            polarity = get_rashi_translations(sign_index, lang)["all"][lang]["polarity"]
            assert "Day Sign" not in polarity
            assert "Night Sign" not in polarity
            assert "দিবা" not in polarity
            assert "রাত্রি" not in polarity
            assert "दिवा" not in polarity
            assert "रात्रि" not in polarity


def test_client_rasi_colour_is_available_and_distinct_from_lucky_colour():
    result = calculate_rashi(
        make_request(day=1, month=7, year=1990)  # whichever sign, both must be present
    )
    colour = next(
        e.value for e in result.client_rules.classifications if e.key == "colour"
    )
    assert colour
    assert colour != result.traits.lucky_color


def test_guna_contradiction_is_surfaced_not_resolved():
    """Four signs are classified differently on p.5 and p.8 of the client's 01.pdf.

    Capricorn and Aquarius are tamasik in both statements, so they are not disputed.
    """
    disputed = [
        i for i in range(12) if client_rules.get_sign_profile(i, "en")["guna"]["is_disputed"]
    ]
    names = [client_rules.SIGN_ORDER[i] for i in disputed]
    assert sorted(names) == sorted(
        ["Aries", "Gemini", "Virgo", "Scorpio"]
    )
    profile = client_rules.get_sign_profile(0, "en")
    assert len(profile["guna"]["readings"]) == 2
    assert profile["guna"]["notice"]


def test_client_group_assignments_match_the_documents_own_lists():
    """01.pdf states each group twice: inline per sign, and as an explicit list."""
    expected = {
        "triplicity": {
            "fire": ["Aries", "Leo", "Sagittarius"],
            "earth": ["Taurus", "Virgo", "Capricorn"],
            "air": ["Gemini", "Libra", "Aquarius"],
            "water": ["Cancer", "Scorpio", "Pisces"],
        },
        "quadruplicity": {
            "movable": ["Aries", "Cancer", "Libra", "Capricorn"],
            "fixed": ["Taurus", "Leo", "Scorpio", "Aquarius"],
            "dual": ["Gemini", "Virgo", "Sagittarius", "Pisces"],
        },
        "fruitfulness": {
            "fruitful": ["Cancer", "Scorpio", "Pisces"],
            "barren": ["Aries", "Gemini", "Leo", "Virgo"],
        },
        "voice": {
            "voice": ["Gemini", "Libra", "Aquarius"],
            "mute": ["Cancer", "Scorpio", "Pisces"],
        },
        "violent": {"violent": ["Aries", "Scorpio"]},
        "double_bodied": {"double_bodied": ["Gemini", "Sagittarius", "Pisces"]},
        "varna": {
            "brahmin": ["Cancer", "Scorpio", "Pisces"],
            "kshatriya": ["Aries", "Leo", "Sagittarius"],
            "vaishya": ["Taurus", "Virgo", "Capricorn"],
            "shudra": ["Gemini", "Libra", "Aquarius"],
        },
        "dosha": {
            "pitta": ["Aries", "Leo", "Sagittarius"],
            "vaata": ["Taurus", "Virgo", "Capricorn"],
            "kapha": ["Cancer", "Scorpio", "Pisces"],
            "mixed_dosha": ["Gemini", "Libra", "Aquarius"],
        },
        "rising": {
            "seershodaya": ["Gemini", "Leo", "Virgo", "Libra", "Scorpio", "Aquarius"],
            "prishthodaya": ["Aries", "Taurus", "Cancer", "Sagittarius", "Capricorn"],
            "ubhayodaya": ["Pisces"],
        },
        "ascension": {
            "long_asc": ["Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"],
            "short_asc": ["Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini"],
        },
        "footedness": {
            "odd_footed": ["Aries", "Taurus", "Gemini", "Libra", "Scorpio", "Sagittarius"],
            "even_footed": ["Cancer", "Leo", "Virgo", "Capricorn", "Aquarius", "Pisces"],
        },
        "direction": {
            "east": ["Aries", "Leo", "Sagittarius"],
            "south": ["Taurus", "Virgo", "Capricorn"],
            "west": ["Gemini", "Libra", "Aquarius"],
            "north": ["Cancer", "Scorpio", "Pisces"],
        },
    }
    for group, buckets in expected.items():
        for value, signs in buckets.items():
            got = [
                client_rules.SIGN_ORDER[i]
                for i, row in enumerate(client_rules._A)
                if row[group] == value
            ]
            assert sorted(got) == sorted(signs), f"{group}/{value}"


def test_sign_lords_match_the_client_table():
    """12 Rashis and Their Planetary Lords.pdf: traditional lords only."""
    expected = [
        "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
        "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
    ]
    assert [client_rules.get_sign_lord(i) for i in range(12)] == expected


def test_kp_reference_carries_the_clients_five_rules_and_twelve_houses():
    result = calculate_rashi(make_request())
    assert len(result.kp_reference["basic_rules"]) == 5
    assert len(result.kp_reference["house_significations"]) == 12
    joined = " ".join(result.kp_reference["basic_rules"])
    assert "cuspal sub-lord" in joined.lower()
    assert "12th house" in joined


# ----------------------------------------------------------------------------------
# Defect 5: Hindi names were Latin transliteration
# ----------------------------------------------------------------------------------
def test_hindi_sign_names_are_devanagari():
    for sign_index in range(12):
        name = client_rules.SIGN_NAMES[sign_index]["hi"]
        assert any("ऀ" <= ch <= "ॿ" for ch in name), name


def test_response_uses_devanagari_and_bengali_names():
    result = calculate_rashi(make_request())
    assert any("ऀ" <= ch <= "ॿ" for ch in result.rashi_name_hi)
    assert any("ঀ" <= ch <= "৿" for ch in result.rashi_name_bn)


# ----------------------------------------------------------------------------------
# Trilingual integrity
# ----------------------------------------------------------------------------------
@pytest.mark.parametrize("lang", ["en", "bn", "hi"])
def test_all_languages_return_complete_client_rules(lang):
    result = calculate_rashi(make_request(language=lang))
    assert len(result.client_rules.classifications) == 19
    for entry in result.client_rules.classifications:
        assert entry.label and entry.value and entry.definition
    assert result.client_rules.places
    assert result.client_rules.trait_keywords


# ----------------------------------------------------------------------------------
# Robustness: nothing may crash the worker
# ----------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "overrides",
    [
        {"day": 29, "month": 2, "year": 2000},             # leap day
        {"hour": 0, "minute": 0, "second": 0},             # midnight
        {"hour": 23, "minute": 59, "second": 59},          # just before midnight
        {"hour": 12, "period": "AM"},                      # 12 AM
        {"hour": 12, "period": "PM"},                      # 12 PM
        {"year": 1800},                                    # earliest allowed
        {"year": 2100},                                    # latest allowed
        {"latitude": 90.0, "longitude": 0.0},              # north pole
        {"latitude": -90.0, "longitude": 0.0},             # south pole
        {"latitude": 0.0, "longitude": 180.0},             # antimeridian
        {"latitude": 0.0, "longitude": -180.0},
        {"latitude": None, "longitude": None},             # no coordinates at all
        {"name": "", "place": ""},                         # empty strings
        {"name": "A" * 200},                               # long name
        {"timezone": -12.0},                               # extreme offsets
        {"timezone": 14.0},
    ],
)
def test_edge_case_inputs_produce_a_valid_chart(overrides):
    result = calculate_rashi(make_request(**overrides))
    assert 0 <= result.rashi_index <= 11
    assert 0 <= result.nakshatra_index <= 26
    assert 1 <= result.nakshatra_pada <= 4
    assert 0.0 <= result.moon_sidereal_longitude < 360.0
    assert 0.0 <= result.ascendant_longitude < 360.0
    assert len(result.planets) == 9
    assert len(result.house_cusps) == 12
    assert all(1 <= p.house <= 12 for p in result.planets)
    assert result.client_rules is not None


@pytest.mark.parametrize("ayanamsa", [
    "lahiri", "bv_raman", "krishnamurti", "yukteshwar",
    "suryasiddhanta", "true_pushya", "true_mula",
])
def test_every_ayanamsa_option_works(ayanamsa):
    result = calculate_rashi(make_request(ayanamsa=ayanamsa))
    assert result.ayanamsa_name
    assert 0 < result.ayanamsa_degrees < 30
    assert result.calculation.ayanamsa_key == ayanamsa


def test_dateline_crossing_does_not_shift_the_day():
    """A birth just after local midnight near +14 must not land on the wrong date."""
    result = calculate_rashi(
        make_request(
            hour=0, minute=30, latitude=-13.0, longitude=-172.0, place="Apia",
        )
    )
    assert result.birth_date_formatted.startswith("10-03-1995")


def test_calculation_meta_is_always_present():
    result = calculate_rashi(make_request())
    meta = result.calculation
    assert meta.engine == "swiss_ephemeris"
    assert meta.node_type == "mean"
    assert meta.julian_day_ut > 2_000_000
    assert meta.house_system_key == "placidus"


# ----------------------------------------------------------------------------------
# Input bounds. The documented ranges were never enforced, so latitude 999 produced
# a chart from meaningless geometry instead of a validation error.
# ----------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "field,value",
    [
        ("latitude", 999.0),
        ("latitude", -91.0),
        ("longitude", 400.0),
        ("longitude", -181.0),
        ("timezone", 99.0),
        ("timezone", -13.0),
        ("month", 13),
        ("day", 32),
        ("hour", 24),
        ("minute", 60),
        ("year", 1700),
        ("year", 2200),
    ],
)
def test_out_of_range_input_is_rejected(field, value):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        make_request(**{field: value})


def test_impossible_calendar_date_is_rejected_cleanly():
    """31 February must raise a ValueError the API turns into a 422, not a 500."""
    with pytest.raises(ValueError):
        calculate_rashi(make_request(day=31, month=2))

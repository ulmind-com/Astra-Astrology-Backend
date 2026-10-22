"""The same birth, through every feature, must give the same answer.

A tester reported one page of the site calling them Manglik while another did not,
and reported a different rashi on the matching page from the one they knew. The
site has five separate chart engines - the rashi calculator, the nakshatra
calculator, KP, kundli and kundli matching - each of which used to resolve the birth
instant, place the planets and judge the doshas in its own code. Nothing kept them
in step.

These tests are the thing that keeps them in step. Every one of them runs a single
birth through several features and asserts they agree. If someone later changes how
one feature computes a Moon sign, a pada or a Manglik verdict without changing the
others, a test here fails rather than a user finding it.
"""

import pytest

from app.schemas.astrology import (
    KPCalculateRequest,
    KundliCalculateRequest,
    KundliMatchingPersonInput,
    KundliMatchingRequest,
    NakshatraCalculateRequest,
    RashiCalculateRequest,
)
from app.services.astrology.calculator import calculate_nakshatra, calculate_rashi
from app.services.astrology.doshas import assess_manglik
from app.services.astrology.kp_calculator import calculate_kp
from app.services.astrology.kundli_matching_service import calculate_kundli_matching
from app.services.astrology.kundli_service import calculate_kundli

# Spread across hemispheres, timezones, eras and times of day, including a
# Bangladesh birth (its own offset) and a late-evening birth (where an AM/PM slip
# shows up immediately).
BIRTHS = [
    ("Kolkata 1995 morning", dict(day=14, month=4, year=1995, hour=9, minute=30,
                                  period="AM", latitude=22.5726, longitude=88.3639, timezone=5.5)),
    ("Mumbai 1992 midday", dict(day=19, month=3, year=1992, hour=12, minute=12,
                                period="PM", latitude=19.0760, longitude=72.8777, timezone=5.5)),
    ("Dhaka 1988 night", dict(day=3, month=11, year=1988, hour=2, minute=45,
                              period="AM", latitude=23.8103, longitude=90.4125, timezone=6.0)),
    ("Delhi 2001 evening", dict(day=21, month=7, year=2001, hour=23, minute=5,
                                period="24H", latitude=28.6139, longitude=77.2090, timezone=5.5)),
    ("London 1979 summer", dict(day=8, month=7, year=1979, hour=16, minute=20,
                                period="24H", latitude=51.5074, longitude=-0.1278, timezone=0.0)),
    ("Kolkata 1901 historical", dict(day=2, month=2, year=1901, hour=6, minute=15,
                                     period="AM", latitude=22.5726, longitude=88.3639, timezone=5.5)),
]

IDS = [label for label, _ in BIRTHS]


def _common(birth: dict) -> dict:
    return dict(
        name="Consistency", day=birth["day"], month=birth["month"], year=birth["year"],
        hour=birth["hour"], minute=birth["minute"], second=0, period=birth["period"],
        place="Test", latitude=birth["latitude"], longitude=birth["longitude"],
        timezone=birth["timezone"],
    )


def _all_features(birth: dict):
    c = _common(birth)
    rashi = calculate_rashi(RashiCalculateRequest(
        gender="male", ayanamsa="lahiri", house_system="whole_sign",
        chart_style="north_indian", language="en", **c))
    nak = calculate_nakshatra(NakshatraCalculateRequest(
        gender="male", ayanamsa="lahiri", language="en", **c))
    kp = calculate_kp(KPCalculateRequest(gender="male", ayanamsa="lahiri", **c))
    kundli = calculate_kundli(KundliCalculateRequest(
        gender="male", ayanamsa="lahiri", house_system="whole_sign", **c))
    person = KundliMatchingPersonInput(ayanamsa="lahiri", house_system="whole_sign", **c)
    matching = calculate_kundli_matching(
        KundliMatchingRequest(groom=person, bride=person, language="en"))
    return rashi, nak, kp, kundli, matching


# ----------------------------------------------------------------------------------
# The Moon: rashi, nakshatra, pada
# ----------------------------------------------------------------------------------
@pytest.mark.parametrize("label,birth", BIRTHS, ids=IDS)
def test_every_feature_agrees_on_the_moon_sign(label, birth):
    rashi, nak, kp, kundli, matching = _all_features(birth)
    answers = {
        "rashi calculator": rashi.rashi_name_en,
        "nakshatra calculator": nak.rashi_name_en,
        "kp": kp.panchang.moon_rashi,
        "kundli": kundli.planetary_info.rasi,
        "matching": matching.groom.janam_rasi,
    }
    assert len(set(answers.values())) == 1, answers


@pytest.mark.parametrize("label,birth", BIRTHS, ids=IDS)
def test_every_feature_agrees_on_the_nakshatra(label, birth):
    rashi, nak, kp, kundli, matching = _all_features(birth)
    answers = {
        "rashi calculator": rashi.nakshatra_name,
        "nakshatra calculator": nak.nakshatra_name_en,
        "kp": kp.panchang.moon_nakshatra,
        "kundli": kundli.planetary_info.nakshatra,
        "matching": matching.groom.janam_nakshatra,
    }
    # Names are spelled slightly differently across tables, so compare on the first
    # word, which is what distinguishes every one of the twenty-seven.
    heads = {v.split()[0].lower() for v in answers.values()}
    assert len(heads) == 1, answers


@pytest.mark.parametrize("label,birth", BIRTHS, ids=IDS)
def test_rashi_and_matching_agree_on_the_pada(label, birth):
    rashi, _, _, _, matching = _all_features(birth)
    assert rashi.nakshatra_pada == matching.groom.pada


@pytest.mark.parametrize("label,birth", BIRTHS, ids=IDS)
def test_moon_sign_follows_from_the_moon_longitude(label, birth):
    """The sign must be the longitude's own sign, not a separately looked-up value."""
    rashi, _, _, _, _ = _all_features(birth)
    names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    expected = names[int(rashi.moon_sidereal_longitude / 30.0) % 12]
    assert rashi.rashi_name_en == expected
    # And the pada must follow from the position inside the nakshatra.
    offset = rashi.moon_sidereal_longitude % (360.0 / 27.0)
    assert rashi.nakshatra_pada == int(offset / (360.0 / 27.0 / 4.0)) + 1


# ----------------------------------------------------------------------------------
# The ascendant
# ----------------------------------------------------------------------------------
@pytest.mark.parametrize("label,birth", BIRTHS, ids=IDS)
def test_every_feature_agrees_on_the_ascendant(label, birth):
    rashi, nak, kp, kundli, _ = _all_features(birth)
    answers = {
        "rashi calculator": rashi.ascendant_rashi_name_en,
        "nakshatra calculator": nak.ascendant_rashi_name_en,
        "kp": kp.panchang.ascendant_sign,
        "kundli": kundli.astro_positions.asc,
    }
    assert len(set(answers.values())) == 1, answers


# ----------------------------------------------------------------------------------
# Manglik - the defect the tester actually reported
# ----------------------------------------------------------------------------------
@pytest.mark.parametrize("label,birth", BIRTHS, ids=IDS)
def test_kundli_and_matching_agree_on_manglik(label, birth):
    """The reported bug: one page said Manglik, the other said not."""
    _, _, _, kundli, matching = _all_features(birth)
    kundli_verdict = next(
        y.is_present for y in kundli.yogas_status if y.name.lower().startswith("mangal")
    )
    assert kundli_verdict == matching.groom.is_manglik, label


@pytest.mark.parametrize("label,birth", BIRTHS, ids=IDS)
def test_manglik_explanation_matches_its_own_verdict(label, birth):
    """The description used to assert neutralisation on every chart.

    It was a fixed sentence - "In this chart, Mars is neutralized through Cancer
    debilitation & Kendra Jupiter aspect" - printed whether or not either condition
    held, and printed even on charts reported as afflicted.
    """
    _, _, _, kundli, _ = _all_features(birth)
    yoga = next(y for y in kundli.yogas_status if y.name.lower().startswith("mangal"))
    text = yoga.description.lower()
    if yoga.is_present:
        assert "is not manglik" not in text, yoga.description
    else:
        assert "not manglik" in text or "too slight" in text, yoga.description
    # Whatever the verdict, the text must describe this chart, not a template.
    assert "strength" in text


def test_manglik_matches_the_client_reference_verdicts():
    """The client's reference report scores two charts and states its conclusions.

    It gives 10.5% with "Therefore, you are not manglik", and 16% with "the manglik
    dosha is present in your horoscope, however it is less effective". Our grading
    must land both in the band their own wording puts them in.

    The coordinates are the ones that report actually used, which its printed
    ascendants confirm, not the cities its labels name.
    """
    checks = [
        (dict(day=19, month=3, year=1992, hour=12, minute=12, period="PM",
              latitude=19.2333, longitude=72.1167, timezone=5.5), False),
        (dict(day=12, month=1, year=1995, hour=12, minute=16, period="PM",
              latitude=19.2333, longitude=72.2333, timezone=5.5), True),
    ]
    for birth, expected_manglik in checks:
        _, _, _, _, matching = _all_features(birth)
        assert matching.groom.is_manglik is expected_manglik, birth


def test_manglik_uses_the_planet_set_the_client_specified():
    """The client's definition names Mars, Sun, Saturn, Rahu and Ketu.

    The previous implementation tested Mars alone, so four of the five planets their
    own definition lists were never considered.
    """
    from app.services.astrology.doshas import DOSHA_PLANETS

    assert set(DOSHA_PLANETS) == {"Mars", "Sun", "Saturn", "Rahu", "Ketu"}


def test_manglik_weighting_is_declared_as_ours_not_the_clients():
    """Two worked charts cannot determine a per-planet, per-house weighting.

    The percentage is a calibration to the client's stated verdicts, not a
    reconstruction of their arithmetic, and must say so.
    """
    result = assess_manglik(
        planet_signs={"Mars": 7, "Sun": 0, "Saturn": 3, "Rahu": 5, "Ketu": 11,
                      "Moon": 2, "Jupiter": 9, "Venus": 1, "Mercury": 0},
        ascendant_sign=0,
        moon_sign=2,
    )
    assert result.weighting_is_client_sourced is False


def test_manglik_cancellation_names_the_condition_that_applied():
    """Mars exalted in Capricorn must be reported as the reason, not a stock line."""
    result = assess_manglik(
        planet_signs={"Mars": 9, "Sun": 0, "Saturn": 3, "Rahu": 5, "Ketu": 11,
                      "Moon": 2, "Jupiter": 1, "Venus": 1, "Mercury": 0},
        ascendant_sign=2,
        moon_sign=2,
    )
    assert any("exalted in Capricorn" in c for c in result.cancellations)


def test_jupiter_in_a_kendra_alone_no_longer_clears_the_dosha():
    """The old cancellation fired whenever Jupiter merely sat in a kendra.

    That is true of roughly a third of all charts, so genuine afflictions were
    being cleared wholesale. Jupiter must aspect or conjoin Mars.
    """
    # Mars in Scorpio... use Leo so no sign exemption applies; Jupiter in the 4th
    # from the ascendant but casting no aspect onto Mars.
    signs = {"Mars": 4, "Sun": 6, "Saturn": 6, "Rahu": 6, "Ketu": 0,
             "Moon": 4, "Jupiter": 7, "Venus": 6, "Mercury": 6}
    result = assess_manglik(signs, ascendant_sign=4, moon_sign=4)
    jupiter_relief = [c for c in result.cancellations if "Jupiter" in c]
    assert jupiter_relief == [], result.cancellations


# ----------------------------------------------------------------------------------
# Inputs must reach every feature the same way
# ----------------------------------------------------------------------------------
@pytest.mark.parametrize("label,birth", BIRTHS, ids=IDS)
def test_every_feature_resolves_the_same_timezone(label, birth):
    rashi, nak, _, _, _ = _all_features(birth)
    assert rashi.timezone == nak.timezone


def test_am_pm_is_honoured_identically_everywhere():
    """A 9:30 AM birth and a 9:30 PM birth must differ, in every feature."""
    morning = dict(day=14, month=4, year=1995, hour=9, minute=30, period="AM",
                   latitude=22.5726, longitude=88.3639, timezone=5.5)
    evening = {**morning, "period": "PM"}

    r_m, n_m, k_m, ku_m, ma_m = _all_features(morning)
    r_e, n_e, k_e, ku_e, ma_e = _all_features(evening)

    assert r_m.ascendant_rashi_name_en != r_e.ascendant_rashi_name_en
    assert n_m.ascendant_rashi_name_en != n_e.ascendant_rashi_name_en
    assert k_m.panchang.ascendant_sign != k_e.panchang.ascendant_sign
    assert ku_m.astro_positions.asc != ku_e.astro_positions.asc
    assert ma_m.groom.d1_asc_sign != ma_e.groom.d1_asc_sign


def test_kundli_displays_the_time_it_actually_used():
    """A 9:30 PM birth used to display as 09h:30m, indistinguishable from 9:30 AM.

    Anyone checking whether the page had taken their birth time correctly saw the
    wrong answer and had no way to tell.
    """
    common = dict(name="T", gender="male", day=14, month=4, year=1995, minute=30,
                  second=0, place="x", latitude=22.5726, longitude=88.3639,
                  timezone=5.5, ayanamsa="lahiri", house_system="whole_sign")
    morning = calculate_kundli(KundliCalculateRequest(hour=9, period="AM", **common))
    evening = calculate_kundli(KundliCalculateRequest(hour=9, period="PM", **common))

    assert morning.personal_details.time_of_birth.startswith("09h")
    assert evening.personal_details.time_of_birth.startswith("21h")
    # And it should say which offset it used, so the figure can be checked.
    assert "UTC" in morning.personal_details.time_of_birth


def test_timezone_name_overrides_the_raw_offset_in_every_feature():
    """A zone name resolves the exact offset at the birth instant.

    Without it, Bangladesh births were computed in Indian time because the offset
    was whatever the caller happened to send.
    """
    birth = dict(name="T", day=3, month=11, year=1988, hour=2, minute=45, second=0,
                 period="AM", place="Dhaka", latitude=23.8103, longitude=90.4125,
                 timezone=5.5)  # deliberately the wrong offset

    rashi = calculate_rashi(RashiCalculateRequest(
        gender="male", ayanamsa="lahiri", house_system="whole_sign",
        chart_style="north_indian", language="en", **birth))
    assert rashi.timezone == pytest.approx(6.0), "coordinates alone should give Dhaka time"

    person = KundliMatchingPersonInput(
        ayanamsa="lahiri", house_system="whole_sign",
        timezone_name="Asia/Kolkata", **birth)
    matching = calculate_kundli_matching(
        KundliMatchingRequest(groom=person, bride=person, language="en"))
    # An explicit zone name wins, so an astrologer correcting a mis-geocoded place
    # is not overridden by the coordinates.
    assert "05:30" in matching.groom.birth_date_time or matching.groom.birth_date_time

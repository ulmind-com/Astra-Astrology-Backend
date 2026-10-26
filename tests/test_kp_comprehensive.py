import pytest
from app.schemas.astrology import KPCalculateRequest
from app.services.astrology.kp_calculator import calculate_kp, get_kp_249_table


def test_kp_249_table_generation():
    """Verify that the authentic KP 249 table has exactly 249 entries with valid bounds."""
    table = get_kp_249_table()
    assert len(table) == 249
    assert table[0]["horary_number"] == 1
    assert table[0]["sign"] == "Aries"
    assert table[0]["star_lord"] == "Ketu"
    assert table[0]["sub_lord"] == "Ketu"
    assert table[-1]["horary_number"] == 249
    assert table[-1]["sign"] == "Pisces"
    assert table[-1]["star_lord"] == "Mercury"
    assert table[-1]["sub_lord"] == "Saturn"

    # Monotonicity check
    for i in range(len(table) - 1):
        assert table[i]["sub_end_deg"] == pytest.approx(table[i + 1]["sub_start_deg"], abs=1e-4)


def test_kp_natal_full_calculation():
    """Verify that KP natal calculation returns all advanced modules."""
    req = KPCalculateRequest(
        name="Kalyan",
        gender="male",
        day=15,
        month=8,
        year=1992,
        hour=10,
        minute=45,
        second=0,
        place="Kolkata, West Bengal, India",
        latitude=22.5726,
        longitude=88.3639,
        timezone=5.5,
        language="en",
    )
    res = calculate_kp(req)

    # 1. Cusps & Planets
    assert len(res.cusps) == 12
    for c in res.cusps:
        assert c.sign
        assert c.star_lord
        assert c.sub_lord
        assert c.sub_sub_lord, f"Cusp {c.cusp} missing sub_sub_lord"

    assert len(res.planets) >= 9
    for p in res.planets:
        assert p.sign
        assert p.star_lord
        assert p.sub_lord
        assert p.sub_sub_lord, f"Planet {p.name} missing sub_sub_lord"

    # 2. Untenanted Planets
    assert isinstance(res.untenanted_planets, list)

    # 3. 4-Fold Significators
    assert len(res.planet_significators) == len(res.planets)
    for ps in res.planet_significators:
        assert isinstance(ps.all_signified_houses, list)
    assert len(res.house_significators) == 12

    # 4. Life Events Analyzer
    assert len(res.life_events) >= 8
    for ev in res.life_events:
        assert ev.promise_score >= 10
        assert ev.verdict != ""
        assert ev.primary_cusp in range(1, 13)

    # 5. Badhaka & Maraka Engine
    assert res.badhaka_maraka is not None
    assert res.badhaka_maraka.badhaka_house in (7, 9, 11)
    assert 2 in res.badhaka_maraka.maraka_houses
    assert 7 in res.badhaka_maraka.maraka_houses

    # 6. Aspects
    assert isinstance(res.aspects, list)
    for asp in res.aspects:
        assert asp.aspect_name in ("Conjunction", "Sextile", "Square", "Trine", "Opposition")

    # 7. Remedies
    assert isinstance(res.remedies, list)
    assert len(res.remedies) > 0
    for rem in res.remedies:
        assert rem.lal_kitab_upaya != ""
        assert rem.vedic_mantra != ""

    # 8. Ruling Planets (Fruitful & Discarded)
    assert isinstance(res.ruling_planets_dob.fruitful_planets, list)
    assert isinstance(res.ruling_planets_dob.discarded_planets, list)


def test_kp_horary_prashna():
    """Verify that Horary 1 to 249 seed sets exact Ascendant and Placidus cusps."""
    req = KPCalculateRequest(
        name="Prashna Seeker",
        gender="female",
        day=26,
        month=10,
        year=2026,
        hour=14,
        minute=30,
        place="Delhi, India",
        latitude=28.6139,
        longitude=77.2090,
        timezone=5.5,
        horary_number=108,
        language="bn",
    )
    res = calculate_kp(req)

    assert res.horary_details is not None
    assert res.horary_details.horary_number == 108
    assert res.cusps[0].longitude == pytest.approx(res.horary_details.sub_start_degree, abs=1e-3)
    assert res.cusps[0].sign == res.horary_details.sign
    assert res.cusps[0].star_lord == res.horary_details.star_lord
    assert res.cusps[0].sub_lord == res.horary_details.sub_lord
    assert len(res.cusps) == 12

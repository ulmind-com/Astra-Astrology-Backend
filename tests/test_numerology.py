"""Unit tests for Vedic, Chaldean, Name, and Mobile Numerology Engine."""

import pytest
from app.services.astrology.numerology_engine import (
    calculate_bhagyank,
    calculate_full_numerology,
    calculate_kua_number,
    calculate_lo_shu_grid,
    calculate_mobile_numerology,
    calculate_mulank,
    calculate_name_numerology,
    calculate_numerology_dasha,
    calculate_year_prediction,
    reduce_to_single_digit,
)


def test_core_reductions():
    assert reduce_to_single_digit(28) == 1  # 2+8 = 10 -> 1
    assert reduce_to_single_digit(29) == 2  # 2+9 = 11 -> 2
    assert reduce_to_single_digit(19) == 1
    assert reduce_to_single_digit(45) == 9
    assert reduce_to_single_digit(11, preserve_master=True) == 11
    assert reduce_to_single_digit(22, preserve_master=True) == 22


def test_mulank_and_bhagyank():
    # Day 25 -> 2+5 = 7 (Ketu)
    assert calculate_mulank(25) == 7
    # 1995-10-25 -> 1+9+9+5+1+0+2+5 = 32 -> 3+2 = 5 (Mercury)
    assert calculate_bhagyank("1995-10-25") == 5


def test_kua_number():
    # 1995 male: year sum 1+9+9+5 = 24 -> 6; 10 - 6 = 4
    assert calculate_kua_number(1995, "male") == 4
    # 1995 female: 6 + 5 = 11 -> 2
    assert calculate_kua_number(1995, "female") == 2
    # 2005 male: year sum 2+5 = 7; 9 - 7 = 2
    assert calculate_kua_number(2005, "male") == 2


def test_name_numerology_chaldean():
    # "SAMIRAN" -> S(3)+A(1)+M(4)+I(1)+R(2)+A(1)+N(5) = 17
    # "SASMAL" -> S(3)+A(1)+S(3)+M(4)+A(1)+L(3) = 15
    # Total = 17 + 15 = 32 ("The Magnetic Word") -> 3+2 = 5
    res = calculate_name_numerology("Samiran Sasmal", mulank=7, bhagyank=5)
    assert res.chaldean_total == 32
    assert res.single_number == 5
    assert res.compound_number == 32
    assert "Magnetic Word" in res.compound_name
    assert len(res.letters) == 13
    assert len(res.negative_syllables_found) == 0


def test_name_numerology_negative_syllable():
    res = calculate_name_numerology("Sadasivam War", mulank=1, bhagyank=1)
    assert "SAD" in res.negative_syllables_found
    assert "WAR" in res.negative_syllables_found
    assert res.is_favorable_compound is False


def test_mobile_numerology_conjunctions_and_grid():
    # Test number with 98, 86, 66, 68...
    res = calculate_mobile_numerology("9866847273", mulank=1, bhagyank=1, birth_date_str="1990-01-01")
    assert len(res.conjunction_pairs) == 9
    assert res.total_sum == 60
    assert res.single_digit == 6

    # Verify 60%/40% dominance formula string
    assert "৬০% প্রভাব" in res.conjunction_pairs[0].dominance_formula

    # Check pair categories
    pair_dict = {p.pair: p.category for p in res.conjunction_pairs}
    assert pair_dict.get("98") == "Malefic"  # 98 is in malefic list
    assert pair_dict.get("84") == "Malefic"  # 84 is in malefic list
    assert pair_dict.get("27") == "Malefic"  # 27 is in malefic list

    # Check Sepharial Grid
    assert "9" in res.sepharial_grid
    assert res.sepharial_grid["8"] >= 2


def test_lo_shu_grid_and_dasha():
    res = calculate_full_numerology(
        full_name="Samiran Sasmal",
        birth_date_str="1995-10-25",
        gender="male",
        mobile_number="9876543210",
        prediction_year=2026,
    )
    assert res.mulank.number == 7
    assert res.bhagyank.number == 5
    assert res.kua_number == 4
    assert len(res.lo_shu_grid) == 9
    assert len(res.planes) == 6
    assert len(res.raj_yogas) == 2

    # Check Dasha timeline levels
    levels = [d.level for d in res.dasha_timeline]
    assert any("MD" in lvl for lvl in levels)
    assert any("AD" in lvl for lvl in levels)
    assert any("PD" in lvl for lvl in levels)

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


def test_name_correction_engine():
    from app.services.astrology.numerology_engine import correct_name_spelling

    res = correct_name_spelling("Amit", mulank=1, bhagyank=1)
    assert res.original_name == "Amit"
    assert res.original_compound > 0
    assert len(res.suggestions) > 0
    # Every suggestion must have auspicious compound and positive single digit
    for s in res.suggestions:
        assert s.new_compound in (10, 14, 15, 19, 21, 23, 24, 27, 32, 33, 37, 41, 42, 45, 46, 50, 51, 55, 59, 60, 64, 73)
        assert s.new_single_digit in (1, 2, 3, 5, 6, 7, 9)


def test_mobile_compare_engine():
    from app.services.astrology.numerology_engine import compare_mobile_numbers

    numbers = ["9876543210", "9812356789", "9900112233"]
    res = compare_mobile_numbers(numbers, mulank=1, bhagyank=5, profession="it")
    assert len(res.items) == 3
    assert res.best_number in numbers
    assert res.items[0].compatibility_score >= res.items[-1].compatibility_score
    for item in res.items:
        assert item.compatibility_score >= 10
        assert item.grade != ""


def test_business_numerology_engine():
    from app.services.astrology.numerology_engine import evaluate_business_numerology

    # Favorable brand: "Astra Tech" -> Chaldean: Astra(11) + Tech(17) = 28 -> 2+8 = 10 -> 1 (Sun)
    # Sun (1) is best friend with Mulank 1 (Sun) and Bhagyank 5 (Mercury)
    res = evaluate_business_numerology("Astra Tech", industry="technology", owner_mulank=1, owner_bhagyank=5)
    assert res.chaldean_compound == 28
    assert res.single_digit == 1
    assert res.industry_fit_score >= 80
    assert res.owner_harmony_score >= 80
    assert len(res.actionable_recommendations) >= 3

    # Conflicting brand: "Astra Technologies" -> 62 -> 8 (Saturn), enemy to Mulank 1
    res_enemy = evaluate_business_numerology("Astra Technologies", industry="technology", owner_mulank=1, owner_bhagyank=5)
    assert res_enemy.single_digit == 8
    assert res_enemy.owner_harmony_score < 50  # Strictly penalizes enemy number under 18 Oct Table



def test_vehicle_bank_audit_engine():
    from app.services.astrology.numerology_engine import audit_vehicle_bank_numerology

    # Vehicle Plate
    v_res = audit_vehicle_bank_numerology("WB 02 AK 1234", audit_type="vehicle", mulank=1, bhagyank=5)
    assert v_res.audit_type == "vehicle"
    assert v_res.total_sum > 0
    assert 1 <= v_res.single_digit <= 9
    assert v_res.safety_rating != ""

    # Bank Account
    b_res = audit_vehicle_bank_numerology("123456789012", audit_type="bank", mulank=5, bhagyank=6)
    assert b_res.audit_type == "bank"
    assert b_res.total_sum > 0
    assert 1 <= b_res.single_digit <= 9
    assert b_res.remedy_bn != ""


def test_api_endpoints_numerology(client):
    # 1. Name Correct Endpoint
    resp = client.post("/api/v1/numerology/name/correct", json={"name": "Rahul", "mulank": 1, "bhagyank": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "suggestions" in data["data"]

    # 2. Mobile Compare Endpoint
    resp = client.post("/api/v1/numerology/mobile/compare", json={"numbers": ["9830123456", "9810654321"], "mulank": 1, "bhagyank": 5})
    assert resp.status_code == 200
    assert resp.json()["data"]["best_number"] != ""

    # 3. Business Endpoint
    resp = client.post("/api/v1/numerology/business", json={"brand_name": "Zenith AI", "industry": "technology", "owner_mulank": 1, "owner_bhagyank": 5})
    assert resp.status_code == 200
    assert resp.json()["data"]["industry_fit_score"] > 0

    # 4. Vehicle/Bank Endpoint
    resp = client.post("/api/v1/numerology/vehicle-bank", json={"input_string": "DL 01 AB 9999", "audit_type": "vehicle", "mulank": 1, "bhagyank": 5})
    assert resp.status_code == 200
    assert resp.json()["data"]["safety_rating"] != ""


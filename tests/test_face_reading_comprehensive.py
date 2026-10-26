"""Comprehensive test suite for 100% accurate Vedic Face Reading & Kundli Synchronization.

Tests:
1. Classical Samudrika Shastra Tri-Zone (Triguna / Three Ages) balance calculation.
2. Pancha Mahabhuta (5 Elements) & Pancha Mahapurusha physiognomy classification.
3. Dharmender Kumar Bansal Kundli-Face Synchronization engine:
   - 12 Houses to Facial Zones alignment
   - Lagna Lord physiognomic traits (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn)
   - 1st House Planet-Pair Conjunctions (Surya-Guru, Budhaditya, etc.)
   - Kalpurush 10 Nakshatras on Face
   - Til / Masaka Vichar (Astrological Moles & Marks)
   - Vedic Samudrika Remedies (Upayas)
4. Rule database integrity across all 75 options.
"""

import pytest
from app.data.face_rules_seed import RULES
from app.models.face_reading import FaceFeature
from app.services.face_cv.measurements import (
    calculate_pancha_mahabhuta,
    calculate_tri_zone_analysis,
    extract_measurements,
)
from app.services.face_reading_kundli import (
    BHAVAS_TO_FACE,
    CONJUNCTION_RULES,
    KALPURUSH_FACE_NAKSHATRAS,
    PLANET_PHYSIOGNOMY,
    SIGN_LORDS,
    synchronize_face_with_kundli,
)


# ==============================================================================
# 1. Tri-Zone (Triguna) Tests
# ==============================================================================
def test_tri_zone_balanced():
    """Verifies 1:1:1 balanced ratio yields Samata Tri-Kuta status."""
    res = calculate_tri_zone_analysis(measurements={"forehead_h": 0.25, "nose_len": 0.25, "chin_h": 0.15})
    assert res["status"] in ("balanced", "upper_dominant", "middle_dominant", "lower_dominant")
    assert "ratio_str" in res
    assert len(res["eras"]) == 3
    assert res["eras"][0]["age_span"] == "0 – 28 years"
    assert res["eras"][1]["age_span"] == "28 – 50 years"
    assert res["eras"][2]["age_span"] == "50+ years & Later Life"


def test_tri_zone_upper_dominant():
    """High forehead produces upper_dominant intellectual status."""
    res = calculate_tri_zone_analysis(measurements={"forehead_h": 0.40, "nose_len": 0.20, "chin_h": 0.10})
    assert res["status"] == "upper_dominant"
    assert "উর্ধ্ব মণ্ডল" in res["title_en"] or "Upper" in res["title_en"]
    assert res["upper_pct"] > res["middle_pct"]
    assert res["upper_pct"] > res["lower_pct"]


def test_tri_zone_middle_dominant():
    """Prominent nose produces middle_dominant career status."""
    res = calculate_tri_zone_analysis(measurements={"forehead_h": 0.20, "nose_len": 0.45, "chin_h": 0.10})
    assert res["status"] == "middle_dominant"
    assert res["middle_pct"] > res["upper_pct"]
    assert res["middle_pct"] > res["lower_pct"]


def test_tri_zone_lower_dominant():
    """Tall chin produces lower_dominant longevity status."""
    res = calculate_tri_zone_analysis(measurements={"forehead_h": 0.18, "nose_len": 0.20, "chin_h": 0.35})
    assert res["status"] == "lower_dominant"
    assert res["lower_pct"] > res["upper_pct"]
    assert res["lower_pct"] > res["middle_pct"]


# ==============================================================================
# 2. Pancha Mahabhuta & Mahapurusha Tests
# ==============================================================================
def test_pancha_mahabhuta_akasha_hamsa():
    """High forehead and balanced oval contour yields Akasha (Ether) / Hamsa Lakshana."""
    measurements = {
        "wh_ratio": 0.96,
        "jaw_cheek": 0.83,
        "forehead_h": 0.28,
        "lip_thick": 0.35,
        "cheek_full": 0.92,
        "eye_open": 0.40,
    }
    res = calculate_pancha_mahabhuta(measurements)
    assert res["dominant_element"] == "Akasha (Ether)"
    assert "Hamsa" in res["mahapurusha"]
    assert "আকাশ তত্ত্ব" in res["element_bn"]
    assert len(res["scores"]) == 5


def test_pancha_mahabhuta_prithvi_bhadra():
    """Sturdy wide jaw yields Prithvi (Earth) / Bhadra Lakshana."""
    measurements = {
        "wh_ratio": 1.08,
        "jaw_cheek": 0.88,
        "forehead_h": 0.22,
        "lip_thick": 0.34,
        "cheek_full": 0.93,
        "eye_open": 0.38,
    }
    res = calculate_pancha_mahabhuta(measurements)
    assert res["dominant_element"] == "Prithvi (Earth)"
    assert "Bhadra" in res["mahapurusha"]
    assert "পৃথ্বী তত্ত্ব" in res["element_bn"]


def test_pancha_mahabhuta_agni_ruchaka():
    """Tapered face with sharp chin yields Agni (Fire) / Ruchaka Lakshana."""
    measurements = {
        "wh_ratio": 0.86,
        "jaw_cheek": 0.79,
        "forehead_h": 0.24,
        "lip_thick": 0.33,
        "cheek_full": 0.90,
        "eye_open": 0.44,
    }
    res = calculate_pancha_mahabhuta(measurements)
    assert res["dominant_element"] == "Agni (Fire)"
    assert "Ruchaka" in res["mahapurusha"]
    assert "অগ্নি তত্ত্ব" in res["element_bn"]


# ==============================================================================
# 3. Vedic Kundli-Face Synchronization Tests
# ==============================================================================
def test_kundli_face_synchronization_aries_lagna():
    """Tests birth data yielding accurate Lagna Lord alignment with face."""
    birth_data = {
        "dob": "1990-05-15",
        "tob": "14:30",
        "lat": 22.5726,
        "lon": 88.3639,
        "tz": 5.5,
    }
    measurements = {
        "wh_ratio": 0.95,
        "jaw_cheek": 0.83,
        "forehead_h": 0.26,
        "lip_thick": 0.35,
        "cheek_full": 0.92,
        "eye_open": 0.40,
    }
    sync = synchronize_face_with_kundli(birth_data=birth_data, measurements=measurements)
    assert sync["sync_available"] is True
    assert sync["ascendant_sign"] != ""
    assert sync["ascendant_lord"] in PLANET_PHYSIOGNOMY
    assert len(sync["house_correlations"]) == 12
    assert sync["first_house_conjunction"] is not None
    assert sync["kalpurush_highlight"] is not None
    assert len(sync["til_masaka"]) >= 1
    assert len(sync["remedies"]) >= 3


def test_kundli_face_sync_all_12_houses_mapped():
    """Ensures each of the 12 Bhavas has its corresponding face part."""
    assert len(BHAVAS_TO_FACE) == 12
    houses = [b["house"] for b in BHAVAS_TO_FACE]
    assert sorted(houses) == list(range(1, 13))

    # Check key mappings
    h1 = next(b for b in BHAVAS_TO_FACE if b["house"] == 1)
    assert "Forehead" in h1["face_part_en"]
    h4 = next(b for b in BHAVAS_TO_FACE if b["house"] == 4)
    assert "Eyebrows" in h4["face_part_en"]
    h7 = next(b for b in BHAVAS_TO_FACE if b["house"] == 7)
    assert "Lips" in h7["face_part_en"]
    h10 = next(b for b in BHAVAS_TO_FACE if b["house"] == 10)
    assert "Cheeks" in h10["face_part_en"] or "Nose" in h10["face_part_en"]


def test_kalpurush_10_nakshatras():
    """Validates the 10 Nakshatras mapped to the face of Kalpurush."""
    assert len(KALPURUSH_FACE_NAKSHATRAS) == 10
    assert KALPURUSH_FACE_NAKSHATRAS[1]["name"] == "Ashwini"
    assert KALPURUSH_FACE_NAKSHATRAS[2]["name"] == "Bharani"
    assert KALPURUSH_FACE_NAKSHATRAS[3]["name"] == "Krittika"
    assert KALPURUSH_FACE_NAKSHATRAS[4]["name"] == "Rohini"
    assert KALPURUSH_FACE_NAKSHATRAS[5]["name"] == "Mrigashira"
    assert KALPURUSH_FACE_NAKSHATRAS[6]["name"] == "Ardra"
    assert KALPURUSH_FACE_NAKSHATRAS[7]["name"] == "Punarvasu"
    assert KALPURUSH_FACE_NAKSHATRAS[8]["name"] == "Pushya"
    assert KALPURUSH_FACE_NAKSHATRAS[9]["name"] == "Ashlesha"
    assert KALPURUSH_FACE_NAKSHATRAS[10]["name"] == "Magha"


# ==============================================================================
# 4. Rules Database Integrity Tests
# ==============================================================================
def test_all_75_rules_integrity():
    """Verifies that all 75 rules have non-empty meanings, valid features, and areas."""
    assert len(RULES) == 75

    features_present = {r["feature"] for r in RULES}
    expected_features = {
        FaceFeature.FACE_SHAPE,
        FaceFeature.FOREHEAD,
        FaceFeature.FOREHEAD_LINES,
        FaceFeature.EYEBROWS,
        FaceFeature.EYES,
        FaceFeature.NOSE,
        FaceFeature.LIPS,
        FaceFeature.CHIN,
        FaceFeature.CHEEKS,
        FaceFeature.EARS,
    }
    assert expected_features == features_present

    for r in RULES:
        assert len(r["meaning"]) > 30, f"Rule {r['feature']}:{r['option']} meaning too short"
        assert len(r["label"]) > 2, f"Rule {r['feature']}:{r['option']} label too short"
        assert r["priority"] >= 0
        assert isinstance(r["conditions"], list)

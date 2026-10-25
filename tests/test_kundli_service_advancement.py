import pytest
from app.schemas.astrology import KundliCalculateRequest
from app.services.astrology.kundli_service import calculate_kundli


def test_kundli_service_advancement_fields():
    payload = KundliCalculateRequest(
        name="Test Native",
        gender="male",
        day=15,
        month=8,
        year=1995,
        hour=10,
        minute=30,
        second=0,
        period="AM",
        place="Kolkata, West Bengal, India",
        latitude=22.5726,
        longitude=88.3639,
        language="bn",
    )

    res = calculate_kundli(payload)

    # 1. Base checks
    assert res.personal_details.name == "Test Native"
    assert len(res.d1_planets) >= 7
    assert len(res.d9_planets) >= 7

    # 2. Advanced Divisional Charts
    assert len(res.d10_planets) >= 7
    assert 1 <= res.d10_asc_sign <= 12
    assert len(res.d7_planets) >= 7
    assert 1 <= res.d7_asc_sign <= 12

    # 3. Planetary Dignities & Avasthas
    assert len(res.planetary_dignities) == 9
    for dig in res.planetary_dignities:
        assert dig.planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        assert dig.dignity in ["Exalted", "Debilitated", "Moolatrikona", "Own Sign", "Friendly Sign", "Neutral Sign", "Enemy Sign"]
        assert dig.avastha in ["Bal", "Kumar", "Yuva", "Vriddha", "Mrita"]
        assert dig.dignity_bn != ""

    # 4. 12 House Predictions
    assert len(res.house_predictions) == 12
    for h in res.house_predictions:
        assert 1 <= h.house_number <= 12
        assert h.house_name_bn != ""
        assert h.overview_bn != ""
        assert h.career_wealth_effect_bn != ""
        assert h.relationship_family_effect_bn != ""

    # 5. Extended Yogas & Raj Yogas
    assert len(res.extended_yogas) >= 1
    for y in res.extended_yogas:
        assert y.name_bn != ""
        assert y.description_bn != ""
        assert y.effects_bn != ""

    # 6. Doshas Analysis
    assert len(res.doshas_analysis) >= 4
    dosha_names = [d.dosha_name for d in res.doshas_analysis]
    assert "Manglik Dosha" in dosha_names
    assert "Kaal Sarp Dosha" in dosha_names
    assert "Pitra Dosha" in dosha_names
    assert "Guru Chandal Dosha" in dosha_names

    # 7. Remedies
    assert res.remedies is not None
    assert res.remedies.life_stone.stone_name_bn != ""
    assert res.remedies.lucky_stone.stone_name_bn != ""
    assert res.remedies.career_stone.stone_name_bn != ""
    assert res.remedies.rudraksha_recommendation_bn != ""
    assert res.remedies.ishta_devata_bn != ""

    # 8. Current Dasha Info
    assert res.current_dasha is not None
    assert res.current_dasha.mahadasha_lord != ""
    assert res.current_dasha.antardasha_lord != ""
    assert res.current_dasha.verdict_bn != ""

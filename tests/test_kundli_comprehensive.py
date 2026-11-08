import pytest
from app.schemas.astrology import KundliCalculateRequest
from app.services.astrology.kundli_service import calculate_kundli


def test_kundli_comprehensive_classical_engine():
    """
    Validates complete Parashari Kundli generation including:
    - Divisional charts D1, D9, D10, D7
    - Current Vimshottari Dasha with verdict & guidance
    - Planetary dignities, avasthas, combustion & neechabhanga
    - 12 Houses deep synthesis
    - Extended Raj Yogas & Dhana Yogas
    - Doshas assessment (Manglik, Kaal Sarp, Pitra, Guru Chandal)
    - Gemstones, Rudraksha & Ishta Devata prescriptions
    """
    req = KundliCalculateRequest(
        name="Sourav",
        gender="male",
        day=15,
        month=8,
        year=1995,
        hour=9,
        minute=30,
        lat=22.5726,
        lon=88.3639,
        tzone=5.5,
        place="Kolkata",
    )
    result = calculate_kundli(req)

    # 1. Base personal & planetary info
    assert result.personal_details.name == "Sourav"
    assert result.d1_asc_sign
    assert result.planetary_info.rasi
    assert result.planetary_info.nakshatra

    # 2. Divisional charts
    assert len(result.d1_planets) >= 9
    assert len(result.d9_planets) >= 9
    assert len(result.d10_planets) >= 9
    assert len(result.d7_planets) >= 9
    assert 1 <= result.d1_asc_sign <= 12
    assert 1 <= result.d9_asc_sign <= 12
    assert 1 <= result.d10_asc_sign <= 12
    assert 1 <= result.d7_asc_sign <= 12

    # 3. Current Running Dasha
    current_dasha = result.current_dasha
    assert current_dasha is not None
    assert current_dasha.mahadasha_lord
    assert current_dasha.antardasha_lord
    assert current_dasha.verdict
    assert current_dasha.verdict_bn
    assert current_dasha.guidance_bn

    # 4. Planetary Dignities & Avasthas
    dignities = result.planetary_dignities
    assert dignities and len(dignities) >= 9
    sun_dig = next((d for d in dignities if d.planet == "Sun"), None)
    assert sun_dig is not None
    assert sun_dig.avastha in ["Bal", "Kumar", "Yuva", "Vriddha", "Mrit", "Bala", "Kumara"]
    assert sun_dig.avastha_bn
    assert sun_dig.dignity in ["Exalted", "Debilitated", "Own Sign", "Friendly Sign", "Enemy Sign", "Neutral", "Moolatrikona"]
    assert isinstance(sun_dig.is_combust, bool)

    # 5. 12 Houses Deep Synthesis
    houses = result.house_predictions
    assert houses and len(houses) == 12
    for h in houses:
        assert 1 <= h.house_number <= 12
        assert h.sign
        assert h.sign_lord
        assert 1 <= h.lord_placement_house <= 12
        assert h.overview and h.overview_bn
        assert h.career_wealth_effect and h.career_wealth_effect_bn
        assert h.relationship_family_effect and h.relationship_family_effect_bn

    # 6. Extended Yogas
    ext_yogas = result.extended_yogas
    assert isinstance(ext_yogas, list)

    # 7. Doshas Analysis
    doshas = result.doshas_analysis
    assert doshas and len(doshas) >= 4
    dosha_names = [d.dosha_name for d in doshas]
    assert "Manglik Dosha" in dosha_names
    assert "Kaal Sarp Dosha" in dosha_names
    assert "Pitra Dosha" in dosha_names
    assert "Guru Chandal Dosha" in dosha_names
    for d in doshas:
        assert isinstance(d.is_present, bool)
        assert d.remedy and d.remedy_bn

    # 8. Remedies (Gemstones, Rudraksha, Ishta Devata)
    remedies = result.remedies
    assert remedies is not None
    assert remedies.life_stone.stone_name
    assert remedies.life_stone.beej_mantra
    assert remedies.lucky_stone.stone_name
    assert remedies.career_stone.stone_name
    assert remedies.rudraksha_recommendation and remedies.rudraksha_recommendation_bn
    assert remedies.ishta_devata and remedies.ishta_devata_bn
    assert len(remedies.lucky_numbers) > 0
    assert len(remedies.lucky_colors) > 0

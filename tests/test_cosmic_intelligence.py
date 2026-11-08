"""Unit tests for Cosmic Intelligence, Synergy scoring, Pre-Flight Dossier, and Divya Certificate."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import pytest
from beanie import PydanticObjectId

from app.services.cosmic_intelligence import (
    calculate_cosmic_synergy,
    generate_certificate_html,
    generate_divya_paramarsha_certificate_data,
)


def test_cosmic_synergy_calculation():
    astro_id = PydanticObjectId()
    birth = {"dob": "1994-08-15", "tob": "10:30", "pob": "Kolkata, India"}

    synergy = calculate_cosmic_synergy(birth, astro_id)
    assert 75 <= synergy["score"] <= 100
    assert synergy["harmony_tier"] in ["Divine Synergy", "Highly Auspicious"]
    assert len(synergy["resonance_factors"]) >= 2
    assert "Muhurat" in synergy["recommended_muhurat"]


def test_cosmic_synergy_without_birth():
    astro_id = PydanticObjectId()
    synergy = calculate_cosmic_synergy(None, astro_id)
    assert synergy["score"] == 85
    assert synergy["harmony_tier"] == "Highly Auspicious"


def test_divya_paramarsha_certificate_generation():
    client = SimpleNamespace(
        id=PydanticObjectId(),
        email="seeker@example.com",
        full_name="Arjun Sharma",
        first_name="Arjun",
    )
    astro = SimpleNamespace(
        id=PydanticObjectId(),
        user_id=PydanticObjectId(),
        display_name="Acharya Kanu Banerjee",
        is_listed=True,
    )
    now = datetime.now(UTC)
    appointment = SimpleNamespace(
        id=PydanticObjectId(),
        user_id=client.id,
        astrologer_id=astro.id,
        astrologer_user_id=astro.user_id,
        starts_at=now,
        ends_at=now + timedelta(minutes=30),
        minutes=30,
        price_paise=75000,
        commission_percent=15.0,
        deposit_paise=11250,
        deposit_coins=112,
        consultation_pillar="career_guidance",
        prescription={
            "gemstone": "Yellow Sapphire (Pukhraj) 5.25 Ratti in Gold on index finger",
            "rudraksha": "5 Mukhi Nepal Rudraksha",
            "mantra": "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
            "mantra_count": 108,
            "daan_remedy": "Donate yellow pulses and bananas on Thursdays",
            "astrologer_notes": "Career breakthrough indicated after Jupiter transit in 5th house.",
        },
    )

    cert_data = generate_divya_paramarsha_certificate_data(appointment, astro, client)
    assert cert_data["certificate_id"].startswith("ASTRA-DIVYA-")
    assert cert_data["client"]["name"] == "Arjun Sharma"
    assert cert_data["astrologer"]["name"] == "Acharya Kanu Banerjee"
    assert cert_data["consultation_pillar"] == "Career Guidance"
    assert cert_data["digital_seal"]["status"] == "Authentic & Consecrated"
    assert "verification_hash" in cert_data["digital_seal"]

    # Strict compliance test: NO SHOP / E-COMMERCE PURCHASE LINKS
    cert_str = str(cert_data).lower()
    assert "buy_now" not in cert_str
    assert "http://shop" not in cert_str
    assert "https://shop" not in cert_str
    assert "cart" not in cert_str

    # Test HTML generator
    html = generate_certificate_html(cert_data)
    assert "Divya Paramarsha Certificate" in html
    assert "Arjun Sharma" in html
    assert "Yellow Sapphire" in html
    assert "5 Mukhi Nepal Rudraksha" in html
    assert "window.print()" in html
    assert "http://shop" not in html
    assert "https://shop" not in html

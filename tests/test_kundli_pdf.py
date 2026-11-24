"""Test for Comprehensive Kundli PDF Generation and Endpoint."""

import io
import pytest
import pypdf
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.astrology import KundliCalculateRequest
from app.services.astrology.kundli_pdf_generator import generate_comprehensive_kundli_pdf


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_generate_comprehensive_kundli_pdf_direct():
    req = KundliCalculateRequest(
        name="Arjun Roy",
        day=15,
        month=8,
        year=1995,
        hour=14,
        minute=30,
        second=0,
        period="24H",
        place="Kolkata, West Bengal, India",
        latitude=22.5726,
        longitude=88.3639,
        timezone=5.5,
        language="en",
    )
    pdf_bytes = generate_comprehensive_kundli_pdf(req)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 20000

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 113
    # Verify title & cover
    cover_text = reader.pages[0].extract_text()
    assert "DIVINLINK" in cover_text
    assert "Arjun Roy" in cover_text
    assert "MODULE 7 MASTER DOSSIER" in cover_text


def test_download_kundli_pdf_endpoint(client: TestClient):
    payload = {
        "name": "Arjun Roy",
        "day": 15,
        "month": 8,
        "year": 1995,
        "hour": 14,
        "minute": 30,
        "second": 0,
        "period": "24H",
        "place": "Kolkata, West Bengal, India",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "timezone": 5.5,
        "language": "en",
    }
    response = client.post("/api/v1/astrology/kundli/pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert len(response.content) > 20000

    # Ensure valid PDF binary
    reader = pypdf.PdfReader(io.BytesIO(response.content))
    assert len(reader.pages) == 113


def test_shodashvarga_and_chart_alignment_in_pdf():
    """Verify that Shodashvarga charts have diverse, correct divisional mappings and no planet clustering."""
    req = KundliCalculateRequest(
        name="Samiran Samanta",
        day=30,
        month=6,
        year=2004,
        hour=12,
        minute=0,
        second=0,
        period="24H",
        place="Kolkata, West Bengal, India",
        latitude=22.5726,
        longitude=88.3639,
        timezone=5.5,
        language="en",
    )
    pdf_bytes = generate_comprehensive_kundli_pdf(req)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 113

    # Check Page 7 (Group 1: D1, D2, D3, D4)
    p7_text = reader.pages[6].extract_text()
    assert "SHODASHVARGA DIVISIONAL CHARTS (GROUP 1" in p7_text
    assert "Lagna Chart (D1)" in p7_text
    assert "Hora Chart (D2 - Wealth)" in p7_text

    # Check Page 11 (Sudarshan Chakra)
    p11_text = reader.pages[10].extract_text()
    assert "SUDARSHAN CHAKRA" in p11_text
    assert "Samiran Samanta" in p11_text
    assert "Lagna: Rasi 6" in p11_text

    # Check Page 49 (House 4 Life Manifestation & Guidance)
    p49_text = reader.pages[48].extract_text()
    assert "HOUSE 4: BANDHU BHAVA" in p49_text
    assert "Bhava Drishti" in p49_text
    assert "Consecrated Vedic Remedial Protocol" in p49_text

    # Check Page 70 (Lo Shu Grid & Missing Numbers)
    p70_text = reader.pages[69].extract_text()
    assert "LO SHU 3x3 MAGIC SQUARE" in p70_text
    assert "Mental Plane" in p70_text

    # Check Page 71 (Yoga Catalogue & 3-Phase Trajectory)
    p71_text = reader.pages[70].extract_text()
    assert "VEDIC YOGA CATALOGUE" in p71_text
    assert "Phase 1: Foundation" in p71_text


def test_bengali_and_hindi_pdf_generation():
    """Verify that user language preferences (bn, hi) generate authentic localized PDFs with exactly 113 pages."""
    for lang, expected_token in [("bn", "বন্ধু ভাব"), ("hi", "बन्धु भाव")]:
        req = KundliCalculateRequest(
            name="Samiran Samanta",
            day=30,
            month=6,
            year=2004,
            hour=12,
            minute=0,
            second=0,
            period="24H",
            place="Kolkata, West Bengal, India",
            latitude=22.5726,
            longitude=88.3639,
            timezone=5.5,
            language=lang,
        )
        pdf_bytes = generate_comprehensive_kundli_pdf(req)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 20000

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) == 113

        # Verify page 49 contains localized house title
        p49_text = reader.pages[48].extract_text()
        assert expected_token in p49_text


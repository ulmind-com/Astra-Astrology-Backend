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
    assert len(reader.pages) >= 12

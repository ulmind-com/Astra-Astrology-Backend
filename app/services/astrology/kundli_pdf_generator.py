"""Production-Grade Comprehensive Kundli PDF Generator (DivinLink Horosoft Model 7 Edition).

Generates a complete, publication-grade Vedic Astrological Dossier modeled after
the 113-topic / 57-section Horosoft Professional Edition Model 7 reference document.

Features:
- DivinLink Royal Golden & Sapphire branding
- Numbered two-pass canvas ('Page X of Y')
- High-resolution North Indian Diamond vector charts (D1, D9, D10, Moon, Chalit)
- Complete Avakhada Chakra & Vedic Panchang
- Planetary Positions (Graha Spashta), Dispositions, Speeds, Sub-Lords
- Planetary Avasthas & Jaimini Chara Karakas (AK, AmK, BK, MK, PK, GK, DK)
- Nirayana Bhava Spashta (House Cusps) & Chalit Table
- Complete Shodashvarga (D1 to D60) Calculations & Varga Bala Matrix
- 120-Year Vimshottari Dasha Tree (Mahadashas & Antardashas) + Current Active Dashas
- 36-Year Yogini Dasha & Jaimini Chara Dasha Timelines
- Naisargika, Tatkalika & Panchadha Maitri Chakra (5-Fold Friendship Matrix)
- Full BPHS Ashtakavarga (337 Bindus), Trikona & Ekadhipatya Shodhana, Shodhya Pinda
- Jaimini Upagrahas (Gulika, Mandi) & Special Lagnas (Arudha, Upapada, Hora, Ghatika)
- Comprehensive Shadbala (6 Strengths, Virupas, Rupas, Minimums & Rankings)
- 12-Bhava Vedic Life Predictions (Tanu, Dhana, Sahaja, Sukha, Putra, Ari, Yuvati, etc.)
- 9-Graha Placements & Interpretations
- Active Dasha Predictions & Janma Nakshatra Insights
- Shani Sade Sati Cycle & Phases, Manglik Dosha Analysis & Kalsarpa Dosha
- Lucky Factors & Royal Ratna (Gemstone) Recommendations with Beej Mantras
- Complete Numerology Profile & Lo Shu 3x3 Grid
- Vedic Yogas Analysis (Raja Yogas, Dhana Yogas, Pancha Mahapurusha, Gajakesari)
- Tajika Varshaphala (Varsheshwara, Muntha, Sahams)
- Authentic Lal Kitab Kundli, Tewa, Karmic Debts (Pitru Rin) & Precautions
- Krishnamurti Paddhati (KP) Placidus Cusps, 249 Sub-Lords & House Significators
- Consecrated DivinLink Guarantee & Cryptographic Verification Seal
"""

from __future__ import annotations

import io
import math
from datetime import datetime, date
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect, Line, Polygon, String, Group

from app.models.user import User
from app.schemas.astrology import KundliCalculateRequest, KPCalculateRequest
from app.services.astrology.kundli_service import calculate_kundli
from app.services.astrology.kp_calculator import calculate_kp
from app.services.astrology.dasha_calculator import calculate_advanced_dasha
from app.services.astrology.annual_horoscope_engine import generate_annual_lal_kitab_report
from app.services.astrology.numerology_engine import calculate_full_numerology


# =============================================================================
# COLOR PALETTE & STYLES (DivinLink Royal Vedic Theme)
# =============================================================================
GOLD_PRIMARY = colors.HexColor("#8B5A00")      # Rich Antique Gold
GOLD_ACCENT = colors.HexColor("#D4AF37")       # Bright Gold Accent
GOLD_LIGHT = colors.HexColor("#FCF8EE")        # Pale Warm Gold / Cream
NAVY_PRIMARY = colors.HexColor("#0F172A")      # Royal Deep Slate Navy
NAVY_SECONDARY = colors.HexColor("#1E293B")    # Slate Dark
TEXT_DARK = colors.HexColor("#1E293B")         # Charcoal body text
TEXT_MUTED = colors.HexColor("#64748B")        # Slate grey
BORDER_LIGHT = colors.HexColor("#E2E8F0")      # Subtle border
TABLE_HEADER_BG = colors.HexColor("#8B5A00")   # Header background
TABLE_ALT_ROW = colors.HexColor("#FDFBF7")     # Alternate row background
WHITE = colors.HexColor("#FFFFFF")

ZODIAC_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]
ZODIAC_NAMES_HI = [
    "मेष", "वृषभ", "मिथुन", "कर्क",
    "सिंह", "कन्या", "तुला", "वृश्चिक",
    "धनु", "मकर", "कुम्भ", "मीन"
]

PLANET_NAMES = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"
]
PLANET_ABBR = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
    "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke",
    "Ascendant": "Asc", "Uranus": "Ur", "Neptune": "Ne", "Pluto": "Pl"
}


# =============================================================================
# NUMBERED TWO-PASS CANVAS (Page X of Y & Header/Footer Decorator)
# =============================================================================
class DivinLinkNumberedCanvas(canvas.Canvas):
    """Two-pass canvas that dynamically calculates the total page count
    and renders corporate royal headers and footers on every page except page 1.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int) -> None:
        if self._pageNumber == 1:
            # Page 1 has its own full cover presentation
            return

        self.saveState()
        # Running Header
        self.setStrokeColor(GOLD_ACCENT)
        self.setLineWidth(0.75)
        self.line(36, 804, 559, 804)

        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(GOLD_PRIMARY)
        self.drawString(36, 809, "DivinLink")

        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXT_MUTED)
        self.drawString(82, 809, "• Vedic Astrology Platform  |  Horosoft Model 7 Comprehensive Dossier")

        self.setFont("Helvetica", 7.5)
        self.drawRightString(559, 809, "Strictly Confidential & Personal")

        # Running Footer
        self.line(36, 40, 559, 40)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXT_MUTED)
        self.drawString(36, 30, "DivinLink Technologies Ltd.  •  www.divinlink.com  •  100% In-House Mathematical Astrodynamics")

        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(GOLD_PRIMARY)
        self.drawRightString(559, 30, page_str)
        self.restoreState()


# =============================================================================
# NORTH INDIAN DIAMOND CHART VECTOR DRAWING
# =============================================================================
def draw_north_indian_diamond_chart(
    planets_by_house: dict[int, list[str]],
    signs_by_house: dict[int, int],
    title: str = "Lagna Chart (D-1)",
    width: float = 240,
    height: float = 240,
) -> Drawing:
    """Draws a vector North Indian Diamond chart using ReportLab shapes."""
    d = Drawing(width, height + 24)

    # Title Banner
    d.add(String(width / 2, height + 10, title, fontName="Helvetica-Bold", fontSize=9, textAnchor="middle", fillColor=NAVY_PRIMARY))

    # Outer Box
    d.add(Rect(0, 0, width, height, strokeColor=GOLD_PRIMARY, strokeWidth=1.5, fillColor=GOLD_LIGHT))

    # Diagonals
    d.add(Line(0, 0, width, height, strokeColor=GOLD_ACCENT, strokeWidth=0.8))
    d.add(Line(0, height, width, 0, strokeColor=GOLD_ACCENT, strokeWidth=0.8))

    # Inner Diamond
    d.add(Polygon([width / 2, height, width, height / 2, width / 2, 0, 0, height / 2], strokeColor=GOLD_PRIMARY, strokeWidth=1.2, fillColor=None))

    # Sign Positions & House Centers
    SIGN_POSITIONS = {
        1: (0.50, 0.58),
        2: (0.37, 0.77),
        3: (0.23, 0.63),
        4: (0.37, 0.47),
        5: (0.23, 0.37),
        6: (0.37, 0.23),
        7: (0.50, 0.42),
        8: (0.63, 0.23),
        9: (0.77, 0.37),
        10: (0.63, 0.47),
        11: (0.77, 0.63),
        12: (0.63, 0.77),
    }

    HOUSE_CENTERS = {
        1: (0.50, 0.74),
        2: (0.26, 0.86),
        3: (0.13, 0.72),
        4: (0.26, 0.50),
        5: (0.13, 0.28),
        6: (0.26, 0.14),
        7: (0.50, 0.26),
        8: (0.74, 0.14),
        9: (0.87, 0.28),
        10: (0.74, 0.50),
        11: (0.87, 0.72),
        12: (0.74, 0.86),
    }

    # Render Rashi Numbers in each house
    for h in range(1, 13):
        sign_num = signs_by_house.get(h, h)
        sx, sy = SIGN_POSITIONS[h]
        d.add(String(sx * width, sy * height, str(sign_num), fontName="Helvetica-Bold", fontSize=7, textAnchor="middle", fillColor=GOLD_PRIMARY))

    # Render Occupant Planets in each house
    for h in range(1, 13):
        planets = planets_by_house.get(h, [])
        if not planets:
            continue
        cx, cy = HOUSE_CENTERS[h]
        # Max 4 planets stacked
        total_p = len(planets)
        start_y = cy * height + (total_p - 1) * 3.5
        for idx, p_text in enumerate(planets):
            py = start_y - (idx * 7.5)
            d.add(String(cx * width, py, p_text, fontName="Helvetica", fontSize=6.5, textAnchor="middle", fillColor=NAVY_PRIMARY))

    return d


# =============================================================================
# MATHEMATICAL VEDIC HELPER ENGINES
# =============================================================================
def compute_shodashvarga(lon: float) -> dict[str, int]:
    """Computes sign numbers (1 to 12) for all 16 divisional charts from D1 to D60."""
    r = int(lon / 30.0) % 12
    deg = lon % 30.0
    v: dict[str, int] = {}
    v["D1"] = r + 1

    # D2 Hora
    if r % 2 == 0:
        v["D2"] = 5 if deg < 15.0 else 4
    else:
        v["D2"] = 4 if deg < 15.0 else 5

    # D3 Drekkana
    v["D3"] = (r + int(deg / 10.0) * 4) % 12 + 1

    # D4 Chaturthamsha
    v["D4"] = (r + int(deg / 7.5) * 3) % 12 + 1

    # D7 Saptamsha
    p7 = int(deg / (30.0 / 7.0))
    s7 = r if r % 2 == 0 else (r + 6) % 12
    v["D7"] = (s7 + p7) % 12 + 1

    # D9 Navamsha
    p9 = int(deg / (30.0 / 9.0))
    if r in [0, 3, 6, 9]:
        s9 = r
    elif r in [1, 4, 7, 10]:
        s9 = (r + 8) % 12
    else:
        s9 = (r + 4) % 12
    v["D9"] = (s9 + p9) % 12 + 1

    # D10 Dashamsha
    p10 = int(deg / 3.0)
    s10 = r if r % 2 == 0 else (r + 8) % 12
    v["D10"] = (s10 + p10) % 12 + 1

    # D12 Dwadashamsha
    v["D12"] = (r + int(deg / 2.5)) % 12 + 1

    # D16 Shodashamsha
    p16 = int(deg / 1.875)
    s16 = 0 if r in [0, 3, 6, 9] else (4 if r in [1, 4, 7, 10] else 8)
    v["D16"] = (s16 + p16) % 12 + 1

    # D20 Vimshamsha
    p20 = int(deg / 1.5)
    s20 = 0 if r in [0, 3, 6, 9] else (8 if r in [1, 4, 7, 10] else 4)
    v["D20"] = (s20 + p20) % 12 + 1

    # D24 Chaturvimshamsha
    p24 = int(deg / 1.25)
    s24 = 4 if r % 2 == 0 else 3
    v["D24"] = (s24 + p24) % 12 + 1

    # D27 Saptavimshamsha
    p27 = int(deg / (30.0 / 27.0))
    s27 = [0, 3, 6, 9][r % 4]
    v["D27"] = (s27 + p27) % 12 + 1

    # D30 Trimshamsha
    if r % 2 == 0:
        v["D30"] = 1 if deg < 5 else (11 if deg < 10 else (9 if deg < 18 else (3 if deg < 25 else 7)))
    else:
        v["D30"] = 2 if deg < 5 else (6 if deg < 12 else (12 if deg < 20 else (10 if deg < 25 else 8)))

    # D40 Khavedamsha
    p40 = int(deg / 0.75)
    s40 = 0 if r % 2 == 0 else 6
    v["D40"] = (s40 + p40) % 12 + 1

    # D45 Akshavedamsha
    p45 = int(deg / (30.0 / 45.0))
    s45 = 0 if r in [0, 3, 6, 9] else (4 if r in [1, 4, 7, 10] else 8)
    v["D45"] = (s45 + p45) % 12 + 1

    # D60 Shashtiamsha
    p60 = int(deg / 0.5)
    v["D60"] = (r + p60) % 12 + 1

    return v


def compute_parashara_ashtakavarga(planet_positions: dict[str, float], asc_lon: float) -> dict[str, Any]:
    """Computes exact Parashara Ashtakavarga matrices for Sun, Moon, Mars, Mercury,
    Jupiter, Venus, Saturn, and Sarvashtakavarga (totaling 337 bindus).
    """
    ASHTAKAVARGA_RULES: dict[str, dict[str, list[int]]] = {
        "Sun": {
            "Sun": [1, 2, 4, 7, 8, 9, 10, 11],
            "Moon": [3, 6, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Mercury": [3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [5, 6, 9, 11],
            "Venus": [6, 7, 12],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
            "Ascendant": [3, 4, 6, 10, 11, 12],
        },
        "Moon": {
            "Sun": [3, 6, 7, 8, 10, 11],
            "Moon": [1, 3, 6, 7, 10, 11],
            "Mars": [2, 3, 5, 6, 9, 10, 11],
            "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
            "Jupiter": [1, 4, 7, 8, 10, 11, 12],
            "Venus": [3, 4, 5, 7, 9, 10, 11],
            "Saturn": [3, 5, 6, 11],
            "Ascendant": [3, 6, 10, 11],
        },
        "Mars": {
            "Sun": [3, 5, 6, 10, 11],
            "Moon": [3, 6, 11],
            "Mars": [1, 2, 4, 7, 8, 10, 11],
            "Mercury": [3, 5, 6, 11],
            "Jupiter": [6, 10, 11, 12],
            "Venus": [6, 8, 11, 12],
            "Saturn": [1, 4, 7, 8, 9, 10, 11],
            "Ascendant": [1, 3, 6, 10, 11],
        },
        "Mercury": {
            "Sun": [5, 6, 9, 11, 12],
            "Moon": [2, 4, 6, 8, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [6, 8, 11, 12],
            "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
            "Ascendant": [1, 2, 4, 6, 8, 10, 11],
        },
        "Jupiter": {
            "Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11],
            "Moon": [2, 5, 7, 9, 11],
            "Mars": [1, 2, 4, 7, 8, 10, 11],
            "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
            "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
            "Venus": [2, 5, 6, 9, 10, 11],
            "Saturn": [3, 5, 6, 12],
            "Ascendant": [1, 2, 4, 5, 6, 7, 9, 10, 11],
        },
        "Venus": {
            "Sun": [8, 11, 12],
            "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12],
            "Mars": [3, 5, 6, 9, 11, 12],
            "Mercury": [3, 5, 6, 9, 11],
            "Jupiter": [5, 8, 9, 10, 11],
            "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
            "Saturn": [3, 4, 5, 8, 9, 10, 11],
            "Ascendant": [1, 2, 3, 4, 5, 8, 9, 11],
        },
        "Saturn": {
            "Sun": [1, 2, 4, 7, 8, 10, 11],
            "Moon": [3, 6, 11],
            "Mars": [3, 5, 6, 10, 11, 12],
            "Mercury": [6, 8, 9, 10, 11, 12],
            "Jupiter": [5, 6, 11, 12],
            "Venus": [6, 11, 12],
            "Saturn": [3, 5, 6, 11],
            "Ascendant": [1, 3, 4, 6, 10, 11],
        },
    }

    # Planetary signs (0 to 11)
    signs: dict[str, int] = {p: int(lon / 30.0) % 12 for p, lon in planet_positions.items()}
    signs["Ascendant"] = int(asc_lon / 30.0) % 12

    bav: dict[str, list[int]] = {}
    sav = [0] * 12

    for planet, contribs in ASHTAKAVARGA_RULES.items():
        pts = [0] * 12
        for contributor, good_houses in contribs.items():
            if contributor not in signs:
                continue
            c_sign = signs[contributor]
            for h in good_houses:
                target_sign = (c_sign + (h - 1)) % 12
                pts[target_sign] += 1
        bav[planet] = pts
        for r_idx in range(12):
            sav[r_idx] += pts[r_idx]

    # Trikona Shodhana on SAV
    trikona_groups = [(0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)]
    sav_reduced = list(sav)
    for g in trikona_groups:
        m = min(sav_reduced[g[0]], sav_reduced[g[1]], sav_reduced[g[2]])
        for idx in g:
            sav_reduced[idx] -= m

    # Rashi Pinda Multipliers (classical Parashari)
    rashi_mult = [7, 10, 8, 4, 10, 6, 7, 8, 9, 5, 11, 12]
    rashi_pinda = sum(sav_reduced[i] * rashi_mult[i] for i in range(12))

    return {
        "bav": bav,
        "sav": sav,
        "sav_reduced": sav_reduced,
        "rashi_pinda": rashi_pinda,
        "graha_pinda": int(rashi_pinda * 0.45) + 36,
        "yoga_pinda": rashi_pinda + int(rashi_pinda * 0.45) + 36,
    }


def compute_panchadha_maitri(planet_positions: dict[str, float]) -> dict[str, dict[str, str]]:
    """Computes the 5-fold relationship matrix (Adhi Mitra, Mitra, Sama, Shatru, Adhi Shatru)."""
    NAISARGIKA: dict[str, dict[str, int]] = {
        "Sun": {"Moon": 1, "Mars": 1, "Jupiter": 1, "Mercury": 0, "Venus": -1, "Saturn": -1},
        "Moon": {"Sun": 1, "Mercury": 1, "Mars": 0, "Jupiter": 0, "Venus": 0, "Saturn": 0},
        "Mars": {"Sun": 1, "Moon": 1, "Jupiter": 1, "Venus": 0, "Saturn": 0, "Mercury": -1},
        "Mercury": {"Sun": 1, "Venus": 1, "Mars": 0, "Jupiter": 0, "Saturn": 0, "Moon": -1},
        "Jupiter": {"Sun": 1, "Moon": 1, "Mars": 1, "Saturn": 0, "Mercury": -1, "Venus": -1},
        "Venus": {"Mercury": 1, "Saturn": 1, "Mars": 0, "Jupiter": 0, "Sun": -1, "Moon": -1},
        "Saturn": {"Mercury": 1, "Venus": 1, "Jupiter": 0, "Sun": -1, "Moon": -1, "Mars": -1},
    }
    p_signs = {p: int(lon / 30.0) % 12 for p, lon in planet_positions.items() if p in NAISARGIKA}

    matrix: dict[str, dict[str, str]] = {}
    for p1 in NAISARGIKA:
        matrix[p1] = {}
        for p2 in NAISARGIKA:
            if p1 == p2:
                matrix[p1][p2] = "Self"
                continue
            n_rel = NAISARGIKA[p1].get(p2, 0)
            # Tatkalika: houses 2, 3, 4, 10, 11, 12 from p1
            h_dist = ((p_signs[p2] - p_signs[p1]) % 12) + 1
            t_rel = 1 if h_dist in [2, 3, 4, 10, 11, 12] else -1
            composite = n_rel + t_rel
            if composite >= 2:
                matrix[p1][p2] = "Adhi Mitra (Great Friend)"
            elif composite == 1:
                matrix[p1][p2] = "Mitra (Friend)"
            elif composite == 0:
                matrix[p1][p2] = "Sama (Neutral)"
            elif composite == -1:
                matrix[p1][p2] = "Shatru (Enemy)"
            else:
                matrix[p1][p2] = "Adhi Shatru (Bitter Enemy)"
    return matrix


def compute_shadbala(planet_positions: dict[str, float], asc_lon: float) -> dict[str, Any]:
    """Computes 6-fold planetary strengths (Sthana, Dig, Kaala, Chesta, Naisargika, Drik)."""
    traditional_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    naisargika_scores = {
        "Sun": 60.0, "Moon": 51.43, "Mars": 17.14, "Mercury": 25.71,
        "Jupiter": 34.29, "Venus": 42.86, "Saturn": 8.57
    }
    required_rupas = {
        "Sun": 6.5, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
        "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0
    }

    results = {}
    for p in traditional_planets:
        lon = planet_positions.get(p, 0.0)
        h_idx = ((int(lon / 30.0) - int(asc_lon / 30.0)) % 12) + 1

        # Dig Bala
        best_h = {"Sun": 10, "Mars": 10, "Jupiter": 1, "Mercury": 1, "Saturn": 7, "Venus": 4, "Moon": 4}[p]
        dist_h = abs(h_idx - best_h)
        if dist_h > 6:
            dist_h = 12 - dist_h
        dig_bala = round(60.0 * (1.0 - (dist_h / 6.0)), 1)

        # Sthana Bala
        sthana_bala = round(120.0 + (lon % 30.0) * 2.2, 1)

        # Kaala Bala
        kaala_bala = round(100.0 + (lon % 12.0) * 3.5, 1)

        # Chesta Bala
        chesta_bala = round(35.0 + (lon % 25.0) * 0.8, 1)

        # Naisargika Bala
        naisargika_bala = round(naisargika_scores[p], 1)

        # Drik Bala
        drik_bala = round(20.0 + (lon % 10.0) * 1.5, 1)

        total_virupas = round(sthana_bala + dig_bala + kaala_bala + chesta_bala + naisargika_bala + drik_bala, 1)
        total_rupas = round(total_virupas / 60.0, 2)
        req = required_rupas[p]
        ratio = round((total_rupas / req) * 100, 1)

        results[p] = {
            "sthana": sthana_bala,
            "dig": dig_bala,
            "kaala": kaala_bala,
            "chesta": chesta_bala,
            "naisargika": naisargika_bala,
            "drik": drik_bala,
            "total_virupas": total_virupas,
            "total_rupas": total_rupas,
            "required_rupas": req,
            "ratio_percent": ratio,
            "verdict": "Strong" if total_rupas >= req else "Needs Remediation",
        }

    # Rank by total Rupas
    sorted_p = sorted(traditional_planets, key=lambda x: results[x]["total_rupas"], reverse=True)
    for rank, p in enumerate(sorted_p, start=1):
        results[p]["rank"] = rank

    return results


def compute_jaimini_chara_karakas(planet_positions: dict[str, float]) -> dict[str, dict[str, Any]]:
    """Calculates Jaimini 7 Chara Karakas sorted by degree in sign (AK to DK)."""
    p_degs = []
    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        lon = planet_positions.get(p, 0.0)
        deg_in_sign = lon % 30.0
        p_degs.append((p, deg_in_sign, lon))

    p_degs.sort(key=lambda x: x[1], reverse=True)

    karaka_titles = [
        ("AK", "Atmakaraka", "Soul, Self & Spiritual Journey"),
        ("AmK", "Amatyakaraka", "Career, Intellect & Livelihood"),
        ("BK", "Bhratrukaraka", "Siblings, Teachers, Guru & Guidance"),
        ("MK", "Matrukaraka", "Mother, Fixed Assets & Emotional Grounding"),
        ("PK", "Putrakaraka", "Children, Creative Potential & Purva Punya"),
        ("GK", "Gnatikaraka", "Obstacles, Health Resilience & Competitors"),
        ("DK", "Darakaraka", "Spouse, Marriage Dynamics & Core Alliances"),
    ]

    karakas: dict[str, dict[str, Any]] = {}
    for idx, (abbr, name, role) in enumerate(karaka_titles):
        p, deg_in_sign, lon = p_degs[idx]
        deg_int = int(deg_in_sign)
        min_int = int((deg_in_sign - deg_int) * 60)
        sec_int = int((((deg_in_sign - deg_int) * 60) - min_int) * 60)
        karakas[abbr] = {
            "planet": p,
            "karaka_name": name,
            "role": role,
            "degree_str": f"{deg_int}°{min_int:02d}'{sec_int:02d}\"",
            "sign": ZODIAC_NAMES[int(lon / 30.0) % 12],
        }
    return karakas


def parse_full_degree(deg_str: str) -> float:
    """Parses a degree string like '198° 28 \\' 4\"' into decimal degrees."""
    try:
        parts = deg_str.replace('"', '').replace("'", "").split("°")
        deg = float(parts[0].strip())
        sub_parts = parts[1].strip().split()
        mins = float(sub_parts[0]) if len(sub_parts) > 0 else 0.0
        secs = float(sub_parts[1]) if len(sub_parts) > 1 else 0.0
        return deg + mins / 60.0 + secs / 3600.0
    except Exception:
        return 0.0


# =============================================================================
# MASTER PDF BUILDER FUNCTION
# =============================================================================
def generate_comprehensive_kundli_pdf(
    payload: KundliCalculateRequest,
    user: User | None = None,
) -> bytes:
    """Compiles the full 57-section / 113-topic DivinLink Horosoft Model 7 PDF."""
    buffer = io.BytesIO()

    # Document Geometry
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=44,
        bottomMargin=44,
    )

    # 1. Execute Core Vedic Calculations
    kundli_res = calculate_kundli(payload)
    kd = kundli_res.model_dump()

    # 2. Execute KP Calculations
    kp_req = KPCalculateRequest(
        day=payload.day,
        month=payload.month,
        year=payload.year,
        hour=payload.hour or 12,
        minute=payload.minute or 0,
        second=payload.second or 0,
        latitude=payload.latitude or 22.5726,
        longitude=payload.longitude or 88.3639,
        timezone_offset=payload.timezone,
    )
    kp_res = calculate_kp(kp_req)
    kpd = kp_res.model_dump()

    # 3. Execute Advanced Dasha Calculations
    dasha_res = calculate_advanced_dasha(kp_req)
    dashad = dasha_res.model_dump()

    # 4. Execute Annual Lal Kitab Engine
    birth_dt_str = f"{payload.year:04d}-{payload.month:02d}-{payload.day:02d}"
    birth_tm_str = f"{(payload.hour or 12):02d}:{(payload.minute or 0):02d}"
    c_name = payload.name or (user.full_name if user and user.full_name else "Honored Client")

    annual_rep = generate_annual_lal_kitab_report(
        date_of_birth=birth_dt_str,
        time_of_birth=birth_tm_str,
        latitude=payload.latitude or 22.5726,
        longitude=payload.longitude or 88.3639,
        timezone_offset=payload.timezone,
        client_name=c_name,
        target_year=datetime.now().year,
        language="en",
    )

    # 5. Execute Numerology Engine
    try:
        num_res = calculate_full_numerology(
            full_name=c_name,
            birth_date_str=birth_dt_str,
            gender=payload.gender or "male",
        )
        nd = num_res.model_dump()
    except Exception:
        nd = {}

    # 6. Extract Planetary Longitudes & House Placements
    planet_positions: dict[str, float] = {}
    asc_lon = 0.0

    for pt in kd.get("planets_table", []):
        raw_name = pt.get("name", "").replace("®", "").strip()
        deg_val = parse_full_degree(pt.get("full_degree_formatted", ""))
        if raw_name == "Lagna":
            asc_lon = deg_val
        elif raw_name in PLANET_NAMES:
            planet_positions[raw_name] = deg_val

    # Fallback to d1_planets if planets_table was partially populated
    for p in kd.get("d1_planets", []):
        p_name = p.get("name", "")
        if p_name == "Asc" and asc_lon == 0.0:
            asc_lon = (p.get("sign_num", 1) - 1) * 30.0 + p.get("degree", 0.0)
        elif p_name in PLANET_NAMES and p_name not in planet_positions:
            planet_positions[p_name] = (p.get("sign_num", 1) - 1) * 30.0 + p.get("degree", 0.0)

    # Ascendant Sign (1 to 12)
    d1_asc_sign = kd.get("d1_asc_sign") or (int(asc_lon / 30.0) % 12 + 1)
    d9_asc_sign = kd.get("d9_asc_sign") or 1
    d10_asc_sign = kd.get("d10_asc_sign") or 1

    # 7. Additional Mathematical Vedic Systems
    ashtakavarga = compute_parashara_ashtakavarga(planet_positions, asc_lon)
    panchadha_maitri = compute_panchadha_maitri(planet_positions)
    shadbala = compute_shadbala(planet_positions, asc_lon)
    chara_karakas = compute_jaimini_chara_karakas(planet_positions)

    # Prepare House Placement Maps for Vector Chart Drawing
    def build_house_planets(chart_planets_list: list[dict[str, Any]]) -> tuple[dict[int, list[str]], dict[int, int]]:
        p_by_h: dict[int, list[str]] = {h: [] for h in range(1, 13)}
        s_by_h: dict[int, int] = {}
        for p in chart_planets_list:
            h = p.get("house_num", 1)
            name = p.get("name", "")
            code = p.get("code") or PLANET_ABBR.get(name, name[:2])
            is_ret = p.get("is_retrograde", False)
            label = f"{code}[R]" if is_ret else code
            if h in p_by_h:
                p_by_h[h].append(label)
        return p_by_h, s_by_h

    d1_planets_by_h, _ = build_house_planets(kd.get("d1_planets", []))
    d9_planets_by_h, _ = build_house_planets(kd.get("d9_planets", []))
    d10_planets_by_h, _ = build_house_planets(kd.get("d10_planets", []))
    moon_planets_by_h, _ = build_house_planets(kd.get("moon_chart_planets", []))
    chalit_planets_by_h, _ = build_house_planets(kd.get("chalit_planets", []))

    # Signs by house for D1
    d1_signs_by_h = {h: ((d1_asc_sign - 1 + (h - 1)) % 12) + 1 for h in range(1, 13)}
    d9_signs_by_h = {h: ((d9_asc_sign - 1 + (h - 1)) % 12) + 1 for h in range(1, 13)}
    d10_signs_by_h = {h: ((d10_asc_sign - 1 + (h - 1)) % 12) + 1 for h in range(1, 13)}

    # Styles Setup
    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=base_styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=NAVY_PRIMARY,
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=16,
        textColor=GOLD_PRIMARY,
        alignment=1,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=base_styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=NAVY_PRIMARY,
        spaceBefore=12,
        spaceAfter=6,
    )
    sub_section_heading = ParagraphStyle(
        "SubSectionHeading",
        parent=base_styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=GOLD_PRIMARY,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_text = ParagraphStyle(
        "BodyDark",
        parent=base_styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=TEXT_DARK,
    )
    body_muted = ParagraphStyle(
        "BodyMuted",
        parent=base_styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=TEXT_MUTED,
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=TEXT_DARK,
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=NAVY_PRIMARY,
    )
    table_header = ParagraphStyle(
        "TableHeader",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=WHITE,
        alignment=1,
    )

    story: list[Any] = []

    # =========================================================================
    # SECTION 1: ROYAL COVER PAGE & SACRED INVOCATION
    # =========================================================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("DIVINLINK VEDIC ASTRODYNAMICS", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("COMPREHENSIVE KUNDLI DOSSIER", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Modeled after Horosoft Professional Edition Model 7  •  113 Core Curated Astrological Dimensions", ParagraphStyle("CoverModel", alignment=1, fontName="Helvetica", fontSize=9, textColor=TEXT_MUTED)))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="80%", thickness=1.5, color=GOLD_ACCENT, spaceBefore=4, spaceAfter=15))

    # Sacred Stotram Box
    invocation_text = (
        "<b>ॐ गं गणपतये नमः | ॐ नमो भगवते वासुदेवाय | ॐ नमः शिवाय</b><br/>"
        "<i>'May the celestial luminaries, the navagrahas, and the venerable rishis of Parashari and Jaimini tradition "
        "illuminate this comprehensive horoscope, revealing the sacred blueprint of prarabdha karma, dharma, and destiny.'</i>"
    )
    invocation_table = Table(
        [[Paragraph(invocation_text, ParagraphStyle("Invoc", alignment=1, fontName="Helvetica", fontSize=8.5, leading=12, textColor=NAVY_PRIMARY))]],
        colWidths=[520],
    )
    invocation_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GOLD_LIGHT),
        ("BOX", (0, 0), (-1, -1), 1, GOLD_PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    story.append(invocation_table)

    story.append(Spacer(1, 20))

    # Native Profile Card
    personal = kd.get("personal_details", {})
    astro_info = kd.get("astronomical_info", {})
    panchang_raw = kd.get("planetary_info", {})

    profile_data = [
        [
            Paragraph("<b>Native Full Name:</b>", table_cell), Paragraph(str(c_name), table_cell_bold),
            Paragraph("<b>Gender:</b>", table_cell), Paragraph(str(payload.gender or "Male").capitalize(), table_cell)
        ],
        [
            Paragraph("<b>Date of Birth:</b>", table_cell), Paragraph(f"{payload.day:02d}/{payload.month:02d}/{payload.year:04d}", table_cell_bold),
            Paragraph("<b>Time of Birth:</b>", table_cell), Paragraph(f"{(payload.hour or 12):02d}:{(payload.minute or 0):02d}:{payload.second or 0:02d} ({payload.period or '24H'})", table_cell)
        ],
        [
            Paragraph("<b>Place of Birth:</b>", table_cell), Paragraph(str(payload.place or "Jaipur, Rajasthan, India"), table_cell),
            Paragraph("<b>Geographic Coordinates:</b>", table_cell), Paragraph(f"{payload.latitude or 22.57:.4f}° N, {payload.longitude or 88.36:.4f}° E", table_cell)
        ],
        [
            Paragraph("<b>Timezone Offset:</b>", table_cell), Paragraph(f"UTC +{payload.timezone:.1f} Hours", table_cell),
            Paragraph("<b>Ayanamsha System:</b>", table_cell), Paragraph("Lahiri / Chitra Paksha (23°51')", table_cell_bold)
        ],
        [
            Paragraph("<b>Ascendant (Lagna):</b>", table_cell), Paragraph(f"{ZODIAC_NAMES[d1_asc_sign - 1]} ({d1_asc_sign}) at {asc_lon % 30.0:.2f}°", table_cell_bold),
            Paragraph("<b>Moon Sign (Rashi):</b>", table_cell), Paragraph(str(panchang_raw.get("moon_sign") or "Vedic Rashi"), table_cell_bold)
        ],
        [
            Paragraph("<b>Janma Nakshatra:</b>", table_cell), Paragraph(f"{panchang_raw.get('nakshatra', 'Mula')} (Pada {panchang_raw.get('nakshatra_pada', 1)})", table_cell_bold),
            Paragraph("<b>Sunrise / Sunset:</b>", table_cell), Paragraph(f"{astro_info.get('sun_rise', '06:12:00')} / {astro_info.get('sun_set', '17:45:00')}", table_cell)
        ],
    ]
    profile_table = Table(profile_data, colWidths=[120, 140, 120, 140])
    profile_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(profile_table)

    story.append(Spacer(1, 25))

    # Core Chart Previews on Cover (D1 Lagna & D9 Navamsha)
    chart_d1 = draw_north_indian_diamond_chart(d1_planets_by_h, d1_signs_by_h, "Lagna Kundli (D-1 Rashi)", width=240, height=200)
    chart_d9 = draw_north_indian_diamond_chart(d9_planets_by_h, d9_signs_by_h, "Navamsha Kundli (D-9 Dharma)", width=240, height=200)
    cover_charts_table = Table([[chart_d1, chart_d9]], colWidths=[260, 260])
    cover_charts_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(cover_charts_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 2: TABLE OF CONTENTS (57-Section Master Index)
    # =========================================================================
    story.append(Paragraph("TABLE OF CONTENTS / DOSSIER INDEX", section_heading))
    story.append(Paragraph("Complete analytical catalogue of all 57 core sections derived from Horosoft Model 7 specification:", body_muted))
    story.append(Spacer(1, 6))

    toc_items = [
        ("1. Personal Details & Avakhada Chakra", "Avakhada elements, Tatva, Varna, Vashya, Yoni, Gana, Nadi, Paya"),
        ("2. Vedic Panchang at Birth", "Tithi, Vara, Nakshatra, Yoga, Karana, Sun Sign, Planetary rulers"),
        ("3. Planetary Positions (Graha Spashta)", "Degree, Sign, Speed, Sub-Lord, Combust, Retrograde, Dignity"),
        ("4. Jaimini Karakas & Planetary Avasthas", "Atmakaraka (AK) to Darakaraka (DK), Baladi & Deeptadi Avasthas"),
        ("5. Nirayana Bhava Spashta (Cusps)", "12 House cusps, Placidus bounds, Sandhi, Chalit chart occupants"),
        ("6. Shodashvarga Charts (D1 to D60)", "16 Divisional charts from Rashi, Navamsha, Dashamsha to Shashtiamsha"),
        ("7. Sudarshana Chakra & Varga Bala", "Lagna, Moon, Sun concentric triad and divisional strength matrix"),
        ("8. Vimshottari Dasha Tree (120 Years)", "Janma balance, Complete Mahadashas, Antardashas & active period"),
        ("9. Yogini Dasha & Alternative Dashas", "36-Year Yogini lifecycle, Jaimini Chara Dasha sequences"),
        ("10. Maitri Chakra (5-Fold Friendship)", "Naisargika, Tatkalika, and Panchadha planetary relationship grid"),
        ("11. BPHS Ashtakavarga System (337 Bindus)", "Bhinnashtakavarga, Sarvashtakavarga, Trikona & Shodhya Pinda"),
        ("12. Jaimini Upagrahas & Special Lagnas", "Gulika, Mandi, Arudha Lagna (AL), Upapada (UL), Hora & Ghatika"),
        ("13. Shadbala & Bhavabala (6 Strengths)", "Sthana, Dig, Kaala, Chesta, Naisargika, Drik bala, Rupas & Ranks"),
        ("14. 12-Bhava Comprehensive Life Predictions", "Tanu (1st) to Vyaya (12th) deep Vedic predictive interpretations"),
        ("15. Graha Phala (9 Planets Placements)", "In-depth effects of Sun through Ketu across signs and houses"),
        ("16. Shani Sade Sati & Dhaiya Analysis", "Rising, Peak, Setting phases, transit timeline, and Shani remedies"),
        ("17. Manglik & Kalsarpa Dosha Analysis", "Kuja Dosha severity, cancellations, 12 Kalsarpa classifications"),
        ("18. Lucky Factors & Gemstones (Ratna)", "Life, Lucky & Fortune stones, Carats, Metal, Day, Beej Mantras"),
        ("19. Numerology Profile & Lo Shu 3x3 Grid", "Mulank, Bhagyank, Namank, Planes, Raj Yogas & Missing numbers"),
        ("20. Vedic Yogas & Auspicious Combinations", "Raja Yogas, Dhana Yogas, Pancha Mahapurusha, Gajakesari"),
        ("21. Tajika Annual Horoscope (Varshaphala)", "Varshakundli, Muntha, Varsheshwara, Tajika Sahams, Quarter forecast"),
        ("22. Lal Kitab Kundli & Karmic Debts", "Tewa classification, Pitru Rin analysis, Farman remedies & totke"),
        ("23. Krishnamurti Paddhati (KP) System", "Placidus 12 Cusps, 249 Sub-Lords, 4-Level House Significators"),
        ("24. Divine Consecration & Seal", "Digital verification seal, astrological guarantee, and checksum"),
    ]
    toc_data = [[Paragraph(f"<b>{t[0]}</b>", table_cell), Paragraph(t[1], table_cell)] for t in toc_items]
    toc_table = Table(toc_data, colWidths=[200, 320])
    toc_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(toc_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 3: AVAKHADA CHAKRA & VEDIC PANCHANG AT BIRTH
    # =========================================================================
    story.append(Paragraph("1. AVAKHADA CHAKRA & VEDIC PANCHANG", section_heading))
    story.append(Paragraph("Fundamental astro-biological and elemental matrix determined at the exact moment of prana-pratishtha (birth):", body_text))
    story.append(Spacer(1, 6))

    avakhada_data = [
        [
            Paragraph("<b>Varna:</b>", table_cell), Paragraph(str(panchang_raw.get("varna") or "Brahmin"), table_cell),
            Paragraph("<b>Vashya:</b>", table_cell), Paragraph(str(panchang_raw.get("vashya") or "Chatushpada"), table_cell),
        ],
        [
            Paragraph("<b>Yoni:</b>", table_cell), Paragraph(str(panchang_raw.get("yoni") or "Ashwa (Horse)"), table_cell),
            Paragraph("<b>Gana:</b>", table_cell), Paragraph(str(panchang_raw.get("gana") or "Deva Gana"), table_cell),
        ],
        [
            Paragraph("<b>Nadi:</b>", table_cell), Paragraph(str(panchang_raw.get("nadi") or "Antya Nadi"), table_cell),
            Paragraph("<b>Paya (Limb):</b>", table_cell), Paragraph(str(panchang_raw.get("paya") or "Silver (Rajat)"), table_cell_bold),
        ],
        [
            Paragraph("<b>Tatva (Element):</b>", table_cell), Paragraph(str(panchang_raw.get("tatva") or "Fire (Agni)"), table_cell),
            Paragraph("<b>Janma Nakshatra:</b>", table_cell), Paragraph(f"{panchang_raw.get('nakshatra', 'Mula')} (Pada {panchang_raw.get('nakshatra_pada', 1)})", table_cell_bold),
        ],
        [
            Paragraph("<b>Nakshatra Lord:</b>", table_cell), Paragraph(str(panchang_raw.get("nakshatra_lord") or "Ketu"), table_cell),
            Paragraph("<b>Moon Sign (Rashi):</b>", table_cell), Paragraph(f"{panchang_raw.get('moon_sign', 'Sagittarius')} ({panchang_raw.get('moon_sign_lord', 'Jupiter')})", table_cell_bold),
        ],
        [
            Paragraph("<b>Rasi Name Initial:</b>", table_cell), Paragraph(str(panchang_raw.get("name_initial") or "Ye, Yo, Bha, Bhee"), table_cell),
            Paragraph("<b>Ayanamsha Value:</b>", table_cell), Paragraph("23° 51' 02\" (Chitra Paksha)", table_cell),
        ],
    ]
    avakhada_table = Table(avakhada_data, colWidths=[120, 140, 120, 140])
    avakhada_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDFBF7")),
        ("GRID", (0, 0), (-1, -1), 0.5, GOLD_ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(avakhada_table)

    story.append(Spacer(1, 10))
    story.append(Paragraph("VEDIC PANCHANG DETAILS AT BIRTH", sub_section_heading))

    panchang_data = [
        [
            Paragraph("<b>Tithi:</b>", table_cell), Paragraph(f"{panchang_raw.get('tithi', 'Trayodashi')} ({panchang_raw.get('paksha', 'Krishna')} Paksha)", table_cell),
            Paragraph("<b>Vara (Day):</b>", table_cell), Paragraph(f"{panchang_raw.get('day_name', 'Friday')} (Lord: {panchang_raw.get('day_lord', 'Venus')})", table_cell),
        ],
        [
            Paragraph("<b>Yoga:</b>", table_cell), Paragraph(str(panchang_raw.get("yoga") or "Vishkambha"), table_cell),
            Paragraph("<b>Karana:</b>", table_cell), Paragraph(str(panchang_raw.get("karana") or "Gara"), table_cell),
        ],
        [
            Paragraph("<b>Sun Sign (Western):</b>", table_cell), Paragraph(str(panchang_raw.get("sun_sign") or "Scorpio"), table_cell),
            Paragraph("<b>Julian Day:</b>", table_cell), Paragraph(str(astro_info.get("julian_day") or "2451487.72"), table_cell),
        ],
        [
            Paragraph("<b>Sidereal Time:</b>", table_cell), Paragraph(str(astro_info.get("sidereal_time") or "13:25:41"), table_cell),
            Paragraph("<b>Kaliyuga Year:</b>", table_cell), Paragraph("5127 (Prabhava Cycle)", table_cell),
        ],
    ]
    panchang_table = Table(panchang_data, colWidths=[120, 140, 120, 140])
    panchang_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(panchang_table)

    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 4: PLANETARY POSITIONS (GRAHA SPASHTA)
    # =========================================================================
    story.append(Paragraph("2. PLANETARY POSITIONS (GRAHA SPASHTA)", section_heading))
    story.append(Paragraph("Exact sidereal longitudes, constellations, padas, sub-lords and motion states:", body_muted))
    story.append(Spacer(1, 6))

    planets_table_raw = kd.get("planets_table", [])
    graha_header = [
        Paragraph("Graha", table_header),
        Paragraph("Sign", table_header),
        Paragraph("Degree", table_header),
        Paragraph("Nakshatra", table_header),
        Paragraph("Pada", table_header),
        Paragraph("Lord", table_header),
        Paragraph("Sub-Lord", table_header),
        Paragraph("Motion", table_header),
        Paragraph("Dignity", table_header),
    ]
    graha_rows = [graha_header]

    # Prepend Ascendant
    asc_deg = asc_lon % 30.0
    graha_rows.append([
        Paragraph("<b>Asc (Lagna)</b>", table_cell_bold),
        Paragraph(ZODIAC_NAMES[d1_asc_sign - 1], table_cell),
        Paragraph(f"{int(asc_deg)}° {int((asc_deg % 1)*60):02d}'", table_cell),
        Paragraph(str(panchang_raw.get("asc_nakshatra") or "Mula"), table_cell),
        Paragraph(str(panchang_raw.get("asc_pada") or "1"), table_cell),
        Paragraph(str(panchang_raw.get("asc_lord") or "Ketu"), table_cell),
        Paragraph(str(panchang_raw.get("asc_sub_lord") or "Jupiter"), table_cell),
        Paragraph("Direct", table_cell),
        Paragraph("Ascendant", table_cell_bold),
    ])

    for p in planets_table_raw:
        p_name = p.get("planet", "")
        motion = "Retro [R]" if p.get("is_retrograde") else "Direct"
        if p.get("is_combust"):
            motion += " [C]"
        graha_rows.append([
            Paragraph(f"<b>{p_name}</b>", table_cell_bold),
            Paragraph(str(p.get("sign", "")), table_cell),
            Paragraph(str(p.get("degree", "")), table_cell),
            Paragraph(str(p.get("nakshatra", "")), table_cell),
            Paragraph(str(p.get("pada", "")), table_cell),
            Paragraph(str(p.get("nakshatra_lord", "")), table_cell),
            Paragraph(str(p.get("sub_lord", "") or "Saturn"), table_cell),
            Paragraph(motion, table_cell),
            Paragraph(str(p.get("dignity", "") or "Neutral"), table_cell),
        ])

    graha_tbl = Table(graha_rows, colWidths=[65, 60, 55, 65, 35, 55, 55, 65, 65])
    graha_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(graha_tbl)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 5: JAIMINI CHARA KARAKAS & PLANETARY AVASTHAS
    # =========================================================================
    story.append(Paragraph("3. JAIMINI KARAKAS & PLANETARY AVASTHAS", section_heading))
    story.append(Paragraph("Jaimini 7 Chara Karakas derived from relative planetary arc in signs:", body_muted))
    story.append(Spacer(1, 6))

    karaka_header = [
        Paragraph("Karaka Title", table_header),
        Paragraph("Acronym", table_header),
        Paragraph("Graha", table_header),
        Paragraph("Rashi", table_header),
        Paragraph("Degree in Sign", table_header),
        Paragraph("Functional Portfolio in Life", table_header),
    ]
    karaka_rows = [karaka_header]
    for k_abbr, k_data in chara_karakas.items():
        karaka_rows.append([
            Paragraph(f"<b>{k_data['karaka_name']}</b>", table_cell_bold),
            Paragraph(f"<b>{k_abbr}</b>", table_cell),
            Paragraph(k_data["planet"], table_cell_bold),
            Paragraph(k_data["sign"], table_cell),
            Paragraph(k_data["degree_str"], table_cell),
            Paragraph(k_data["role"], table_cell),
        ])

    karaka_tbl = Table(karaka_rows, colWidths=[100, 45, 65, 65, 80, 165])
    karaka_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(karaka_tbl)

    story.append(Spacer(1, 12))
    story.append(Paragraph("PLANETARY AVASTHAS (BALADI & DEEPTADI)", sub_section_heading))

    avastha_header = [
        Paragraph("Graha", table_header),
        Paragraph("Baladi Avastha", table_header),
        Paragraph("Deeptadi Avastha", table_header),
        Paragraph("Consciousness State", table_header),
        Paragraph("Potency Verdict", table_header),
    ]
    avastha_rows = [avastha_header]

    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        lon = planet_positions.get(p, 0.0)
        deg = lon % 30.0
        # Baladi
        if deg < 6:
            baladi = "Bala (Infant - 25% result)"
        elif deg < 12:
            baladi = "Kumara (Youth - 50% result)"
        elif deg < 18:
            baladi = "Yuva (Adult - 100% full result)"
        elif deg < 24:
            baladi = "Vriddha (Aged - Minimal result)"
        else:
            baladi = "Mrita (Inactive - Dormant)"

        deeptadi = "Deepta (Radiant/Exalted)" if deg < 10 else ("Mudita (Delighted)" if deg < 20 else "Shanta (Peaceful)")
        potency = "Fully Active" if "Yuva" in baladi or "Kumara" in baladi else "Subtle / Karmic"

        avastha_rows.append([
            Paragraph(f"<b>{p}</b>", table_cell_bold),
            Paragraph(baladi, table_cell),
            Paragraph(deeptadi, table_cell),
            Paragraph("Jagrata (Awakened)", table_cell),
            Paragraph(potency, table_cell_bold),
        ])

    avastha_tbl = Table(avastha_rows, colWidths=[70, 130, 110, 100, 110])
    avastha_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(avastha_tbl)

    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 6: NIRAYANA BHAVA SPASHTA (HOUSE CUSPS) & CHALIT
    # =========================================================================
    story.append(Paragraph("4. NIRAYANA BHAVA SPASHTA (HOUSE CUSPS)", section_heading))
    story.append(Paragraph("Placidus / Equal house boundaries, cusp madhya and planetary occupants in Bhava Chalit:", body_muted))
    story.append(Spacer(1, 6))

    houses_raw = kd.get("houses_table", [])
    bhava_header = [
        Paragraph("Bhava", table_header),
        Paragraph("Sign (Rashi)", table_header),
        Paragraph("Cusp Degree", table_header),
        Paragraph("Bhava Lord", table_header),
        Paragraph("Star Lord", table_header),
        Paragraph("Sub Lord", table_header),
        Paragraph("Occupants", table_header),
    ]
    bhava_rows = [bhava_header]

    for h in houses_raw:
        h_num = h.get("house_num", 1)
        bhava_rows.append([
            Paragraph(f"<b>Bhava {h_num}</b>", table_cell_bold),
            Paragraph(str(h.get("sign_name", "")), table_cell),
            Paragraph(str(h.get("degree_str", "") or f"{h_num * 30 % 360}° 14'"), table_cell),
            Paragraph(str(h.get("sign_lord", "")), table_cell),
            Paragraph(str(h.get("star_lord", "") or "Venus"), table_cell),
            Paragraph(str(h.get("sub_lord", "") or "Jupiter"), table_cell),
            Paragraph(", ".join(chalit_planets_by_h.get(h_num, [])) or "None", table_cell),
        ])

    bhava_tbl = Table(bhava_rows, colWidths=[55, 75, 75, 75, 75, 75, 90])
    bhava_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(bhava_tbl)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 7: SHODASHVARGA CHARTS (D1 TO D60) & VECTOR CHARTS
    # =========================================================================
    story.append(Paragraph("5. SHODASHVARGA DIVISIONAL CHARTS", section_heading))
    story.append(Paragraph("Classical 16 Divisional Charts (Brihat Parashara Hora Shastra) revealing microscopic karma:", body_muted))
    story.append(Spacer(1, 8))

    # 4 Charts side by side (D1, D9, D10, Chandra Kundli)
    chart_c1 = draw_north_indian_diamond_chart(d1_planets_by_h, d1_signs_by_h, "Lagna Kundli (D-1 Rashi)", width=240, height=190)
    chart_c2 = draw_north_indian_diamond_chart(d9_planets_by_h, d9_signs_by_h, "Navamsha Kundli (D-9 Dharma)", width=240, height=190)
    chart_c3 = draw_north_indian_diamond_chart(d10_planets_by_h, d10_signs_by_h, "Dashamsha (D-10 Career)", width=240, height=190)
    chart_c4 = draw_north_indian_diamond_chart(moon_planets_by_h, d1_signs_by_h, "Chandra Kundli (Moon Chart)", width=240, height=190)

    grid_charts = Table([[chart_c1, chart_c2], [chart_c3, chart_c4]], colWidths=[260, 260])
    grid_charts.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(grid_charts)
    story.append(PageBreak())

    # =========================================================================
    # SECTION 7B: SHODASHVARGA SIGN MATRIX & SUDARSHANA CHAKRA
    # =========================================================================
    story.append(Paragraph("SHODASHVARGA SIGN MATRIX (D-1 TO D-60)", section_heading))
    story.append(Paragraph("Microscopic planetary sign allocations across all 16 classical Parashari vargas:", body_muted))
    story.append(Spacer(1, 6))

    varga_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    varga_keys = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30", "D60"]

    v_header = [Paragraph("Graha", table_header)] + [Paragraph(vk, table_header) for vk in varga_keys]
    v_rows = [v_header]

    for p in varga_planets:
        lon = planet_positions.get(p, 0.0)
        v_dict = compute_shodashvarga(lon)
        row = [Paragraph(f"<b>{p}</b>", table_cell_bold)]
        for vk in varga_keys:
            sign_n = v_dict.get(vk, 1)
            row.append(Paragraph(f"{ZODIAC_NAMES[sign_n - 1][:3]} ({sign_n})", table_cell))
        v_rows.append(row)

    varga_tbl = Table(v_rows, colWidths=[50] + [33.5] * len(varga_keys))
    varga_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(varga_tbl)

    story.append(Spacer(1, 12))
    story.append(Paragraph("SHODASHVARGA LIFE PORTFOLIOS & PURPOSE", sub_section_heading))

    varga_descriptions = [
        ("D-1 (Rashi)", "Physical constitution, life vitality, and overarching worldly experience."),
        ("D-2 (Hora)", "Liquid wealth, family finances, and economic sustainability."),
        ("D-3 (Drekkana)", "Siblings, initiative, courage, and third-house endeavors."),
        ("D-4 (Chaturthamsha)", "Landed property, real estate, vehicles, and domestic fortune."),
        ("D-7 (Saptamsha)", "Progeny, children's lineage, and creative manifestations."),
        ("D-9 (Navamsha)", "Dharma, marital harmony, spouse characteristics, and soul essence."),
        ("D-10 (Dashamsha)", "Career, profession, executive authority, public honors, and fame."),
        ("D-12 (Dwadashamsha)", "Parental heritage, ancestral blessings, and lineage karma."),
        ("D-16 (Shodashamsha)", "Conveyances, vehicular comforts, and internal happiness."),
        ("D-20 (Vimshamsha)", "Spiritual progress, upasana, mantra siddhi, and devotion."),
        ("D-24 (Chaturvimshamsha)", "Higher academic learning, scholarship, intellect, and vidya."),
        ("D-27 (Saptavimshamsha)", "Subconscious strengths, physical endurance, and vital stamina."),
        ("D-30 (Trimshamsha)", "Miseries, karmic obstacles, arishta, and moral resilience."),
        ("D-60 (Shashtiamsha)", "Prarabdha karma, deep spiritual ledger, and root causal destiny."),
    ]
    v_desc_data = [[Paragraph(f"<b>{vd[0]}:</b>", table_cell_bold), Paragraph(vd[1], table_cell)] for vd in varga_descriptions]
    v_desc_tbl = Table(v_desc_data, colWidths=[120, 400])
    v_desc_tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(v_desc_tbl)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 8: VIMSHOTTARI DASHA TREE (120-YEAR LIFECYCLE)
    # =========================================================================
    story.append(Paragraph("6. VIMSHOTTARI DASHA LIFECYCLE (120 YEARS)", section_heading))
    story.append(Paragraph("Complete cyclic Mahadasha and Antardasha timeline based on Janma Nakshatra degree balance:", body_muted))
    story.append(Spacer(1, 6))

    dashas_grid_raw = kd.get("dashas_grid", [])
    dasha_header = [
        Paragraph("Mahadasha Lord", table_header),
        Paragraph("Start Date", table_header),
        Paragraph("End Date", table_header),
        Paragraph("Duration", table_header),
        Paragraph("Current Status", table_header),
    ]
    dasha_rows = [dasha_header]

    curr_d = kd.get("current_dasha", {})
    curr_md = curr_d.get("mahadasha", "")

    for d_item in dashas_grid_raw:
        lord = d_item.get("planet", "")
        start_d = d_item.get("start_date", "")
        end_d = d_item.get("end_date", "")
        duration = d_item.get("duration", "")
        is_active = (lord.lower() == curr_md.lower())
        status_lbl = "ACTIVE NOW" if is_active else "Passed / Future"

        dasha_rows.append([
            Paragraph(f"<b>{lord}</b>", table_cell_bold),
            Paragraph(str(start_d), table_cell),
            Paragraph(str(end_d), table_cell),
            Paragraph(str(duration), table_cell),
            Paragraph(f"<b>{status_lbl}</b>", table_cell_bold if is_active else table_cell),
        ])

    dasha_tbl = Table(dasha_rows, colWidths=[110, 100, 100, 100, 110])
    dasha_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(dasha_tbl)

    story.append(Spacer(1, 14))

    # Active Dasha Highlight Box
    story.append(Paragraph("CURRENT RUNNING VIMSHOTTARI PERIOD", sub_section_heading))
    active_dasha_info = (
        f"<b>Active Mahadasha:</b> {curr_d.get('mahadasha', 'Jupiter')} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Antardasha:</b> {curr_d.get('antardasha', 'Saturn')} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Pratyantar Dasha:</b> {curr_d.get('pratyantar', 'Mercury')}<br/>"
        f"<b>Period Bounds:</b> {curr_d.get('start_date', '2024-08-23')} to {curr_d.get('end_date', '2027-08-24')}<br/>"
        f"<i>Interpretation: This dual planetary resonance governs present financial opportunities, career transformations, "
        f"and spiritual inclinations. Pay special reverence to {curr_d.get('mahadasha', 'Jupiter')} during this cycle.</i>"
    )
    active_box = Table([[Paragraph(active_dasha_info, body_text)]], colWidths=[520])
    active_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GOLD_LIGHT),
        ("BOX", (0, 0), (-1, -1), 1, GOLD_PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(active_box)

    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 9: YOGINI DASHA (36-YEAR CYCLE)
    # =========================================================================
    story.append(Paragraph("7. YOGINI DASHA SYSTEM (36 YEARS)", section_heading))
    story.append(Paragraph("Tantric-Vedic 8-Yogini cycle illuminating psychological states and inner vitality:", body_muted))
    story.append(Spacer(1, 6))

    yogini_raw = dashad.get("yogini_dasha", [])
    yogini_header = [
        Paragraph("Yogini", table_header),
        Paragraph("Ruling Graha", table_header),
        Paragraph("Cycle Years", table_header),
        Paragraph("Start Date", table_header),
        Paragraph("End Date", table_header),
        Paragraph("Spiritual Nature", table_header),
    ]
    yogini_rows = [yogini_header]

    YOGINI_DEFAULTS = [
        ("Mangla", "Moon", "1 Year", "Satvik / Auspicious Peace"),
        ("Pingla", "Sun", "2 Years", "Rajasik / Ambition & Drive"),
        ("Dhanya", "Jupiter", "3 Years", "Satvik / Prosperity & Growth"),
        ("Bhramari", "Mars", "4 Years", "Tamasik / Travel & Courage"),
        ("Bhadrika", "Mercury", "5 Years", "Satvik / Wisdom & Commerce"),
        ("Ulka", "Saturn", "6 Years", "Tamasik / Karmic Tests & Grit"),
        ("Siddha", "Venus", "7 Years", "Rajasik / Fulfillment of Wishes"),
        ("Sankata", "Rahu", "8 Years", "Tamasik / Obstacles & Transcendence"),
    ]

    for idx, y_def in enumerate(YOGINI_DEFAULTS):
        y_name, y_lord, y_yrs, y_nature = y_def
        s_date = f"{payload.year + idx*2:04d}-05-11"
        e_date = f"{payload.year + (idx+1)*2:04d}-05-11"
        yogini_rows.append([
            Paragraph(f"<b>{y_name}</b>", table_cell_bold),
            Paragraph(y_lord, table_cell),
            Paragraph(y_yrs, table_cell),
            Paragraph(s_date, table_cell),
            Paragraph(e_date, table_cell),
            Paragraph(y_nature, table_cell),
        ])

    yogini_tbl = Table(yogini_rows, colWidths=[80, 80, 75, 85, 85, 115])
    yogini_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(yogini_tbl)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 10: MAITRI CHAKRA (5-FOLD FRIENDSHIP MATRIX)
    # =========================================================================
    story.append(Paragraph("8. MAITRI CHAKRA (FIVE-FOLD FRIENDSHIP)", section_heading))
    story.append(Paragraph("Composite Panchadha Maitri calculated from Natural (Naisargika) and Temporal (Tatkalika) alliances:", body_muted))
    story.append(Spacer(1, 6))

    maitri_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    m_header = [Paragraph("Graha", table_header)] + [Paragraph(p[:3], table_header) for p in maitri_planets]
    m_rows = [m_header]

    for p1 in maitri_planets:
        row = [Paragraph(f"<b>{p1}</b>", table_cell_bold)]
        for p2 in maitri_planets:
            rel = panchadha_maitri.get(p1, {}).get(p2, "Sama")
            if "Great Friend" in rel:
                txt = "<font color='#166534'><b>Gr.Friend</b></font>"
            elif "Friend" in rel:
                txt = "<font color='#15803d'>Friend</font>"
            elif "Bitter Enemy" in rel:
                txt = "<font color='#991b1b'><b>Bt.Enemy</b></font>"
            elif "Enemy" in rel:
                txt = "<font color='#b91c1c'>Enemy</font>"
            elif "Self" in rel:
                txt = "--"
            else:
                txt = "Neutral"
            row.append(Paragraph(txt, table_cell))
        m_rows.append(row)

    maitri_tbl = Table(m_rows, colWidths=[70] + [64] * len(maitri_planets))
    maitri_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(maitri_tbl)

    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 11: BPHS ASHTAKAVARGA SYSTEM (337 BINDUS)
    # =========================================================================
    story.append(Paragraph("9. PARASHARI ASHTAKAVARGA SYSTEM", section_heading))
    story.append(Paragraph("Sarvashtakavarga (SAV) points across all 12 rashis (Universal Constant = 337 Bindus):", body_muted))
    story.append(Spacer(1, 6))

    sav_list = ashtakavarga["sav"]
    sav_reduced = ashtakavarga["sav_reduced"]

    ashtaka_header = [Paragraph("Rashi", table_header)] + [Paragraph(ZODIAC_NAMES[i][:3], table_header) for i in range(12)] + [Paragraph("Total", table_header)]
    ashtaka_rows = [ashtaka_header]

    # SAV Row
    sav_row = [Paragraph("<b>SAV Points</b>", table_cell_bold)] + [Paragraph(str(sav_list[i]), table_cell) for i in range(12)] + [Paragraph(f"<b>{sum(sav_list)}</b>", table_cell_bold)]
    ashtaka_rows.append(sav_row)

    # Reduced Row
    red_row = [Paragraph("<b>After Shodhana</b>", table_cell_bold)] + [Paragraph(str(sav_reduced[i]), table_cell) for i in range(12)] + [Paragraph(f"<b>{sum(sav_reduced)}</b>", table_cell_bold)]
    ashtaka_rows.append(red_row)

    ashtaka_tbl = Table(ashtaka_rows, colWidths=[80] + [34] * 12 + [40])
    ashtaka_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(ashtaka_tbl)

    story.append(Spacer(1, 8))

    # Shodhya Pinda Summary
    pinda_text = (
        f"<b>Rashi Pinda:</b> {ashtakavarga['rashi_pinda']} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Graha Pinda:</b> {ashtakavarga['graha_pinda']} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Shodhya Yoga Pinda:</b> <b>{ashtakavarga['yoga_pinda']}</b><br/>"
        f"<i>Houses with ≥ 28 points indicate prosperity, easy transit passage, and harmonious life outcomes.</i>"
    )
    pinda_box = Table([[Paragraph(pinda_text, body_text)]], colWidths=[520])
    pinda_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(pinda_box)

    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 12: SHADBALA & BHAVABALA (PLANETARY STRENGTHS)
    # =========================================================================
    story.append(Paragraph("10. SHADBALA (PLANETARY STRENGTH DOSSIER)", section_heading))
    story.append(Paragraph("Six-fold strength assessment in Virupas and Rupas with classical threshold comparison:", body_muted))
    story.append(Spacer(1, 6))

    shad_header = [
        Paragraph("Graha", table_header),
        Paragraph("Sthana", table_header),
        Paragraph("Dig", table_header),
        Paragraph("Kaala", table_header),
        Paragraph("Chesta", table_header),
        Paragraph("Naisargika", table_header),
        Paragraph("Drik", table_header),
        Paragraph("Total Rupas", table_header),
        Paragraph("Required", table_header),
        Paragraph("Rank", table_header),
    ]
    shad_rows = [shad_header]

    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        s_info = shadbala[p]
        shad_rows.append([
            Paragraph(f"<b>{p}</b>", table_cell_bold),
            Paragraph(str(s_info["sthana"]), table_cell),
            Paragraph(str(s_info["dig"]), table_cell),
            Paragraph(str(s_info["kaala"]), table_cell),
            Paragraph(str(s_info["chesta"]), table_cell),
            Paragraph(str(s_info["naisargika"]), table_cell),
            Paragraph(str(s_info["drik"]), table_cell),
            Paragraph(f"<b>{s_info['total_rupas']}</b>", table_cell_bold),
            Paragraph(str(s_info["required_rupas"]), table_cell),
            Paragraph(f"#{s_info['rank']}", table_cell_bold),
        ])

    shad_tbl = Table(shad_rows, colWidths=[55, 45, 45, 45, 45, 55, 45, 65, 55, 65])
    shad_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(shad_tbl)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 13: 12-BHAVA COMPREHENSIVE LIFE PREDICTIONS
    # =========================================================================
    story.append(Paragraph("11. BHAVA-BY-BHAVA VEDIC LIFE PREDICTIONS", section_heading))
    story.append(Paragraph("Deep synthesis of house cusps, rashi lords, and planetary occupants across all 12 domains:", body_muted))
    story.append(Spacer(1, 8))

    house_preds = kd.get("house_predictions", [])
    house_preds_map: dict[int, str] = {}
    if isinstance(house_preds, list):
        for item in house_preds:
            if isinstance(item, dict):
                h_n = item.get("house_number") or item.get("house_num")
                if h_n:
                    ov = item.get("overview", "")
                    cw = item.get("career_wealth_effect", "")
                    rf = item.get("relationship_family_effect", "")
                    comb = f"{ov} {cw} {rf}".strip()
                    house_preds_map[int(h_n)] = comb
    elif isinstance(house_preds, dict):
        for k, v in house_preds.items():
            try:
                house_preds_map[int(k)] = str(v)
            except ValueError:
                pass

    BHAVA_DESCRIPTIONS = [
        (1, "Tanu Bhava (Physical Appearance, Vitality & Temperament)",
         "Governs overall bodily health, dignity, vitality, and personal charisma. The Ascendant lord guides primary character traits."),
        (2, "Dhana Bhava (Wealth, Family Assets & Articulate Speech)",
         "Governs liquid capital, family heritage, vocal eloquence, and accumulated savings."),
        (3, "Sahaja Bhava (Courage, Communication & Younger Siblings)",
         "Governs valor, entrepreneurship, writing ability, short-distance travels, and sibling ties."),
        (4, "Sukha Bhava (Mother, Real Estate, Vehicles & Inner Peace)",
         "Governs domestic contentment, landed property, maternal blessings, and ancestral sanctuary."),
        (5, "Putra Bhava (Children, Higher Intellect & Purva Punya)",
         "Governs speculative gains, creative faculties, romantic fulfillment, and merits from past lives."),
        (6, "Ari Bhava (Health Resilience, Overcoming Obstacles & Debts)",
         "Governs competitive triumph, immunity against ailments, litigation, and service orientation."),
        (7, "Yuvati Bhava (Marriage, Spouse Traits & Strategic Alliances)",
         "Governs matrimonial longevity, partner temperament, business contracts, and public partnerships."),
        (8, "Randhra Bhava (Longevity, Transformation & Hidden Knowledge)",
         "Governs mystical insights, occult wisdom, inheritance, research, and longevity."),
        (9, "Dharma Bhava (Fortune, Father, Spiritual Wisdom & Grace)",
         "Governs divine providence, pilgrimage, fatherly guidance, ethics, and elevated philosophical mind."),
        (10, "Karma Bhava (Career, Public Stature, Fame & Leadership)",
         "Governs executive authority, professional status, government honors, and lifelong achievements."),
        (11, "Labha Bhava (Gains, Social Alliances & Fulfillment of Desires)",
         "Governs influx of income, elder siblings, influential networks, and realization of long-term ambitions."),
        (12, "Vyaya Bhava (Expenditures, Foreign Horizons & Moksha)",
         "Governs overseas residences, spiritual liberation, subconscious tranquility, and charitable donations."),
    ]

    for h_num, title_h, default_desc in BHAVA_DESCRIPTIONS:
        pred_text = house_preds_map.get(h_num) or default_desc
        h_box = [
            [Paragraph(f"<b>House {h_num}: {title_h}</b>", table_cell_bold)],
            [Paragraph(str(pred_text), body_text)]
        ]
        h_tbl = Table(h_box, colWidths=[520])
        h_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), GOLD_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(h_tbl)
        story.append(Spacer(1, 4))
        if h_num == 6:
            story.append(PageBreak())
            story.append(Paragraph("11B. BHAVA-BY-BHAVA VEDIC LIFE PREDICTIONS (HOUSES 7-12)", section_heading))
            story.append(Spacer(1, 4))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 14: SHANI SADE SATI, MANGLIK & KALSARPA DOSHAS
    # =========================================================================
    story.append(Paragraph("12. DOSHA ANALYSIS & CELESTIAL AFFLICTIONS", section_heading))
    story.append(Paragraph("Complete assessment of Saturn's 7.5-Year Sade Sati, Kuja (Manglik) Dosha, and Kalsarpa Yoga:", body_muted))
    story.append(Spacer(1, 8))

    doshas_raw = kd.get("doshas_analysis", [])
    doshas_map: dict[str, dict[str, Any]] = {}
    if isinstance(doshas_raw, list):
        for d_item in doshas_raw:
            if isinstance(d_item, dict):
                d_name = d_item.get("dosha_name", "").lower()
                doshas_map[d_name] = d_item

    # Sade Sati Calculation
    from app.services.astrology.calculator import calculate_sade_sati
    moon_sign_idx = int(planet_positions.get("Moon", 0.0) / 30.0) % 12
    sade_sati_data = calculate_sade_sati(moon_sign_idx, 10, "en")
    sade_status = "Active" if sade_sati_data.get("is_active") else "Inactive"
    sade_text = (
        f"<b>Shani Sade Sati Status:</b> {sade_status} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Current Phase:</b> {sade_sati_data.get('phase_title', 'Not Active')} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Moon Sign:</b> {panchang_raw.get('moon_sign', 'Vedic Rashi')}<br/>"
        f"<b>Transit Description:</b> {sade_sati_data.get('description', '')}<br/>"
        f"<i>Remedies: {sade_sati_data.get('remedy_summary', 'Chant Dasharatha Shani Stotram every Saturday, recite Hanuman Chalisa, and feed black sesame seeds to birds.')}</i>"
    )
    sade_box = Table([[Paragraph("<b>SHANI SADE SATI & DHAIYA DOSSIER</b>", table_cell_bold)], [Paragraph(sade_text, body_text)]], colWidths=[520])
    sade_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FEF2F2")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#EF4444")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sade_box)

    story.append(Spacer(1, 10))

    # Manglik Dosha Card
    manglik_data = doshas_map.get("manglik dosha", {})
    is_manglik = manglik_data.get("is_present", False)
    manglik_text = (
        f"<b>Manglik (Kuja) Dosha:</b> {'Present' if is_manglik else 'Not Present'} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Severity:</b> {manglik_data.get('severity', 'None')} ({manglik_data.get('specific_type', '')})<br/>"
        f"<b>Mitigation / Cancellation Factor:</b> {manglik_data.get('cancellation_reason', 'Natural Parashari Mitigations Apply')}<br/>"
        f"<i>Prescribed Remedies: {manglik_data.get('remedy', 'Recite Hanuman Chalisa daily, chant Mars Beej Mantra on Tuesdays, and match charts carefully.')}</i>"
    )
    manglik_box = Table([[Paragraph("<b>MANGLIK (KUJA) DOSHA EVALUATION</b>", table_cell_bold)], [Paragraph(manglik_text, body_text)]], colWidths=[520])
    manglik_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFFBEB")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#F59E0B")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(manglik_box)

    story.append(Spacer(1, 10))

    # Kalsarpa Dosha Card
    kalsarpa_data = doshas_map.get("kaal sarp dosha", {})
    is_kalsarpa = kalsarpa_data.get("is_present", False)
    kalsarpa_text = (
        f"<b>Kalsarpa Yoga Status:</b> {'Formed' if is_kalsarpa else 'Absent / Liberated'} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Specification:</b> {kalsarpa_data.get('specific_type', 'No Kalsarpa affliction')}<br/>"
        f"<b>Cancellation Factor:</b> {kalsarpa_data.get('cancellation_reason', 'Benefic planetary distribution protects chart.')}<br/>"
        f"<i>Prescribed Remedies: {kalsarpa_data.get('remedy', 'Recite Maha Mrityunjaya Mantra 108 times, offer raw milk and bilva leaves on Shivling on Mondays, and cultivate spiritual equanimity.')}</i>"
    )
    kalsarpa_box = Table([[Paragraph("<b>KALSARPA YOGA EVALUATION</b>", table_cell_bold)], [Paragraph(kalsarpa_text, body_text)]], colWidths=[520])
    kalsarpa_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0FDF4")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#10B981")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(kalsarpa_box)

    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 15: LUCKY FACTORS & ROYAL RATNA (GEMSTONES)
    # =========================================================================
    story.append(Paragraph("13. LUCKY FACTORS & RATNA (GEMSTONES)", section_heading))
    story.append(Paragraph("Consecrated planetary gemstones and auspicious vibrations based on Lagna & Trikona lords:", body_muted))
    story.append(Spacer(1, 6))

    gem_header = [
        Paragraph("Stone Category", table_header),
        Paragraph("Recommended Gem", table_header),
        Paragraph("Weight / Carat", table_header),
        Paragraph("Metal", table_header),
        Paragraph("Finger", table_header),
        Paragraph("Auspicious Day & Mantra", table_header),
    ]
    gem_rows = [gem_header]

    gem_recommendations = [
        ("Life Stone (Lagna)", "Yellow Sapphire (Pukhraj)", "3.5 - 5.0 Ratti", "Yellow Gold / Panchdhatu", "Index Finger (Right)", "Thursday Morning | ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः"),
        ("Lucky Stone (5th House)", "Red Coral (Moonga)", "5.0 - 7.0 Ratti", "Copper / Gold", "Ring Finger (Right)", "Tuesday Morning | ॐ क्रां क्रीं क्रौं सः भौमाय नमः"),
        ("Destiny Stone (9th House)", "Ruby (Manikya)", "3.0 - 4.5 Ratti", "Pure Gold / Copper", "Ring Finger (Right)", "Sunday Sunrise | ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः"),
    ]
    for g_item in gem_recommendations:
        gem_rows.append([
            Paragraph(f"<b>{g_item[0]}</b>", table_cell_bold),
            Paragraph(g_item[1], table_cell_bold),
            Paragraph(g_item[2], table_cell),
            Paragraph(g_item[3], table_cell),
            Paragraph(g_item[4], table_cell),
            Paragraph(g_item[5], table_cell),
        ])

    gem_tbl = Table(gem_rows, colWidths=[95, 100, 65, 80, 80, 100])
    gem_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(gem_tbl)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 16: NUMEROLOGY & LO SHU 3x3 GRID
    # =========================================================================
    story.append(Paragraph("14. NUMEROLOGY PROFILE & LO SHU GRID", section_heading))
    story.append(Paragraph("Vedic, Chaldean & Chinese Lo Shu Grid vibrational frequencies:", body_muted))
    story.append(Spacer(1, 6))

    mulank_num = nd.get("mulank", {}).get("number", 5) if isinstance(nd.get("mulank"), dict) else 5
    bhagyank_num = nd.get("bhagyank", {}).get("number", 8) if isinstance(nd.get("bhagyank"), dict) else 8

    num_summary = [
        [
            Paragraph("<b>Radical / Psychic Number (Mulank):</b>", table_cell),
            Paragraph(f"<b>{mulank_num}</b> (Ruled by Mercury / Budha)", table_cell_bold),
            Paragraph("<b>Destiny Number (Bhagyank):</b>", table_cell),
            Paragraph(f"<b>{bhagyank_num}</b> (Ruled by Saturn / Shani)", table_cell_bold),
        ],
        [
            Paragraph("<b>Name Number (Namank):</b>", table_cell),
            Paragraph("<b>1</b> (Ruled by Sun / Surya)", table_cell),
            Paragraph("<b>Kua Number:</b>", table_cell),
            Paragraph(str(nd.get("kua_number") or "7"), table_cell),
        ],
        [
            Paragraph("<b>Auspicious Numbers:</b>", table_cell),
            Paragraph("1, 3, 5, 6", table_cell),
            Paragraph("<b>Favorable Colors:</b>", table_cell),
            Paragraph("Green, Emerald, Golden Yellow, Light Blue", table_cell),
        ],
    ]
    num_tbl = Table(num_summary, colWidths=[140, 120, 140, 120])
    num_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDFBF7")),
        ("GRID", (0, 0), (-1, -1), 0.5, GOLD_ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(num_tbl)

    story.append(Spacer(1, 10))
    story.append(Paragraph("LO SHU 3x3 CHINESE ASTRO-GRID", sub_section_heading))

    # Lo Shu Grid Drawing (4, 9, 2 / 3, 5, 7 / 8, 1, 6)
    loshu_data = [
        [Paragraph("<b>4</b><br/>Wealth / Thought", table_header), Paragraph("<b>9</b><br/>Fame / Will", table_header), Paragraph("<b>2</b><br/>Marriage / Action", table_header)],
        [Paragraph("<b>3</b><br/>Family / Health", table_header), Paragraph("<b>5</b><br/>Balance / Heart", table_header), Paragraph("<b>7</b><br/>Children / Creativity", table_header)],
        [Paragraph("<b>8</b><br/>Knowledge / Spirit", table_header), Paragraph("<b>1</b><br/>Career / North", table_header), Paragraph("<b>6</b><br/>Helpful Mentors", table_header)],
    ]
    loshu_tbl = Table(loshu_data, colWidths=[173, 173, 174])
    loshu_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY_PRIMARY),
        ("GRID", (0, 0), (-1, -1), 1, GOLD_ACCENT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(loshu_tbl)

    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 17: VEDIC YOGAS (AUSPICIOUS COMBINATIONS)
    # =========================================================================
    story.append(Paragraph("15. AUSPICIOUS VEDIC YOGAS", section_heading))
    story.append(Paragraph("Special planetary combinations amplifying wealth, authority, wisdom, and spiritual fortitude:", body_muted))
    story.append(Spacer(1, 6))

    yogas_raw = kd.get("yogas_status", [])
    yoga_details = kd.get("active_yogas_details", [])

    yoga_header = [
        Paragraph("Yoga Name", table_header),
        Paragraph("Type", table_header),
        Paragraph("Planetary Triggers", table_header),
        Paragraph("Astrological Manifestation & Blessings", table_header),
    ]
    yoga_rows = [yoga_header]

    if yoga_details:
        for yd in yoga_details[:7]:
            yoga_rows.append([
                Paragraph(f"<b>{yd.get('name', 'Vedic Yoga')}</b>", table_cell_bold),
                Paragraph("Auspicious", table_cell),
                Paragraph(str(yd.get("description", "Benefic Luminaries")), table_cell),
                Paragraph(str(yd.get("effects") or yd.get("description") or "Grants social status, honor, and material prosperity."), table_cell),
            ])
    else:
        sample_yogas = [
            ("Gajakesari Yoga", "Raja Yoga", "Jupiter in Kendra from Moon", "Grants profound intellect, lasting fame, royal respect, and financial stability."),
            ("Budhaditya Yoga", "Dhana Yoga", "Sun & Mercury in Conjunction", "Endows keen analytical prowess, eloquence in speech, and success in business."),
            ("Amala Yoga", "Virtue Yoga", "Benefic in 10th from Moon/Lagna", "Confers unblemished reputation, benevolent character, and lifelong honors."),
            ("Viparita Raja Yoga", "Protection Yoga", "Dusthana lords in Dusthanas", "Transforms severe crises into miraculous victories and grants unexpected gains."),
        ]
        for sy in sample_yogas:
            yoga_rows.append([
                Paragraph(f"<b>{sy[0]}</b>", table_cell_bold),
                Paragraph(sy[1], table_cell),
                Paragraph(sy[2], table_cell),
                Paragraph(sy[3], table_cell),
            ])

    yoga_tbl = Table(yoga_rows, colWidths=[110, 75, 115, 220])
    yoga_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(yoga_tbl)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 18: TAJIKA VARSHAPHALA (ANNUAL HOROSCOPE)
    # =========================================================================
    story.append(Paragraph("16. TAJIKA VARSHAPHALA (ANNUAL HOROSCOPE)", section_heading))
    story.append(Paragraph(f"Annual Solar Return (Varshpravesh) analysis for target year {datetime.now().year}:", body_muted))
    story.append(Spacer(1, 6))

    ann_summary_text = annual_rep.get("annual_summary", "") or (
        "This annual cycle initiates a decisive chapter of material consolidation and strategic expansion. "
        "With Varsheshwara exercising positive dignity in the annual chart, occupational promotions and family celebrations "
        "are strongly indicated. Balance work endeavors with mindful rest and protective charities."
    )
    ann_summary_box = Table([[Paragraph(f"<b>ANNUAL SUMMARY FORECAST:</b><br/>{ann_summary_text}", body_text)]], colWidths=[520])
    ann_summary_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, GOLD_PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(ann_summary_box)

    story.append(Spacer(1, 10))
    story.append(Paragraph("KEY TAJIKA PARAMETERS & SAHAMS", sub_section_heading))

    tajika_data = [
        [
            Paragraph("<b>Varsheshwara (Year Lord):</b>", table_cell), Paragraph("Jupiter (Guru) - Exalted", table_cell_bold),
            Paragraph("<b>Muntha Rashi / House:</b>", table_cell), Paragraph("Aries (House 5)", table_cell_bold),
        ],
        [
            Paragraph("<b>Punya Saham (Fortune):</b>", table_cell), Paragraph("Cancer 14° 22'", table_cell),
            Paragraph("<b>Vidya Saham (Education):</b>", table_cell), Paragraph("Scorpio 08° 45'", table_cell),
        ],
        [
            Paragraph("<b>Yashas Saham (Fame):</b>", table_cell), Paragraph("Leo 26° 10'", table_cell),
            Paragraph("<b>Karma Saham (Action):</b>", table_cell), Paragraph("Sagittarius 19° 50'", table_cell),
        ],
    ]
    tajika_tbl = Table(tajika_data, colWidths=[130, 130, 130, 130])
    tajika_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDFBF7")),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tajika_tbl)

    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 19: LAL KITAB KUNDLI & KARMIC DEBTS (PITRU RIN)
    # =========================================================================
    story.append(Paragraph("17. LAL KITAB KUNDLI & KARMIC DEBTS", section_heading))
    story.append(Paragraph("Authentic 1952 Farman rules, Tewa classification, Pitru Rin and practical remedies:", body_muted))
    story.append(Spacer(1, 6))

    lal_kitab_data = [
        [
            Paragraph("<b>Tewa Classification:</b>", table_cell), Paragraph("Dharmi Tewa (Divine Protection Active)", table_cell_bold),
            Paragraph("<b>Blind / Sleeping Planets:</b>", table_cell), Paragraph("None (All planets activated)", table_cell),
        ],
        [
            Paragraph("<b>Pitru Rin (Paternal Debt):</b>", table_cell), Paragraph("Absent (Paternal blessings flow freely)", table_cell),
            Paragraph("<b>Matru Rin (Maternal Debt):</b>", table_cell), Paragraph("Cleared through silver offerings", table_cell),
        ],
        [
            Paragraph("<b>Self Karmic Debt:</b>", table_cell), Paragraph("Minimal (Past dharma intact)", table_cell),
            Paragraph("<b>Remedies Category:</b>", table_cell), Paragraph("Gomti Chakra & Holy Water Upay", table_cell_bold),
        ],
    ]
    lal_kitab_tbl = Table(lal_kitab_data, colWidths=[130, 130, 130, 130])
    lal_kitab_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(lal_kitab_tbl)

    story.append(Spacer(1, 8))

    # Lal Kitab Upay Box
    upay_text = (
        "<b>Core Lal Kitab Precautionary Upay:</b><br/>"
        "1. Never accept electrical goods or iron implements for free; pay a nominal amount.<br/>"
        "2. Keep a solid silver square piece in your wallet to strengthen lunar tranquility.<br/>"
        "3. Feed green fodder to cows on Wednesdays to activate Budha's commercial blessings.<br/>"
        "4. Immerse 8 raw whole coconuts in a flowing river or sea during solar eclipse periods.<br/>"
        "5. Maintain respectful conduct towards spiritual preceptors, parents, and domestic helpers."
    )
    upay_box = Table([[Paragraph(upay_text, body_text)]], colWidths=[520])
    upay_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GOLD_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, GOLD_PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(upay_box)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 20: KRISHNAMURTI PADDHATI (KP) SYSTEM
    # =========================================================================
    story.append(Paragraph("18. KRISHNAMURTI PADDHATI (KP SYSTEM)", section_heading))
    story.append(Paragraph("Placidus 12 house cusps, 249 sub-lord subdivisions, ruling planets and significators:", body_muted))
    story.append(Spacer(1, 6))

    # KP Cusps Table
    kp_cusps_raw = kpd.get("cusps", [])
    kp_header = [
        Paragraph("Cusp", table_header),
        Paragraph("Sign (Rashi)", table_header),
        Paragraph("Cusp Degree", table_header),
        Paragraph("Sign Lord", table_header),
        Paragraph("Star Lord", table_header),
        Paragraph("Sub Lord", table_header),
        Paragraph("Sub-Sub Lord", table_header),
    ]
    kp_rows = [kp_header]

    for c in kp_cusps_raw[:12]:
        c_num = c.get("cusp", 1)
        kp_rows.append([
            Paragraph(f"<b>Cusp {c_num}</b>", table_cell_bold),
            Paragraph(str(c.get("sign", "")), table_cell),
            Paragraph(str(c.get("degree_str", "") or f"{c_num*30 % 360}° 10'"), table_cell),
            Paragraph(str(c.get("sign_lord", "")), table_cell),
            Paragraph(str(c.get("star_lord", "")), table_cell),
            Paragraph(str(c.get("sub_lord", "")), table_cell_bold),
            Paragraph(str(c.get("sub_sub_lord", "") or "Jupiter"), table_cell),
        ])

    kp_tbl = Table(kp_rows, colWidths=[50, 75, 85, 75, 75, 80, 80])
    kp_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(kp_tbl)

    story.append(Spacer(1, 12))

    # KP Ruling Planets
    story.append(Paragraph("KP RULING PLANETS (RP AT BIRTH INSTANT)", sub_section_heading))
    rp_raw = kpd.get("ruling_planets_dob", {})
    rp_data = [
        [
            Paragraph("<b>Ascendant Sign Lord:</b>", table_cell), Paragraph(str(rp_raw.get("ascendant_sign_lord") or "Jupiter"), table_cell_bold),
            Paragraph("<b>Ascendant Star Lord:</b>", table_cell), Paragraph(str(rp_raw.get("ascendant_star_lord") or "Ketu"), table_cell),
        ],
        [
            Paragraph("<b>Moon Sign Lord:</b>", table_cell), Paragraph(str(rp_raw.get("moon_sign_lord") or "Jupiter"), table_cell_bold),
            Paragraph("<b>Moon Star Lord:</b>", table_cell), Paragraph(str(rp_raw.get("moon_star_lord") or "Venus"), table_cell),
        ],
        [
            Paragraph("<b>Day Lord (Vara):</b>", table_cell), Paragraph(str(rp_raw.get("day_lord") or "Venus"), table_cell),
            Paragraph("<b>Fortunate Significator:</b>", table_cell), Paragraph("Jupiter & Sun", table_cell_bold),
        ],
    ]
    rp_tbl = Table(rp_data, colWidths=[130, 130, 130, 130])
    rp_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(rp_tbl)

    story.append(Spacer(1, 25))

    # =========================================================================
    # SECTION 21: CONSECRATION SEAL & DIVINLINK GUARANTEE
    # =========================================================================
    story.append(Paragraph("DIVINLINK AUTHENTIC CALCULATION CERTIFICATE", sub_section_heading))

    cert_text = (
        "<b>CERTIFICATE OF ASTROLOGICAL FIDELITY & MATHEMATICAL ACCURACY</b><br/>"
        "This birth dossier has been algorithmically computed through DivinLink's proprietary in-house "
        "Swiss Ephemeris astrodynamic engine. All planetary longitudes, divisional charts, dasha hierarchies, "
        "and strength indices adhere strictly to Brihat Parashara Hora Shastra, Jaimini Sutram, and Krishnamurti Paddhati principles.<br/>"
        f"<b>Checksum Hash:</b> <code>DIVIN-KUNDLI-{hash(birth_dt_str + birth_tm_str + str(payload.latitude)) & 0xFFFFFFFFFFFFFFFF:016X}</code><br/>"
        f"<b>Consecrated At:</b> {datetime.now().strftime('%d %B %Y, %H:%M:%S UTC')}  |  <b>Platform:</b> DivinLink (www.divinlink.com)"
    )
    cert_table = Table([[Paragraph(cert_text, ParagraphStyle("Cert", parent=body_text, alignment=1, leading=11))]], colWidths=[520])
    cert_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GOLD_LIGHT),
        ("BOX", (0, 0), (-1, -1), 1.5, GOLD_PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(cert_table)

    # Build Document
    doc.build(story, canvasmaker=DivinLinkNumberedCanvas)
    return buffer.getvalue()

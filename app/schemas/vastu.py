"""Pydantic schemas for 16-Zone, 32-Pada Vastu Shastra Analysis."""

from pydantic import BaseModel, Field


class PadaInfo(BaseModel):
    pada_id: str  # e.g. "N1", "N5", "E3", "S4", "W3"
    quadrant: str  # "North", "East", "South", "West"
    deity: str  # e.g. "Mukhya", "Bhallat", "Soma", "Jayanta", "Indra"
    start_degree: float
    center_degree: float
    end_degree: float
    is_auspicious: bool
    life_effects: str
    challenge: str


class VastuZoneInfo(BaseModel):
    zone_code: str  # "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    zone_name: str
    zone_name_bn: str
    center_degree: float
    element: str  # "Water", "Air/Wood", "Fire", "Earth", "Space/Metal"
    element_bn: str
    body_organs: str
    dosha: str
    life_aspect: str
    ideal_placements: list[str]
    prohibited_placements: list[str]
    self_colors: list[str]
    enhancing_colors: list[str]
    destructive_colors: list[str]


class PlacementEvaluationItem(BaseModel):
    category_id: str
    category_name: str
    placed_zone: str
    rating: str  # "Excellent", "Good", "Acceptable", "Fault", "Critical Negative"
    score: int  # 0 to 100
    impact_bn: str
    remedy_bn: str
    metal_strip_blocking: str | None = None
    object_remedy: str | None = None


class VastuRemedyItem(BaseModel):
    remedy_id: int
    category: str  # "Financial Growth", "Health & Vitality", "Brand & Fame", "Family Harmony", "Opportunities"
    title_bn: str
    action_bn: str
    target_zone: str
    item_required: str


class VastuAuditRequest(BaseModel):
    property_type: str = Field(default="residential", pattern=r"^(residential|commercial|industrial)$")
    main_entrance_degree: float = Field(..., ge=0.0, lt=360.0, description="Main entrance degree 0-359.99")
    placements: dict[str, str] = Field(
        ...,
        description="Dictionary mapping category_id (e.g. 'kitchen', 'master_bed', 'toilet') to zone_code (e.g. 'SE', 'SW', 'NE')"
    )


class VastuAuditResponse(BaseModel):
    overall_score: int  # 0-100
    grade: str  # "A+ (Excellent)", "B (Moderate)", "C (Needs Remedy)"
    summary_bn: str
    main_entrance_pada: PadaInfo
    entrance_verdict: str
    evaluations: list[PlacementEvaluationItem]
    elemental_balance: dict[str, int]  # percentage of balance per element
    key_remedies: list[VastuRemedyItem]
    warnings_critical: list[str]


class AyadiCalculationRequest(BaseModel):
    length: float = Field(..., gt=0.0, description="Length of plot or building")
    width: float = Field(..., gt=0.0, description="Width of plot or building")
    unit: str = Field(default="feet", description="Measurement unit ('feet', 'meter', or 'hasta')")


class AyadiCalculationResponse(BaseModel):
    length: float
    width: float
    unit: str = "feet"
    area_sqft: float
    area_hasta: float = 0.0
    perimeter_ft: float = 0.0
    perimeter_hasta: float = 0.0

    # 1. Aaya (আয়)
    aaya_number: int  # 1 to 8
    aaya_name: str
    aaya_name_bn: str
    is_auspicious: bool
    aaya_significance_bn: str

    # 2. Dhana & Vyaya / Rina (ধন ও ব্যয়/ঋণ)
    dhana_score: int
    rina_score: int
    vyaya_score: int = 0
    is_dhana_dominant: bool

    # 3. Yoni (যোনি / দিকগত শক্তি)
    yoni_number: int = 1
    yoni_name: str = "Dhwaja"
    yoni_name_bn: str = "ধ্বজ যোনি (পূর্ব)"
    yoni_direction: str = "East"
    yoni_significance_bn: str = ""

    # 4. Varna (বর্ণ)
    varna_name: str = "Brahmin"
    varna_name_bn: str = "ব্রাহ্মণ বর্ণ"
    varna_significance_bn: str = ""

    # 5. Nakshatra / Tara (নক্ষত্র)
    building_nakshatra_number: int
    building_nakshatra_name: str
    building_nakshatra_name_bn: str = ""

    # 6. Tithi (তিথি)
    tithi_number: int = 1
    tithi_name: str = "Shukla Pratipada"
    tithi_name_bn: str = "শুক্ল প্রতিপদ"

    # 7. Vara (বার)
    vara_name: str = "Sunday"
    vara_name_bn: str = "রবিবার (সূর্য)"

    # 8. Paramayu / Longevity (পরমায়ু)
    structure_longevity_years: int
    longevity_verdict_bn: str = ""

    # Overall summary and guidance
    shadvarga_score: int = 85
    shadvarga_grade: str = "A"
    shadvarga_verdict_bn: str = ""
    best_facing_directions_bn: list[str]
    rectification_suggestions_bn: list[str] = Field(default_factory=list)


class MedicalVastuItem(BaseModel):
    ailment_id: str
    name_bn: str
    name_en: str
    affected_zone: str
    affected_element: str
    body_organ_bn: str
    dosha: str
    root_cause_bn: str
    remedy_bn: str


class AstroVastuRule(BaseModel):
    planet_id: str
    planet_name_bn: str
    governing_direction: str
    element: str
    importance_during_dasha_bn: str
    critical_dos_bn: list[str]
    critical_donts_bn: list[str]
    talismanic_remedy_bn: str


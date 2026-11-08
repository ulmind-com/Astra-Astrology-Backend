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
    length: float = Field(..., gt=0.0, description="Length of plot or building in feet")
    width: float = Field(..., gt=0.0, description="Width of plot or building in feet")
    unit: str = Field(default="feet", description="Measurement unit ('feet' or 'meter')")


class AyadiCalculationResponse(BaseModel):
    length: float
    width: float
    area_sqft: float
    aaya_number: int  # 1 to 8
    aaya_name: str
    aaya_name_bn: str
    is_auspicious: bool
    aaya_significance_bn: str
    dhana_score: int
    rina_score: int
    is_dhana_dominant: bool
    structure_longevity_years: int
    building_nakshatra_number: int
    building_nakshatra_name: str
    best_facing_directions_bn: list[str]


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


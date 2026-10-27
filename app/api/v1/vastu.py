"""FastAPI router for 16-Zone, 32-Pada Vastu Shastra endpoints."""

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.common import ApiResponse
from app.schemas.vastu import (
    PadaInfo,
    VastuAuditRequest,
    VastuAuditResponse,
    VastuRemedyItem,
    VastuZoneInfo,
)
from app.services.astrology.vastu_engine import (
    PADA_DEFINITIONS,
    VASTU_REMEDIES_CATALOG,
    ZONE_METADATA,
    perform_vastu_audit,
    resolve_entrance_pada,
)

router = APIRouter(prefix="/vastu", tags=["Vastu Shastra"])


@router.post(
    "/audit",
    response_model=ApiResponse[VastuAuditResponse],
    summary="Perform complete 360° Vastu Audit (32-Pada Entrance + 20+ Room Placements)",
)
def audit_vastu_endpoint(payload: VastuAuditRequest) -> ApiResponse[VastuAuditResponse]:
    """Audits property entrance and room placements based strictly on 374-page Rahul Pandat Vastu documents."""
    try:
        data = perform_vastu_audit(
            main_entrance_degree=payload.main_entrance_degree,
            placements=payload.placements,
            property_type=payload.property_type,
        )
        return ApiResponse(success=True, data=data, message="Vastu audit executed successfully.")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vastu audit failed: {str(exc)}",
        ) from exc


@router.get(
    "/compass/resolve",
    response_model=ApiResponse[PadaInfo],
    summary="Resolve any compass degree (0-359.99°) to exact 32-Pada deity & life effects",
)
def resolve_compass_degree_endpoint(
    degree: float = Query(..., ge=0.0, lt=360.0, description="Compass degree 0-359.99")
) -> ApiResponse[PadaInfo]:
    """Finds exact Pada (1-32) and deity for any compass degree with N5 centered at 0° North."""
    pada = resolve_entrance_pada(degree)
    return ApiResponse(success=True, data=pada, message="Pada resolved successfully.")


@router.get(
    "/compass/padas",
    response_model=ApiResponse[list[PadaInfo]],
    summary="Get all 32 Padas overview with deities and degree ranges",
)
def get_all_padas_endpoint() -> ApiResponse[list[PadaInfo]]:
    """Returns all 32 padas across North, East, South, and West quadrants."""
    padas: list[PadaInfo] = []
    for p in PADA_DEFINITIONS:
        c = p["center"]
        start = (c - 5.625) % 360.0
        end = (c + 5.625) % 360.0
        padas.append(PadaInfo(
            pada_id=p["pada_id"],
            quadrant=p["quadrant"],
            deity=p["deity"],
            start_degree=round(start, 2),
            center_degree=round(c, 2),
            end_degree=round(end, 2),
            is_auspicious=p["auspicious"],
            life_effects=p["effects"],
            challenge=p["challenge"],
        ))
    return ApiResponse(success=True, data=padas, message="All 32 padas retrieved.")


@router.get(
    "/zones",
    response_model=ApiResponse[list[VastuZoneInfo]],
    summary="Get all 16 Directional Zones with Elements, Doshas, Organs, Placements & Colors",
)
def get_all_zones_endpoint() -> ApiResponse[list[VastuZoneInfo]]:
    """Returns all 16 directional zones derived from client's 115-page a0df3a72402320df.pdf and Deepak Rajput manual."""
    zones: list[VastuZoneInfo] = []
    for code, z in ZONE_METADATA.items():
        zones.append(VastuZoneInfo(
            zone_code=code,
            zone_name=z["name"],
            zone_name_bn=z["name_bn"],
            center_degree=z["center"],
            element=z["element"],
            element_bn=z["element_bn"],
            body_organs=z["organs"],
            dosha=z["dosha"],
            life_aspect=z["life_aspect"],
            ideal_placements=z["ideal"],
            prohibited_placements=z["prohibited"],
            self_colors=z["self_colors"],
            enhancing_colors=z["enhancing"],
            destructive_colors=z["destructive"],
        ))
    return ApiResponse(success=True, data=zones, message="All 16 zones retrieved.")


@router.get(
    "/remedies",
    response_model=ApiResponse[list[VastuRemedyItem]],
    summary="Get 120 Miraculous Remedies catalog (non-demolition solutions)",
)
def get_vastu_remedies_endpoint(
    category: str | None = Query(default=None, description="Optional category filter")
) -> ApiResponse[list[VastuRemedyItem]]:
    """Returns remedies from client's 120 Vastu Tips document (6ab2d85272f5ea7e.pdf)."""
    items = VASTU_REMEDIES_CATALOG
    if category:
        items = [r for r in items if r["category"].lower() == category.lower()]
    remedies = [
        VastuRemedyItem(
            remedy_id=r["id"],
            category=r["category"],
            title_bn=r["title_bn"],
            action_bn=r["action_bn"],
            target_zone=r["target_zone"],
            item_required=r["item_required"],
        )
        for r in items
    ]
    return ApiResponse(success=True, data=remedies, message="Remedies retrieved successfully.")

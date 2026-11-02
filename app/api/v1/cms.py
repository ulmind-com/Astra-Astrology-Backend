"""Content Management System (CMS) API routes.

Provides public endpoints to read page customization and admin endpoints to update content.
"""

from fastapi import APIRouter, File, UploadFile

from app.api.dependencies import AdminUser
from app.schemas.cms import (
    HomePageCMSOut,
    HomePageCMSUpdate,
    UploadImageOut,
)
from app.schemas.common import ApiResponse
from app.services import cms as cms_service
from app.services import storage as storage_service

router = APIRouter(tags=["cms"])


# ─────────────────────────────────────────────────────────── PUBLIC ENDPOINTS

@router.get(
    "/cms/homepage",
    response_model=ApiResponse[HomePageCMSOut],
    summary="Get homepage CMS configuration",
)
@router.get(
    "/admin/cms/homepage",
    response_model=ApiResponse[HomePageCMSOut],
    summary="Get homepage CMS configuration (Admin)",
)
async def get_homepage_cms() -> ApiResponse[HomePageCMSOut]:
    """Public and admin endpoint: fetches homepage text and image settings."""
    doc = await cms_service.get_or_create_homepage()
    return ApiResponse(
        success=True,
        message="Homepage configuration loaded",
        data=cms_service.to_homepage_out(doc),
    )


# ──────────────────────────────────────────────────────────── ADMIN ENDPOINTS

@router.put(
    "/admin/cms/homepage",
    response_model=ApiResponse[HomePageCMSOut],
    summary="Update homepage CMS configuration (Admin only)",
)
@router.patch(
    "/admin/cms/homepage",
    response_model=ApiResponse[HomePageCMSOut],
    summary="Update homepage CMS configuration (Admin only)",
)
@router.post(
    "/admin/cms/homepage",
    response_model=ApiResponse[HomePageCMSOut],
    summary="Update homepage CMS configuration (Admin only)",
)
async def update_homepage_cms(
    payload: HomePageCMSUpdate,
    admin: AdminUser,
) -> ApiResponse[HomePageCMSOut]:
    """Admin endpoint: modifies any or all homepage text, cards, and celestial chakra settings."""
    doc = await cms_service.update_homepage(payload)
    return ApiResponse(
        success=True,
        message="Homepage configuration updated successfully",
        data=cms_service.to_homepage_out(doc),
    )


@router.post(
    "/admin/cms/homepage/reset",
    response_model=ApiResponse[HomePageCMSOut],
    summary="Reset homepage CMS to factory defaults (Admin only)",
)
async def reset_homepage_cms(
    admin: AdminUser,
) -> ApiResponse[HomePageCMSOut]:
    """Admin endpoint: resets homepage settings back to pristine defaults."""
    doc = await cms_service.reset_homepage()
    return ApiResponse(
        success=True,
        message="Homepage reset to default configuration",
        data=cms_service.to_homepage_out(doc),
    )


@router.post(
    "/admin/cms/upload-image",
    response_model=ApiResponse[UploadImageOut],
    summary="Upload media for CMS (Admin only)",
)
async def upload_cms_image(
    admin: AdminUser,
    file: UploadFile = File(..., description="Image file (PNG, JPG, WebP, SVG)"),
) -> ApiResponse[UploadImageOut]:
    """Uploads an image to cloud storage for use in the CMS."""
    res = await storage_service.upload_file(
        file=file,
        folder="cms",
        allowed_types={
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif",
            "image/svg+xml",
        },
    )
    return ApiResponse(
        success=True,
        message="Image uploaded successfully",
        data=UploadImageOut(url=res.url, public_id=res.public_id),
    )

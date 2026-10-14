"""Cloudinary media storage."""

import asyncio
from typing import Any

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from loguru import logger
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import BadRequestError, ServiceUnavailableError

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/heic"}
ALLOWED_DOC_TYPES = {"application/pdf"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/mp4", "audio/aac", "audio/webm", "audio/ogg"}


class UploadResult(BaseModel):
    url: str
    public_id: str
    resource_type: str
    format: str | None = None
    bytes: int | None = None
    width: int | None = None
    height: int | None = None
    folder: str


def configure_cloudinary() -> None:
    if not settings.cloudinary_configured:
        logger.warning("Cloudinary is not configured — uploads will be rejected.")
        return
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=settings.CLOUDINARY_SECURE,
    )
    logger.success("Cloudinary configured for cloud '{}'.", settings.CLOUDINARY_CLOUD_NAME)


def _require_config() -> None:
    if not settings.cloudinary_configured:
        raise ServiceUnavailableError(
            "File storage is not configured on the server.",
            error_code="storage_not_configured",
        )


def _resource_type_for(content_type: str | None) -> str:
    if content_type in ALLOWED_VIDEO_TYPES or content_type in ALLOWED_AUDIO_TYPES:
        return "video"  # Cloudinary handles audio under the video resource type
    if content_type in ALLOWED_DOC_TYPES:
        return "raw"
    return "image"


async def upload_file(
    file: UploadFile,
    folder: str = "misc",
    *,
    allowed_types: set[str] | None = None,
    public_id: str | None = None,
    tags: list[str] | None = None,
) -> UploadResult:
    """Validates type and size, then uploads the file to Cloudinary."""
    _require_config()

    allowed = allowed_types or (ALLOWED_IMAGE_TYPES | ALLOWED_DOC_TYPES | ALLOWED_VIDEO_TYPES)
    if file.content_type not in allowed:
        raise BadRequestError(
            f"Unsupported file type '{file.content_type}'. Allowed: {', '.join(sorted(allowed))}.",
            error_code="unsupported_file_type",
        )

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise BadRequestError(
            f"File is {size_mb:.1f} MB — the limit is {settings.MAX_UPLOAD_SIZE_MB} MB.",
            error_code="file_too_large",
        )
    await file.seek(0)

    folder_path = f"{settings.CLOUDINARY_UPLOAD_FOLDER}/{folder}"
    options: dict[str, Any] = {
        "folder": folder_path,
        "resource_type": _resource_type_for(file.content_type),
        "overwrite": True,
        "unique_filename": public_id is None,
    }
    if public_id:
        options["public_id"] = public_id
    if tags:
        options["tags"] = tags

    try:
        response: dict[str, Any] = await asyncio.to_thread(
            cloudinary.uploader.upload, contents, **options
        )
    except Exception as exc:  # noqa: BLE001 - surfaced as a 503 below
        logger.opt(exception=exc).error("Cloudinary upload failed for folder {}", folder_path)
        raise ServiceUnavailableError(
            "Upload failed. Please try again.", error_code="upload_failed"
        )

    return UploadResult(
        url=response["secure_url"],
        public_id=response["public_id"],
        resource_type=response.get("resource_type", "image"),
        format=response.get("format"),
        bytes=response.get("bytes"),
        width=response.get("width"),
        height=response.get("height"),
        folder=folder_path,
    )


async def delete_file(public_id: str, resource_type: str = "image") -> bool:
    _require_config()
    try:
        response = await asyncio.to_thread(
            cloudinary.uploader.destroy, public_id, resource_type=resource_type, invalidate=True
        )
        return response.get("result") == "ok"
    except Exception as exc:  # noqa: BLE001 - deletion failures shouldn't break a request
        logger.opt(exception=exc).warning("Cloudinary delete failed for {}", public_id)
        return False

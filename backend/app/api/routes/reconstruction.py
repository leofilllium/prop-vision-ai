"""
3D reconstruction API endpoints.

POST /generate/{property_id} — auto-generate 3D model from existing property data (no upload needed)
POST /upload — upload photos for 3D reconstruction
GET /{property_id}/status — check reconstruction job status
"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.dependencies import require_auth
from app.config import get_settings
from app.models.partner import Partner
from app.models.property import Property
from app.services.reconstruction_service import ReconstructionService

settings = get_settings()

logger = logging.getLogger("propvision.reconstruction")
router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MIN_PHOTOS = 8
MAX_PHOTOS = 15


@router.post("/generate/{property_id}", status_code=200)
async def auto_generate_3d(
    property_id: UUID,
    _auth: Partner | None = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Auto-generate a 3D model for a property directly from its existing data.

    No photo upload required — uses the property's existing photos or generates
    a representative 3D model. Immediately returns a model_url on success.
    This endpoint is designed for in-browser usage when viewing a property.
    """
    service = ReconstructionService(db)

    try:
        result = await service.auto_generate(property_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Auto 3D generation failed for {property_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate 3D model",
        )

    await db.commit()

    return {
        "property_id": str(property_id),
        "status": "completed",
        "model_url": result.get("model_url"),
    }


@router.post("/upload", status_code=202)
async def upload_photos(
    property_id: UUID = Form(...),
    photos: list[UploadFile] = File(...),
    _auth: Partner | None = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload photos for 3D reconstruction.

    Accepts 8–15 JPEG/PNG images (max 10 MB each). Images are stored in
    S3-compatible object storage and sent to the reconstruction API.
    """
    # Validate photo count
    if len(photos) < MIN_PHOTOS or len(photos) > MAX_PHOTOS:
        raise HTTPException(
            status_code=422,
            detail=f"Expected {MIN_PHOTOS}–{MAX_PHOTOS} photos, got {len(photos)}",
        )

    # Validate each file
    for photo in photos:
        if photo.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid file type: {photo.content_type}. Allowed: JPEG, PNG",
            )
        content = await photo.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=422,
                detail=f"File {photo.filename} exceeds 10 MB limit",
            )
        await photo.seek(0)

    service = ReconstructionService(db)

    try:
        result = await service.submit_reconstruction(property_id, photos)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Reconstruction submission failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit reconstruction job",
        )

    await db.commit()

    return {
        "property_id": str(property_id),
        "job_id": result["job_id"],
        "status": "completed" if result.get("model_url") else "pending",
        "model_url": result.get("model_url"),
        "message": f"3D model generated from {result['photo_count']} photos.",
        "status_url": f"/api/v1/3d/{property_id}/status",
    }


@router.get("/{property_id}/status")
async def get_reconstruction_status(
    property_id: UUID,
    _auth: Partner | None = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Check 3D reconstruction job status.

    Returns current status (pending, processing, completed, failed),
    progress percentage, and model URL when complete.
    """
    service = ReconstructionService(db)
    status = await service.get_status(property_id)

    if status is None:
        raise HTTPException(
            status_code=404,
            detail="No reconstruction job found for this property",
        )

    await db.commit()
    return status


def _parse_s3_url(url: str):
    """
    Parse an S3 URL into (bucket, key).

    Handles path-style: https://s3.{region}.amazonaws.com/{bucket}/{key}
    Returns None if not an S3 URL.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.netloc
    if "amazonaws.com" not in host:
        return None
    # path-style: /{bucket}/{key...}
    parts = parsed.path.lstrip("/").split("/", 1)
    if len(parts) != 2:
        return None
    return parts[0], parts[1]  # bucket, key


@router.get("/{property_id}/model")
async def proxy_model(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Proxy the GLB model file to avoid browser CORS restrictions on S3.

    For S3 URLs: downloads via boto3 (handles private buckets).
    For other URLs: fetches via httpx.
    """
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()

    if not prop or not prop.model_3d_url:
        raise HTTPException(status_code=404, detail="No 3D model available for this property")

    model_url: str = prop.model_3d_url

    # Try boto3 for S3 URLs (handles private buckets)
    s3_parts = _parse_s3_url(model_url)
    if s3_parts and settings.aws_access_key_id and settings.aws_secret_access_key:
        import boto3
        from botocore.exceptions import ClientError

        bucket, key = s3_parts
        try:
            s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
            )
            obj = s3.get_object(Bucket=bucket, Key=key)
            body = obj["Body"].read()
            content_type = obj.get("ContentType", "model/gltf-binary")

            return Response(
                content=body,
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=3600"},
            )
        except ClientError as e:
            logger.error(f"S3 fetch failed for {property_id}: {e}")
            raise HTTPException(status_code=502, detail="Failed to fetch 3D model from S3")

    # Fallback: public URL (GitHub sample models etc.)
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            upstream = await client.get(model_url)
            upstream.raise_for_status()

        content_type = upstream.headers.get("content-type", "model/gltf-binary")

        return Response(
            content=upstream.content,
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=3600"},
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to proxy model for {property_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch 3D model from storage")

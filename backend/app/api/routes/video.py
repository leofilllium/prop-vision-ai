"""
Video Walkthrough API endpoints.

POST /generate/{property_id}     — trigger slideshow video generation from property photos
GET  /{property_id}/status       — poll generation status
GET  /{property_id}/stream       — proxy/stream the MP4 (handles S3 + local storage)
"""

import logging
import os
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response, FileResponse
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.dependencies import require_auth
from app.config import get_settings
from app.models.partner import Partner
from app.models.property import Property
from app.services.video_walkthrough_service import VideoWalkthroughService

settings = get_settings()
logger = logging.getLogger("propvision.video")
router = APIRouter()


@router.post("/generate/{property_id}", status_code=200)
async def generate_video_walkthrough(
    property_id: UUID,
    background_tasks: BackgroundTasks,
    _auth: Partner | None = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Kick off AI video walkthrough generation for a property.

    Returns immediately with status="processing". Poll GET /{property_id}/status
    for updates. When all deAPI img2video jobs complete, clips are concatenated
    with ffmpeg into a single MP4.
    """
    service = VideoWalkthroughService(db)

    try:
        result = await service.generate(property_id, background_tasks)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Video generation failed for {property_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start video generation")

    await db.commit()

    return {
        "property_id": str(property_id),
        "status": result.get("status"),
        "video_url": result.get("video_url"),
        "job_id": result.get("job_id"),
        "message": (
            "Video generation in progress. Poll /status for updates." if result.get("status") == "processing" else None
        ),
    }


@router.get("/{property_id}/status")
async def get_video_status(
    property_id: UUID,
    _auth: Partner | None = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Check video walkthrough generation status.

    Returns status (processing | completed | failed) and video_url when complete.
    Since ffmpeg runs synchronously in a thread executor, status will typically
    be 'completed' or 'failed' immediately after the generate call resolves.
    """
    service = VideoWalkthroughService(db)
    status = await service.get_status(property_id)

    if status is None:
        raise HTTPException(
            status_code=404,
            detail="No video generation job found for this property",
        )

    await db.commit()
    return status


@router.get("/{property_id}/stream")
async def stream_video(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Stream the video walkthrough MP4.

    Handles three storage backends:
    1. Local file system (local:///tmp/propvision_videos/{id}.mp4) — dev fallback
    2. Private S3 bucket — streamed via boto3
    3. Public CDN URL — proxied via httpx

    No API key required — video is a public asset once generated.
    """
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()

    if not prop or not prop.video_walkthrough_url:
        raise HTTPException(status_code=404, detail="No video walkthrough available for this property")

    video_url: str = prop.video_walkthrough_url

    # ── 1. Local file (dev fallback) ──────────────────────────────────────
    if video_url.startswith("local://"):
        local_path = video_url[len("local://") :]
        if not os.path.isfile(local_path):
            raise HTTPException(status_code=404, detail="Local video file not found")
        return FileResponse(
            local_path,
            media_type="video/mp4",
            headers={"Cache-Control": "public, max-age=86400", "Accept-Ranges": "bytes"},
        )

    # ── 2. S3 (private bucket via boto3) ──────────────────────────────────
    s3_parts = _parse_s3_url(video_url)
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
            body = obj["Body"]
            content_length = obj.get("ContentLength")

            headers = {
                "Cache-Control": "public, max-age=86400",
                "Accept-Ranges": "bytes",
            }
            if content_length:
                headers["Content-Length"] = str(content_length)

            return StreamingResponse(
                body.iter_chunks(chunk_size=1024 * 1024),
                media_type="video/mp4",
                headers=headers,
            )
        except ClientError as e:
            logger.error(f"S3 video fetch failed for {property_id}: {e}")
            raise HTTPException(status_code=502, detail="Failed to fetch video from S3")

    # ── 3. Public CDN URL (proxy) ──────────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            async with client.stream("GET", video_url) as upstream:
                upstream.raise_for_status()
                content_type = upstream.headers.get("content-type", "video/mp4")
                content_length = upstream.headers.get("content-length")

                headers = {"Cache-Control": "public, max-age=86400"}
                if content_length:
                    headers["Content-Length"] = content_length

                content = await upstream.aread()

        return Response(
            content=content,
            media_type=content_type,
            headers=headers,
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to proxy video for {property_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch video from storage")


def _parse_s3_url(url: str):
    """
    Parse path-style S3 URL → (bucket, key).
    Returns None if not an S3 URL.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if "amazonaws.com" not in parsed.netloc:
        return None
    parts = parsed.path.lstrip("/").split("/", 1)
    if len(parts) != 2:
        return None
    return parts[0], parts[1]

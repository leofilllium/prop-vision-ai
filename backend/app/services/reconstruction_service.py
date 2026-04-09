"""
3D reconstruction service powered by Meshy AI image-to-3D API.

Flow:
  1. auto_generate(property_id):
     - Fetch the property's first photo as a base64 data URI
       (works even if the photo URL isn't publicly reachable)
     - Submit to Meshy AI POST /openapi/v1/image-to-3d
     - Store the Meshy task_id in reconstruction_job_id, status = "processing"
     - Return immediately; frontend polls /status

  2. get_status(property_id):
     - Query Meshy GET /openapi/v1/image-to-3d/{task_id}
     - Map Meshy status → our status
     - On SUCCEEDED: store model_urls.glb in model_3d_url
     - On FAILED: mark as failed; fall back to sample GLB

Meshy task statuses: PENDING, IN_PROGRESS, SUCCEEDED, FAILED, EXPIRED
"""

import base64
import uuid
import logging
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import httpx
import boto3

from app.models.property import Property
from app.config import get_settings

logger = logging.getLogger("propvision.services.reconstruction")
settings = get_settings()

MESHY_API = "https://api.meshy.ai/openapi/v1"


class ReconstructionService:
    """Service for managing photo-to-3D reconstruction jobs via Meshy AI."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.s3_client = None
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region,
                    endpoint_url=settings.s3_endpoint_url or None,
                )
            except Exception:
                self.s3_client = None

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    async def auto_generate(self, property_id: uuid.UUID) -> dict:
        """
        Auto-generate a 3D model for a property from its first photo.

        - If the property already has a completed model, returns it immediately.
        - Otherwise submits to Meshy AI and returns status=processing.
        """
        result = await self.db.execute(select(Property).where(Property.id == property_id))
        prop = result.scalar_one_or_none()
        if not prop:
            raise ValueError(f"Property {property_id} not found")

        # Already done
        if prop.model_3d_url and prop.reconstruction_status == "completed":
            return {
                "model_url": prop.model_3d_url,
                "status": "completed",
            }

        # Already submitted — just return current state
        if prop.reconstruction_job_id and prop.reconstruction_status == "processing":
            return {
                "model_url": None,
                "status": "processing",
                "job_id": prop.reconstruction_job_id,
            }

        # Obtain source image as base64 data URI
        image_data_uri = await self._get_image_data_uri(prop, property_id)

        # Submit to Meshy AI
        if settings.meshy_api_key:
            try:
                task_id = await self._submit_meshy(image_data_uri, prop)
                await self.db.execute(
                    update(Property)
                    .where(Property.id == property_id)
                    .values(
                        reconstruction_status="processing",
                        reconstruction_job_id=task_id,
                    )
                )
                await self.db.flush()
                logger.info(f"Meshy task {task_id} submitted for property {property_id}")
                return {"model_url": None, "status": "processing", "job_id": task_id}
            except Exception as e:
                logger.warning(f"Meshy submission failed: {e} — falling back to sample GLB")

        # Meshy unavailable — do not apply fallback
        return {"model_url": None, "status": "failed"}

    async def get_status(self, property_id: uuid.UUID) -> Optional[dict]:
        """Poll Meshy for task status and persist result when done."""
        result = await self.db.execute(select(Property).where(Property.id == property_id))
        prop = result.scalar_one_or_none()

        if not prop or not prop.reconstruction_job_id:
            return None

        base_response = {
            "property_id": str(property_id),
            "job_id": prop.reconstruction_job_id,
            "status": prop.reconstruction_status or "unknown",
            "progress_percent": None,
            "model_url": prop.model_3d_url,
            "created_at": prop.created_at.isoformat() if prop.created_at else None,
        }

        if prop.reconstruction_status == "completed":
            base_response["progress_percent"] = 100
            return base_response

        if prop.reconstruction_status != "processing":
            return base_response

        # Poll Meshy
        if not settings.meshy_api_key:
            # No key — fail immediately
            return {"model_url": None, "status": "failed"}

        try:
            task = await self._poll_meshy(str(prop.reconstruction_job_id))
            meshy_status = task.get("status", "PENDING")
            progress = task.get("progress", 0)

            if meshy_status == "SUCCEEDED":
                glb_url = task.get("model_urls", {}).get("glb")
                if not glb_url:
                    raise ValueError("Meshy returned SUCCEEDED but no GLB URL")

                # Download and store in S3 (best-effort)
                stored_url = await self._store_glb_from_url(glb_url, property_id)
                final_url = stored_url or glb_url  # fall back to Meshy CDN if S3 fails

                await self.db.execute(
                    update(Property)
                    .where(Property.id == property_id)
                    .values(
                        reconstruction_status="completed",
                        model_3d_url=final_url,
                    )
                )
                await self.db.flush()
                base_response["status"] = "completed"
                base_response["model_url"] = final_url
                base_response["progress_percent"] = 100
                logger.info(f"3D model ready for property {property_id}: {final_url}")

            elif meshy_status in ("FAILED", "EXPIRED"):
                logger.warning(f"Meshy task {prop.reconstruction_job_id} {meshy_status}")
                base_response["status"] = "failed"

            else:
                # PENDING or IN_PROGRESS
                base_response["status"] = "processing"
                base_response["progress_percent"] = int(progress)

        except Exception as e:
            logger.warning(f"Failed to poll Meshy task: {e}")

        return base_response

    async def submit_reconstruction(
        self,
        property_id: uuid.UUID,
        photos: list[UploadFile],
    ) -> dict:
        """
        Submit a 3D reconstruction job from uploaded photos.
        Uses the first photo as the image for Meshy AI.
        """
        result = await self.db.execute(select(Property).where(Property.id == property_id))
        prop = result.scalar_one_or_none()
        if not prop:
            raise ValueError(f"Property {property_id} not found")

        # Read and encode the first photo
        photo_urls = []
        image_data_uri = None
        for i, photo in enumerate(photos):
            content = await photo.read()
            if i == 0:
                mime = photo.content_type or "image/jpeg"
                b64 = base64.b64encode(content).decode()
                image_data_uri = f"data:{mime};base64,{b64}"
            # Try to upload to S3
            key = f"photos/{property_id}/{i:03d}_{photo.filename}"
            try:
                if self.s3_client:
                    self.s3_client.put_object(
                        Bucket=settings.s3_bucket_name,
                        Key=key,
                        Body=content,
                        ContentType=photo.content_type or "image/jpeg",
                    )
                    url = f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}/{key}"
                else:
                    url = f"placeholder://{key}"
            except Exception:
                url = f"placeholder://{key}"
            photo_urls.append(url)

        logger.info(f"Received {len(photo_urls)} photos for property {property_id}")

        if not image_data_uri:
            raise ValueError("No photos provided")

        job_id = f"upload-{uuid.uuid4().hex[:12]}"
        model_url = None

        if settings.meshy_api_key:
            try:
                task_id = await self._submit_meshy(image_data_uri, prop)
                job_id = task_id
                await self.db.execute(
                    update(Property)
                    .where(Property.id == property_id)
                    .values(
                        reconstruction_status="processing",
                        reconstruction_job_id=job_id,
                    )
                )
                await self.db.flush()
            except Exception as e:
                logger.warning(f"Meshy submission failed: {e}")
                model_url = None
        else:
            model_url = None

        return {
            "job_id": job_id,
            "photo_count": len(photo_urls),
            "photo_urls": photo_urls,
            "model_url": model_url,
        }

    # ──────────────────────────────────────────────────────────────
    # Meshy AI helpers
    # ──────────────────────────────────────────────────────────────

    async def _submit_meshy(self, image_data_uri: str, prop: Property) -> str:
        """Submit to Meshy image-to-3D API. Returns task_id."""
        # Build a descriptive texture prompt from property data
        texture_prompt = (
            f"Realistic apartment building interior, {prop.district or 'modern'} district, "
            f"professional architectural photography, neutral lighting"
        )

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{MESHY_API}/image-to-3d",
                headers={
                    "Authorization": f"Bearer {settings.meshy_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "image_url": image_data_uri,
                    "ai_model": "meshy-6",  # Most stable model
                    "topology": "triangle",
                    "target_polycount": 30000,
                    "should_remesh": True,
                    "should_texture": True,
                    "enable_pbr": False,  # Faster without PBR
                    "texture_prompt": texture_prompt,
                    "target_formats": ["glb"],  # Only request GLB
                },
            )

        if resp.status_code not in (200, 201, 202):
            raise Exception(f"Meshy API error {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        task_id = data.get("result")
        if not task_id:
            raise Exception(f"Meshy returned no task id: {data}")
        return task_id

    async def _poll_meshy(self, task_id: str) -> dict:
        """Retrieve Meshy task status."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{MESHY_API}/image-to-3d/{task_id}",
                headers={"Authorization": f"Bearer {settings.meshy_api_key}"},
            )
        if resp.status_code != 200:
            raise Exception(f"Meshy poll error {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    # ──────────────────────────────────────────────────────────────
    # Image fetching utilities
    # ──────────────────────────────────────────────────────────────

    async def _get_image_data_uri(self, prop: Property, property_id: uuid.UUID) -> str:
        """
        Get a base64 data URI for the property's primary image.

        Tries the property's own photos first. If any are inaccessible
        (placeholder/demo URLs), falls back to a stock apartment image.
        """
        candidate_urls = list(prop.photos or [])

        # Filter out obvious placeholders
        real_urls = [
            u
            for u in candidate_urls
            if u and not u.startswith("placeholder://") and "propvision-demo.s3.amazonaws.com" not in u
        ]

        if not real_urls:
            raise Exception("No real source images found for 3D generation")

        for url in real_urls[:1]:
            try:
                async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
                        if content_type not in ("image/jpeg", "image/png", "image/jpg"):
                            content_type = "image/jpeg"
                        b64 = base64.b64encode(resp.content).decode()
                        logger.info(f"Got source image for {property_id}: {url[:60]}... ({len(resp.content)} bytes)")
                        return f"data:{content_type};base64,{b64}"
            except Exception as e:
                logger.debug(f"Could not fetch {url}: {e}")

        raise Exception("Could not obtain a source image for 3D generation")

    # ──────────────────────────────────────────────────────────────
    # GLB storage
    # ──────────────────────────────────────────────────────────────

    async def _store_glb_from_url(self, glb_url: str, property_id: uuid.UUID) -> Optional[str]:
        """Download a GLB file and upload it to S3. Returns stored URL or None."""
        if not self.s3_client:
            return None
        try:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                resp = await client.get(glb_url)
                if resp.status_code != 200:
                    return None
                glb_key = f"models/{property_id}.glb"
                self.s3_client.put_object(
                    Bucket=settings.s3_bucket_name,
                    Key=glb_key,
                    Body=resp.content,
                    ContentType="model/gltf-binary",
                )
                return f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}/{glb_key}"
        except Exception as e:
            logger.warning(f"S3 GLB store failed: {e}")
            return None

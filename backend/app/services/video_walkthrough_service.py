"""
Video Walkthrough Service — Pollinations img2video slideshow pipeline.

How it works:
  1. generate(property_id, background_tasks):
     - Validates property and marks status = "processing" immediately
     - Returns to the HTTP caller right away (no blocking)
     - Schedules _submit_jobs_background via FastAPI BackgroundTasks (or
       asyncio.create_task as fallback), which runs after the response is sent:
         • For each photo (up to MAX_IMAGES), calls Pollinations GET /image/{prompt}
           with model=ltx-2 and the photo URL as a reference image
         • Each call is synchronous — returns MP4 bytes directly (no polling)
         • Jobs run sequentially with SUBMIT_DELAY_S between them to respect rate limits
     - A per-property asyncio lock prevents duplicate concurrent submissions

  2. get_status(property_id):
     - Simply reads the DB record — no API polling needed (generation is synchronous)
     - When background task finishes: status = "completed", video_walkthrough_url set
     - If background task fails: status = "failed"

Result: one slideshow MP4 built from up to 5 property photos.

Requires POLLINATIONS_API_KEY environment variable and ffmpeg in PATH/Docker.
Model: wan-fast (Wan 2.2 image-to-video) via https://gen.pollinations.ai
  wan-fast animates directly from the uploaded image — not a text-to-video model.
"""

import asyncio
import logging
import os
import random
import subprocess
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from urllib.parse import quote

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.property import Property

logger = logging.getLogger("propvision.services.video_walkthrough")
settings = get_settings()

# Thread pool for blocking ffmpeg operations
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="video")

# Max photos → one Pollinations video job each
MAX_IMAGES = 5

# Seconds to wait between sequential video generation requests (rate-limit guard)
SUBMIT_DELAY_S = 5

POLLINATIONS_BASE = "https://gen.pollinations.ai"

# Per-property locks to prevent duplicate concurrent submissions
_generate_locks: dict[uuid.UUID, asyncio.Lock] = {}


# ------------------------------------------------------------------
# Background submission task (runs after HTTP response is sent)
# ------------------------------------------------------------------


async def _submit_jobs_background(property_id: uuid.UUID) -> None:
    """Generate video clips in the background using a fresh DB session."""
    from app.database import async_session_factory  # avoid circular import at module level

    logger.info(f"Background video generation started for {property_id}")
    async with async_session_factory() as session:
        try:
            service = VideoWalkthroughService(session)
            await service._do_generate(property_id)
            await session.commit()
        except Exception as e:
            logger.error(f"Background video generation failed for {property_id}: {e}")
            try:
                await session.rollback()
            except Exception:
                pass
            async with async_session_factory() as err_session:
                await err_session.execute(
                    update(Property).where(Property.id == property_id).values(video_generation_status="failed")
                )
                await err_session.commit()


# ------------------------------------------------------------------
# Service
# ------------------------------------------------------------------


class VideoWalkthroughService:
    """Generates a property slideshow video via Pollinations ltx-2 + ffmpeg concat."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.s3_client = None
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            try:
                import boto3

                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region,
                    endpoint_url=settings.s3_endpoint_url or None,
                )
            except Exception:
                self.s3_client = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(self, property_id: uuid.UUID, background_tasks=None) -> dict:
        """
        Validate property, mark as processing, schedule background generation, return immediately.
        A per-property lock prevents duplicate concurrent submissions.
        """
        if property_id not in _generate_locks:
            _generate_locks[property_id] = asyncio.Lock()
        if _generate_locks[property_id].locked():
            return {"video_url": None, "status": "processing", "job_id": None}
        async with _generate_locks[property_id]:
            return await self._generate_locked(property_id, background_tasks)

    async def _generate_locked(self, property_id: uuid.UUID, background_tasks=None) -> dict:
        result = await self.db.execute(select(Property).where(Property.id == property_id))
        prop = result.scalar_one_or_none()
        if not prop:
            raise ValueError(f"Property {property_id} not found")

        if prop.video_walkthrough_url and prop.video_generation_status == "completed":
            return {"video_url": prop.video_walkthrough_url, "status": "completed"}

        if prop.video_generation_status == "processing":
            return {"video_url": None, "status": "processing", "job_id": prop.video_generation_job_id}

        if not settings.pollinations_api_key:
            return {"video_url": None, "status": "failed", "error": "Pollinations API not configured"}

        real_urls = [
            u
            for u in (prop.photos or [])
            if u and not u.startswith("placeholder://") and "propvision-demo.s3.amazonaws.com" not in u
        ][:MAX_IMAGES]

        if not real_urls:
            return {"video_url": None, "status": "failed", "error": "No real photos available"}

        # Mark processing and return immediately — actual generation is backgrounded
        await self.db.execute(
            update(Property)
            .where(Property.id == property_id)
            .values(video_generation_status="processing", video_generation_job_id=None)
        )
        await self.db.flush()

        if background_tasks is not None:
            background_tasks.add_task(_submit_jobs_background, property_id)
        else:
            asyncio.create_task(_submit_jobs_background(property_id))

        logger.info(f"Scheduled background video generation for {property_id} ({len(real_urls)} photos)")
        return {"video_url": None, "status": "processing", "job_id": None}

    async def _do_generate(self, property_id: uuid.UUID) -> None:
        """Generate video clips via Pollinations API and concatenate. Called from background task."""
        result = await self.db.execute(select(Property).where(Property.id == property_id))
        prop = result.scalar_one_or_none()
        if not prop:
            logger.error(f"Property {property_id} not found in background generation")
            return

        real_urls = [
            u
            for u in (prop.photos or [])
            if u and not u.startswith("placeholder://") and "propvision-demo.s3.amazonaws.com" not in u
        ][:MAX_IMAGES]

        if not real_urls:
            await self.db.execute(
                update(Property).where(Property.id == property_id).values(video_generation_status="failed")
            )
            return

        rooms_str = f"{prop.rooms}-room " if prop.rooms else ""
        district_str = f" in {prop.district}" if prop.district else ""
        area_str = f", {prop.area_sqm}m²" if prop.area_sqm else ""
        prompt = (
            f"Smooth cinematic interior walkthrough of a {rooms_str}apartment"
            f"{district_str}{area_str}. "
            f"Slow pan through rooms, professional real estate photography style, "
            f"natural warm lighting, steady camera movement, high quality."
        )

        # Generate clips sequentially to respect rate limits
        clip_bytes_list: list[bytes] = []
        for idx, photo_url in enumerate(real_urls):
            raw_url = photo_url.replace("/media/n/", "/media/o/")
            try:
                # Upload image to Pollinations media storage so it's used as the
                # animation source (first frame), not merely a style reference
                hosted_url = await self._upload_image_to_pollinations(raw_url, idx, property_id)
                clip_bytes = await self._generate_clip(prompt, hosted_url, idx, property_id)
                clip_bytes_list.append(clip_bytes)
                logger.info(f"Generated clip {idx + 1}/{len(real_urls)} for {property_id} ({len(clip_bytes):,} bytes)")
            except Exception as e:
                logger.warning(f"Clip {idx} generation failed for {property_id}: {e}")

            if idx < len(real_urls) - 1:
                await asyncio.sleep(SUBMIT_DELAY_S)

        if not clip_bytes_list:
            await self.db.execute(
                update(Property).where(Property.id == property_id).values(video_generation_status="failed")
            )
            return

        # Concat in thread executor and store
        logger.info(f"All {len(clip_bytes_list)} clips ready for {property_id}, concatenating…")
        try:
            final_url = await asyncio.get_event_loop().run_in_executor(
                _executor,
                self._concat_and_store_sync,
                clip_bytes_list,
                property_id,
            )
        except Exception as e:
            logger.error(f"ffmpeg concat failed for {property_id}: {e}")
            await self.db.execute(
                update(Property).where(Property.id == property_id).values(video_generation_status="failed")
            )
            return

        await self.db.execute(
            update(Property)
            .where(Property.id == property_id)
            .values(video_generation_status="completed", video_walkthrough_url=final_url)
        )
        logger.info(f"Slideshow video ready for {property_id}: {final_url}")

    async def get_status(self, property_id: uuid.UUID) -> Optional[dict]:
        """Return the current generation status from DB. No API polling needed."""
        result = await self.db.execute(select(Property).where(Property.id == property_id))
        prop = result.scalar_one_or_none()
        if not prop:
            return None

        return {
            "property_id": str(property_id),
            "job_id": prop.video_generation_job_id,
            "status": prop.video_generation_status or "unknown",
            "video_url": prop.video_walkthrough_url,
        }

    # ------------------------------------------------------------------
    # Pollinations API helpers
    # ------------------------------------------------------------------

    async def _upload_image_to_pollinations(
        self,
        image_url: str,
        idx: int,
        property_id: uuid.UUID,
    ) -> str:
        """Download the property photo and upload it to Pollinations media storage.
        Returns a stable media.pollinations.ai URL that the generation API can use
        as an animation source (first frame) rather than a loose style reference."""
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            dl = await client.get(image_url)
        if dl.status_code != 200 or len(dl.content) < 1000:
            raise Exception(f"Photo {idx} download failed (status={dl.status_code}, size={len(dl.content)})")

        content_type = dl.headers.get("content-type", "").split(";")[0].strip() or "image/jpeg"
        ext = "png" if "png" in content_type else "jpg"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://media.pollinations.ai/upload",
                headers={"Authorization": f"Bearer {settings.pollinations_api_key}"},
                files={"file": (f"photo_{idx}.{ext}", dl.content, content_type)},
            )

        if resp.status_code not in (200, 201):
            raise Exception(f"Pollinations media upload failed {resp.status_code}: {resp.text[:200]}")

        upload_data = resp.json()
        hosted_url = upload_data.get("url")
        if not hosted_url:
            raise Exception(f"Pollinations media upload returned no URL: {upload_data}")

        logger.info(f"Uploaded photo {idx} for {property_id} to Pollinations media: {hosted_url}")
        return hosted_url

    async def _generate_clip(
        self,
        prompt: str,
        hosted_image_url: str,
        idx: int,
        property_id: uuid.UUID,
    ) -> bytes:
        """Animate a single image via Pollinations GET /image/{prompt} with wan-fast.
        wan-fast is an image-to-video model — it animates directly from the hosted image.
        Returns MP4 bytes (~5 seconds per clip)."""
        encoded_prompt = quote(prompt, safe="")
        params = {
            "model": "wan-fast",
            "image": hosted_image_url,
            "aspectRatio": "16:9",
            "duration": "5",
            "seed": str(random.randint(0, 2**31 - 1)),
        }
        param_str = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in params.items())
        url = f"{POLLINATIONS_BASE}/image/{encoded_prompt}?{param_str}"

        max_retries = 4
        for attempt in range(max_retries):
            # Video generation can take a while — use a generous timeout
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=30, read=300, write=30, pool=30),
                follow_redirects=True,
            ) as client:
                resp = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {settings.pollinations_api_key}"},
                )

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 60))
                wait = min(retry_after, 120)
                logger.warning(
                    f"Pollinations 429 for clip {idx} of {property_id}, "
                    f"waiting {wait}s (attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(wait)
                continue

            if resp.status_code == 402:
                raise Exception("Pollinations insufficient balance (402)")

            if resp.status_code != 200:
                raise Exception(f"Pollinations error {resp.status_code}: {resp.text[:300]}")

            content_type = resp.headers.get("content-type", "")
            if "video" not in content_type and len(resp.content) < 1000:
                raise Exception(f"Pollinations returned unexpected content ({content_type}, {len(resp.content)} bytes)")

            return resp.content

        raise Exception(f"Pollinations 429 after {max_retries} retries for clip {idx}")

    # ------------------------------------------------------------------
    # ffmpeg concat + store (runs in thread executor)
    # ------------------------------------------------------------------

    def _concat_and_store_sync(self, clip_bytes_list: list[bytes], property_id: uuid.UUID) -> str:
        """Write clips to disk, ffmpeg-concat into one slideshow MP4, store and return URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            clip_paths: list[str] = []
            for idx, clip_bytes in enumerate(clip_bytes_list):
                dest = os.path.join(tmpdir, f"clip_{idx}.mp4")
                with open(dest, "wb") as f:
                    f.write(clip_bytes)
                clip_paths.append(dest)

            if len(clip_paths) == 1:
                with open(clip_paths[0], "rb") as f:
                    return self._store_video_sync(f.read(), property_id)

            concat_list = os.path.join(tmpdir, "concat.txt")
            with open(concat_list, "w") as f:
                for p in clip_paths:
                    f.write(f"file '{p}'\n")

            output = os.path.join(tmpdir, "slideshow.mp4")
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    concat_list,
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "23",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    output,
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg failed: {result.stderr[-500:]}")

            logger.info(f"Concatenated {len(clip_paths)} clips into slideshow for {property_id}")
            with open(output, "rb") as f:
                return self._store_video_sync(f.read(), property_id)

    # ------------------------------------------------------------------
    # Video storage
    # ------------------------------------------------------------------

    def _store_video_sync(self, video_bytes: bytes, property_id: uuid.UUID) -> str:
        """Upload to S3 or fall back to local /tmp."""
        video_key = f"videos/{property_id}.mp4"
        if self.s3_client:
            try:
                self.s3_client.put_object(
                    Bucket=settings.s3_bucket_name,
                    Key=video_key,
                    Body=video_bytes,
                    ContentType="video/mp4",
                )
                stored = f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}/{video_key}"
                logger.info(f"Uploaded slideshow for {property_id} to S3: {stored}")
                return stored
            except Exception as e:
                logger.warning(f"S3 upload failed ({e}), falling back to local storage")

        local_dir = "/tmp/propvision_videos"
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, f"{property_id}.mp4")
        with open(local_path, "wb") as f:
            f.write(video_bytes)
        logger.info(f"Stored slideshow locally for {property_id}: {local_path}")
        return f"local://{local_path}"

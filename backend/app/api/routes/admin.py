"""
Admin routes: user management, system statistics, and analytics.
"""

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_admin_user
from app.database import get_db
from app.models.user import User
from app.models.property import Property
from app.models.partner import Partner

router = APIRouter()


# ── Response Models ───────────────────────────────────────────────────────────


class UserListItem(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class SystemStats(BaseModel):
    # Users
    total_users: int
    active_users: int
    inactive_users: int
    admin_users: int
    viewer_users: int
    analyst_users: int
    new_users_today: int
    new_users_week: int
    # Properties
    total_properties: int
    active_properties: int
    properties_with_3d: int
    properties_with_video: int
    avg_price: float
    total_partners: int
    active_partners: int
    # Districts breakdown
    districts: list[dict]
    # Recent signups
    recent_users: list[dict]


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Rich system statistics for the admin dashboard."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    # ── User counts ───────────────────────────────────────────────────────────
    def user_count(where=None):
        q = select(func.count(User.id))
        if where is not None:
            q = q.where(where)
        return q

    total_users = (await db.execute(user_count())).scalar() or 0
    active_users = (await db.execute(user_count(User.is_active == True))).scalar() or 0  # noqa: E712
    inactive_users = total_users - active_users
    admin_users = (await db.execute(user_count(User.role == "admin"))).scalar() or 0
    viewer_users = (await db.execute(user_count(User.role == "viewer"))).scalar() or 0
    analyst_users = (await db.execute(user_count(User.role == "analyst"))).scalar() or 0
    new_today = (await db.execute(user_count(User.created_at >= today_start))).scalar() or 0
    new_week = (await db.execute(user_count(User.created_at >= week_start))).scalar() or 0

    # ── Property counts ───────────────────────────────────────────────────────
    total_props = (await db.execute(select(func.count(Property.id)))).scalar() or 0
    active_props = (
        await db.execute(select(func.count(Property.id)).where(Property.is_active == True))  # noqa: E712
    ).scalar() or 0
    props_3d = (
        await db.execute(select(func.count(Property.id)).where(Property.reconstruction_status == "completed"))
    ).scalar() or 0
    props_video = (
        await db.execute(select(func.count(Property.id)).where(Property.video_generation_status == "completed"))
    ).scalar() or 0
    avg_price_result = (await db.execute(select(func.avg(Property.price)))).scalar()
    avg_price = float(avg_price_result) if avg_price_result else 0.0

    # ── Partners ──────────────────────────────────────────────────────────────
    total_partners = (await db.execute(select(func.count(Partner.id)))).scalar() or 0
    active_partners = (
        await db.execute(select(func.count(Partner.id)).where(Partner.is_active == True))  # noqa: E712
    ).scalar() or 0

    # ── District breakdown ────────────────────────────────────────────────────
    district_rows = await db.execute(
        select(Property.district, func.count(Property.id).label("count"))
        .where(Property.district.isnot(None))
        .group_by(Property.district)
        .order_by(func.count(Property.id).desc())
        .limit(10)
    )
    districts = [{"district": r.district, "count": r.count} for r in district_rows]

    # ── Recent signups ────────────────────────────────────────────────────────
    recent_rows = await db.execute(select(User).order_by(User.created_at.desc()).limit(5))
    recent_users = [
        {
            "id": str(u.id),
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in recent_rows.scalars().all()
    ]

    return SystemStats(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        admin_users=admin_users,
        viewer_users=viewer_users,
        analyst_users=analyst_users,
        new_users_today=new_today,
        new_users_week=new_week,
        total_properties=total_props,
        active_properties=active_props,
        properties_with_3d=props_3d,
        properties_with_video=props_video,
        avg_price=avg_price,
        total_partners=total_partners,
        active_partners=active_partners,
        districts=districts,
        recent_users=recent_users,
    )


@router.get("/users", response_model=list[UserListItem])
async def list_users(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.get("/users/{user_id}", response_model=UserListItem)
async def get_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=UserListItem)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's role and/or active status (admin only)."""
    if user_id == admin.id and payload.role and payload.role != "admin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself from admin role")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user (admin only)."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()

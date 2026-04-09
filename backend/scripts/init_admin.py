#!/usr/bin/env python3
"""
Initialize the admin user for the PropVision.AI application.
Creates admin@example.com with password 'admin' and 'admin' role.
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Add parent directory to path for imports
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.models.user import User
from app.services.auth_service import hash_password
from app.database import Base

settings = get_settings()


async def init_admin():
    """Create the admin user if it doesn't exist."""
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=False)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if admin already exists
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print(f"✓ Admin user already exists: {existing_admin.email}")
            return

        # Create new admin user
        admin_user = User(
            email="admin@example.com",
            hashed_password=hash_password("admin"),
            role="admin",
            is_active=True,
        )

        session.add(admin_user)
        await session.commit()

        print("✓ Admin user created successfully!")
        print(f"  Email: admin@example.com")
        print(f"  Password: admin")
        print(f"  Role: admin")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_admin())

#!/bin/bash
set -e

echo "🚀 PropVision.AI Backend Starting..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! pg_isready -h postgres -U propvision -d propvision 2>/dev/null; do
  sleep 2
done
echo "✓ PostgreSQL ready"

# Run migrations
echo "📦 Running database migrations..."
alembic upgrade head

# Initialize admin user
echo "👤 Initializing admin user..."
python3 << 'PYTHON_EOF'
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import get_settings
from app.models.user import User
from app.services.auth_service import hash_password

async def init_admin():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        existing = result.scalar_one_or_none()

        if existing:
            print("✓ Admin user already exists")
        else:
            admin = User(
                email="admin@example.com",
                hashed_password=hash_password("admin"),
                role="admin",
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            print("✓ Admin user created: admin@example.com / admin")

    await engine.dispose()

try:
    asyncio.run(init_admin())
except Exception as e:
    print(f"⚠️  Admin init error (non-fatal): {e}")
PYTHON_EOF

echo "✅ Backend initialization complete!"
echo ""
echo "🎯 Admin Credentials:"
echo "   Email: admin@example.com"
echo "   Password: admin"
echo ""

# Start the application
echo "🔥 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 58000 --workers 2 --loop uvloop

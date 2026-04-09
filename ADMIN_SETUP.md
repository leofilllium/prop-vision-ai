# Admin Panel Setup Guide

## Overview

The PropVision.AI application now includes a fully functional admin panel for managing users and system statistics.

### Default Admin Credentials
- **Email:** `admin@example.com`
- **Password:** `admin`

> ⚠️ **SECURITY WARNING:** Change these credentials immediately after first login in a production environment.

---

## Docker Deployment

### Quick Start

1. **Clone and navigate to project:**
   ```bash
   cd prop-vision-ai
   ```

2. **Build and start services:**
   ```bash
   docker-compose up -d --build
   ```

   This command will:
   - Build the backend with the new admin initialization
   - Start PostgreSQL, Redis, API, Frontend, and Nginx
   - Automatically run database migrations
   - Automatically create the admin user

3. **Access the application:**
   - **Frontend:** http://localhost:50080
   - **API Docs:** http://localhost:50080/api/v1/docs
   - **Admin Panel:** http://localhost:50080/admin (after login)

4. **Check initialization logs:**
   ```bash
   docker logs propvision-api
   ```

   You should see output like:
   ```
   🚀 PropVision.AI Backend Starting...
   ⏳ Waiting for PostgreSQL...
   ✓ PostgreSQL ready
   📦 Running database migrations...
   👤 Initializing admin user...
   ✓ Admin user created: admin@example.com / admin
   ✅ Backend initialization complete!
   ```

---

## Admin Panel Features

### Login
1. Go to http://localhost:50080/login
2. Enter credentials:
   - Email: `admin@example.com`
   - Password: `admin`
3. After login, admin users see an "Admin" link in the navigation

### Dashboard
View system statistics:
- **Total Users:** Count of all users in the system
- **Active Users:** Count of users with `is_active = true`
- **Admin Users:** Count of users with `admin` role

### User Management
1. Click the "Admin" link in navigation
2. View the user management table with all users
3. Click "Edit" on any user to:
   - Change their role (Viewer → Analyst → Admin)
   - Toggle active/inactive status
   - Delete the user (can't delete yourself)

---

## Backend Routes

All admin routes require admin authentication (`role == 'admin'`):

### System Statistics
```
GET /api/v1/admin/stats
Response: { total_users, active_users, admin_users }
```

### User Management
```
GET /api/v1/admin/users                    → List all users
GET /api/v1/admin/users/{user_id}          → Get single user
PATCH /api/v1/admin/users/{user_id}        → Update user (role, is_active)
DELETE /api/v1/admin/users/{user_id}       → Delete user
```

---

## Changing Admin Credentials

### Via Frontend
1. Login as admin
2. Register a new user
3. Edit that user in Admin panel and promote to `admin` role
4. Recommend changing default admin password (currently not possible via UI, do in DB)

### Via Database
```sql
-- Connect to PostgreSQL
docker exec -it propvision-postgres psql -U propvision -d propvision

-- Update admin password (replace HASHED_PASSWORD with actual bcrypt hash)
UPDATE users SET hashed_password = '$2b$12$...' WHERE email = 'admin@example.com';

-- Verify
SELECT id, email, role, is_active FROM users WHERE role = 'admin';
```

---

## Troubleshooting

### Admin user not created
1. Check logs: `docker logs propvision-api`
2. Verify database is running: `docker ps`
3. If needed, manually initialize:
   ```bash
   docker exec propvision-api python3 << 'EOF'
   import asyncio
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
   from sqlalchemy.orm import sessionmaker
   from sqlalchemy import select
   from app.config import get_settings
   from app.models.user import User
   from app.services.auth_service import hash_password

   async def init():
       settings = get_settings()
       engine = create_async_engine(settings.database_url)
       async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
       async with async_session() as session:
           user = User(
               email="admin@example.com",
               hashed_password=hash_password("admin"),
               role="admin",
               is_active=True,
           )
           session.add(user)
           await session.commit()
       await engine.dispose()

   asyncio.run(init())
   EOF
   ```

### Admin panel shows "Access Denied"
- Ensure you're logged in with an admin account
- Check user role in database:
  ```bash
  docker exec -it propvision-postgres psql -U propvision -d propvision
  SELECT email, role FROM users;
  ```

### Can't login
1. Verify admin user exists in database
2. Check frontend is connecting to correct backend URL
3. Verify no CORS issues in browser console

---

## Production Recommendations

1. **Change default admin credentials immediately**
2. **Use environment variables for sensitive data**
3. **Enable HTTPS in Nginx**
4. **Set up strong database passwords**
5. **Regular database backups**
6. **Monitor admin activity and user access**
7. **Implement password reset functionality**
8. **Add audit logging for admin actions**

---

## API Examples

### Get Admin Stats
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:50080/api/v1/admin/stats
```

### List All Users
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:50080/api/v1/admin/users
```

### Update User Role
```bash
curl -X PATCH \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}' \
  http://localhost:50080/api/v1/admin/users/{user_id}
```

### Delete User
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:50080/api/v1/admin/users/{user_id}
```

---

## File Structure

New files added:
```
backend/
├── entrypoint.sh                    ← Initialization script
└── app/api/routes/admin.py          ← Admin routes

frontend/
└── src/components/Admin/
    ├── AdminPage.tsx                ← Admin panel component
    └── AdminPage.css                ← Styling
```

Modified files:
```
backend/
├── Dockerfile                       ← Uses entrypoint.sh
├── app/main.py                      ← Mounts admin routes
├── app/api/dependencies.py          ← Added get_admin_user()

frontend/
├── src/App.tsx                      ← Added /admin route
├── src/api/client.ts                ← Added admin API functions
├── src/hooks/useApi.ts              ← Added admin hooks
└── src/components/Nav/NavBar.tsx    ← Added Admin link for admins
```

---

## Next Steps

1. Deploy using docker-compose
2. Login with admin@example.com / admin
3. Create additional admin accounts
4. Change default admin password
5. Monitor user activity and system health

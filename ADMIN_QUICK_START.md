# Admin Panel - Quick Start (30 seconds)

## Deploy
```bash
cd prop-vision-ai
docker-compose up -d --build
```

## Login
- URL: http://localhost:50080/login
- Email: `admin@example.com`
- Password: `admin`

## Access Admin Panel
- Click "Admin" link in top navigation
- Manage users and view system stats

## Verify Deployment
```bash
# Check all services running
docker ps

# Check admin was created
docker logs propvision-api | grep "Admin user"

# Or verify in database
docker exec -it propvision-postgres psql -U propvision -d propvision -c "SELECT email, role FROM users;"
```

## What's Included
✅ Admin authentication & role checking
✅ User management (list, edit, delete)
✅ System statistics dashboard
✅ Admin panel UI with dark theme
✅ Auto-initialization on startup
✅ Protected admin routes (403 for non-admins)

---

**Full setup guide:** See `ADMIN_SETUP.md`

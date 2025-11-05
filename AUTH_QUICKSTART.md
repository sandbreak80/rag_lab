# 🔐 Authentication Quick Start

**Date:** November 5, 2025
**Status:** ✅ Implemented (Week 9 Fast Track)

---

## ❓ Is There a Default Login?

**Short Answer:** **NO** - There are no default credentials.

**You must register** the first user to get started.

---

## 🚀 Getting Started (First Time Setup)

### Step 1: Open the Application

```bash
# Frontend is running at:
http://localhost:3000
```

### Step 2: Register Your Admin Account

1. Click **"Sign Up"** in the top-right corner (or go to `/register`)
2. Fill in the registration form:
   - **Username:** Choose any username (min 3 characters)
   - **Email:** Your email address
   - **Password:** Choose a strong password (min 8 characters)
3. Click **"Create Account"**

**✨ IMPORTANT:** The **first user to register automatically becomes an admin!**

### Step 3: Log In

1. After registration, you'll be redirected to login
2. Enter your username and password
3. Click **"Sign In"**

**✅ You're now logged in!**

---

## 👤 User Types

### Admin User (First Registered User)

**How to Become Admin:**
- Be the first person to register
- The system automatically grants admin privileges

**Admin Capabilities:**
- Full access to all features
- View all users (future feature)
- Manage system settings (future feature)
- Higher rate limits (1000 req/min vs 100 req/min)

**First Admin Example:**
```bash
# First user to register:
Username: alice
Email: alice@example.com
Password: SecurePass123

# This user becomes admin automatically
```

### Regular User (Subsequent Users)

**Regular User Capabilities:**
- Access to chat and RAG features
- Standard rate limits (100 req/min authenticated, 10 req/min anonymous)
- Profile management
- Cannot manage other users

---

## 🎮 Quick Test Commands

### Test Registration (via API)

```bash
curl -X POST http://localhost:8014/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123"
  }'

# Response:
{
  "success": true,
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "is_admin": true  # ← First user gets admin!
  },
  "message": "User registered successfully"
}
```

### Test Login (via API)

```bash
curl -X POST http://localhost:8014/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123"
  }'

# Response:
{
  "success": true,
  "message": "Logged in successfully",
  "access_token": "eyJ0eXAiOiJKV1QiLC...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLC..."
}
```

### Test Authenticated Request

```bash
# Get your profile
curl -X GET http://localhost:8014/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# Response:
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_admin": true,
  "created_at": "2025-11-05T10:30:00",
  "updated_at": "2025-11-05T10:30:00"
}
```

---

## 🔑 Token Management

### Access Token
- **Lifetime:** 1 hour
- **Purpose:** Authenticates API requests
- **How to Use:** Add to `Authorization: Bearer <token>` header

### Refresh Token
- **Lifetime:** 30 days
- **Purpose:** Get a new access token without re-logging in
- **How to Use:** Call `/refresh` endpoint

### Refresh Your Token

```bash
curl -X POST http://localhost:8014/refresh \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN_HERE"

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLC..."  # New access token
}
```

---

## 🛡️ Security Features

### Password Requirements
- ✅ Minimum 8 characters
- ✅ Hashed with bcrypt (cost factor 12)
- ✅ Never stored in plaintext

### Username Requirements
- ✅ Minimum 3 characters
- ✅ Must be unique
- ✅ Case-sensitive

### Email Requirements
- ✅ Must be valid format
- ✅ Must be unique
- ✅ Converted to lowercase

### JWT Security
- ✅ Signed with secret key
- ✅ Includes expiration time
- ✅ Includes user ID
- ✅ Token revocation on logout

---

## 🚫 Rate Limiting

Authentication affects your rate limits:

### Anonymous (Not Logged In)
- **Limit:** 10 requests per minute
- **Use Case:** Quick testing, public demos

### Authenticated (Regular User)
- **Limit:** 100 requests per minute
- **Use Case:** Normal usage

### Authenticated (Admin)
- **Limit:** 1000 requests per minute
- **Use Case:** Heavy testing, batch operations

---

## 📚 Common Scenarios

### Scenario 1: Fresh Install - First Time Setup

```bash
# 1. Open application
open http://localhost:3000

# 2. Click "Sign Up"
# 3. Register as:
Username: admin
Email: admin@mylab.com
Password: AdminPass123!

# 4. ✨ You're now the admin!
```

### Scenario 2: Create Additional Users

```bash
# Admin already exists, create a regular user:

# 1. Logout (if logged in)
# 2. Click "Sign Up"
# 3. Register as:
Username: developer
Email: dev@mylab.com
Password: DevPass123!

# 4. This user is NOT admin (admin already exists)
```

### Scenario 3: Forgot Who the Admin Is

```bash
# Check the database:
docker exec -it rag-auth-service python3 << 'EOF'
from app.models import db, User
from app.service import app

with app.app_context():
    admin = User.query.filter_by(is_admin=True).first()
    if admin:
        print(f"Admin: {admin.username} ({admin.email})")
    else:
        print("No admin found! Register a user to become admin.")
EOF
```

### Scenario 4: Reset Everything

```bash
# Delete the auth database and start fresh:
docker compose down
docker volume rm rag_lab_auth-data
docker compose up -d

# Now the NEXT person to register becomes admin again
```

---

## 🔧 Configuration

### Environment Variables

Set in `config.env` or `docker-compose.yml`:

```bash
# JWT Secret (CHANGE THIS IN PRODUCTION!)
JWT_SECRET_KEY=your-super-secret-jwt-key-here

# Token Expiration
JWT_ACCESS_TOKEN_EXPIRES=3600      # 1 hour
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days

# Database Path
DB_PATH=/data/auth.db
```

### Database Location

The authentication database is stored in a Docker volume:

```bash
# Volume name: auth-data
# Mount point: /data/auth.db (inside container)

# View database:
docker exec -it rag-auth-service sqlite3 /data/auth.db "SELECT * FROM user;"
```

---

## 🐛 Troubleshooting

### Problem: Can't Register - "Username already exists"

**Solution:**
```bash
# Check existing users:
curl http://localhost:8014/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Or reset the database (see Scenario 4 above)
```

### Problem: Can't Login - "Invalid credentials"

**Checklist:**
- ✅ Username is correct (case-sensitive)
- ✅ Password is correct
- ✅ User was successfully registered (check response)
- ✅ Auth service is running: `docker ps | grep auth-service`

### Problem: Token Expired

**Solution:**
```bash
# Use refresh token to get new access token:
curl -X POST http://localhost:8014/refresh \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"
```

### Problem: No Admin User

**Solution:**
```bash
# The first user to register becomes admin
# If no users exist, just register:

curl -X POST http://localhost:8014/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "SecurePass123"
  }'

# This user will be admin
```

---

## 📖 API Endpoints

### Public Endpoints (No Auth Required)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/register` | POST | Create new user |
| `/login` | POST | Get JWT tokens |
| `/health` | GET | Service health check |

### Protected Endpoints (Auth Required)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/profile` | GET | Get user profile |
| `/profile` | PUT | Update profile |
| `/change_password` | POST | Change password |
| `/logout` | POST | Revoke access token |
| `/refresh` | POST | Get new access token |

### Admin Endpoints (Admin Only)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/admin/users` | GET | List all users |
| `/admin/user/<id>` | DELETE | Delete a user |

---

## 🎓 Learning Objectives

By using this auth system, you'll learn:

1. **JWT Authentication**
   - How tokens work
   - Access vs refresh tokens
   - Token expiration and renewal

2. **Password Security**
   - bcrypt hashing
   - Why plaintext storage is bad
   - Cost factors and performance

3. **User Management**
   - Registration flows
   - Login flows
   - Session management

4. **Authorization**
   - Role-based access (admin vs user)
   - Protected routes
   - Rate limiting by user

5. **API Security**
   - Bearer token authentication
   - Token revocation
   - Security headers

---

## 🚀 Next Steps

### For Learning:
1. ✅ Register and login via UI
2. ✅ Inspect JWT tokens at [jwt.io](https://jwt.io)
3. ✅ Try API calls with curl
4. ✅ Observe rate limiting differences (anonymous vs authenticated)

### For Development:
1. ⏳ Add profile picture upload
2. ⏳ Add password reset via email
3. ⏳ Add OAuth (Google, GitHub)
4. ⏳ Add user activity logs
5. ⏳ Add admin dashboard

---

## 📞 Support

### Check Service Health

```bash
curl http://localhost:8014/health

# Should return:
{
  "status": "healthy",
  "service": "auth-service",
  "timestamp": "2025-11-05T10:30:00.000Z",
  "database": "connected",
  "user_count": 1
}
```

### View Logs

```bash
docker logs rag-auth-service --tail 50
```

### Full System Reset

```bash
# Stop everything
docker compose down

# Remove auth database
docker volume rm rag_lab_auth-data

# Start fresh
docker compose up -d

# Register first user (becomes admin)
```

---

**Summary:**
- ❌ No default credentials
- ✅ First user = admin
- 🔐 JWT-based authentication
- 🛡️ bcrypt password hashing
- 📊 Role-based rate limiting
- 🎓 Production-ready patterns

**Get Started:** Register at http://localhost:3000/register


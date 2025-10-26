# Authentication Setup Guide

This guide explains how to set up and use the authentication system in IT Budget Manager.

## Overview

The system now includes JWT-based authentication with role-based access control (RBAC). Three roles are supported:

- **ADMIN** - Full access to all features
- **ACCOUNTANT** - Access to budgeting, expenses, and reference data management
- **REQUESTER** - Basic access to view expenses and dashboards

## Backend Setup

### 1. Install New Dependencies

The following dependencies have been added to `backend/requirements.txt`:

```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

Install them in your Docker container or local environment:

```bash
cd backend
pip install -r requirements.txt
```

### 2. Apply Database Migration

Apply the migration to create the `users` table:

```bash
cd backend
alembic upgrade head
```

This will:
- Create the `users` table
- Add `UserRoleEnum` (ADMIN, ACCOUNTANT, REQUESTER)
- Update `dashboard_configs` to link to users via foreign key

### 3. Create Default Admin User

Run the provided script to create a default admin account:

```bash
cd backend
python create_admin.py
```

**Default credentials:**
- Username: `admin`
- Password: `admin123`
- Email: `admin@example.com`

**IMPORTANT:** Change the password after first login!

## Frontend Setup

No additional dependencies are required. The frontend authentication is implemented using:
- React Context API for state management
- localStorage for token persistence
- Protected routes with role-based access control

## API Endpoints

### Authentication Endpoints

All authentication endpoints are under `/api/v1/auth`:

#### Register a New User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "department": "IT",
  "position": "Developer",
  "role": "REQUESTER"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "ADMIN",
    ...
  }
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <your-token>
```

#### Update Profile
```http
PUT /api/v1/auth/me
Authorization: Bearer <your-token>
Content-Type: application/json

{
  "full_name": "John Smith",
  "department": "Finance"
}
```

#### Change Password
```http
POST /api/v1/auth/me/change-password
Authorization: Bearer <your-token>
Content-Type: application/json

{
  "old_password": "current_password",
  "new_password": "new_password123"
}
```

#### List All Users (Admin only)
```http
GET /api/v1/auth/users
Authorization: Bearer <admin-token>
```

## Protected Routes

### Frontend Routes

The following frontend routes require authentication:

**All Authenticated Users:**
- `/dashboard` - Main dashboard
- `/dashboard/custom` - Custom dashboards
- `/budget` - Budget overview
- `/expenses` - Expenses list
- `/analytics` - Analytics
- `/analytics/balance` - Balance analytics
- `/payment-calendar` - Payment calendar
- `/forecast` - Forecast page

**ADMIN and ACCOUNTANT only:**
- `/budget/plan` - Budget planning
- `/categories` - Category management
- `/contractors` - Contractor management
- `/organizations` - Organization management

### Backend API Protection

All API endpoints (except `/auth/register` and `/auth/login`) require JWT authentication.

Add the token to requests:
```http
Authorization: Bearer <your-token>
```

## Role-Based Access Control

### Implementation

**Backend:**
- Authentication is handled via `get_current_user()` dependency
- Role checks are implemented in each endpoint
- Example:
```python
@router.get("/admin-only")
async def admin_endpoint(current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return {"message": "Admin access granted"}
```

**Frontend:**
- Protected routes use the `<ProtectedRoute>` component
- Role checks via `useAuth()` hook:
```typescript
const { user, hasRole } = useAuth();

if (hasRole('ADMIN')) {
  // Show admin features
}
```

## Security Configuration

### JWT Settings

JWT configuration is in `backend/app/core/config.py`:

```python
SECRET_KEY: str = "your-secret-key-here-change-in-production"
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
```

**IMPORTANT:** Change `SECRET_KEY` in production!

Generate a secure key:
```bash
openssl rand -hex 32
```

Update in `.env` file:
```
SECRET_KEY=<your-secure-key-here>
```

### Password Requirements

Passwords must:
- Be at least 6 characters long
- Contain at least one letter
- Contain at least one digit

Passwords are hashed using bcrypt before storage.

## Testing the Authentication

### 1. Start the Backend

```bash
docker-compose up -d
```

### 2. Apply Migrations and Create Admin

```bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend python create_admin.py
```

### 3. Test Login via API

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 4. Access the Frontend

Navigate to `http://localhost:5173/login`

Login with:
- Username: `admin`
- Password: `admin123`

## Troubleshooting

### Issue: "Could not validate credentials"
- Check that the token is included in the Authorization header
- Verify token hasn't expired (default: 7 days)
- Ensure SECRET_KEY matches between token creation and validation

### Issue: "User not found" after login
- Ensure migrations have been applied
- Check that admin user was created successfully
- Verify database connection

### Issue: "403 Forbidden" on protected routes
- Check user role in database
- Verify role requirements for the endpoint
- Ensure user account is active (`is_active = true`)

## Next Steps

After setting up authentication, you may want to:

1. **Change the default admin password**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/me/change-password \
     -H "Authorization: Bearer <admin-token>" \
     -H "Content-Type: application/json" \
     -d '{"old_password":"admin123","new_password":"<new-secure-password>"}'
   ```

2. **Create additional users** with appropriate roles

3. **Update SECRET_KEY** in production environment

4. **Enable HTTPS** for production deployment

5. **Implement email verification** (currently disabled)

6. **Add password reset functionality** (planned)

7. **Implement audit logging** for security events

## File Structure

### Backend
```
backend/
├── app/
│   ├── api/v1/
│   │   └── auth.py                  # Authentication endpoints
│   ├── db/
│   │   └── models.py                # User model and UserRoleEnum
│   ├── schemas/
│   │   └── user.py                  # Pydantic schemas for users
│   ├── utils/
│   │   └── auth.py                  # JWT and password utilities
│   └── core/
│       └── config.py                # JWT settings
├── alembic/versions/
│   └── 2025_10_25_0000-c3d4e5f6a7b8_add_users_table.py
├── create_admin.py                  # Script to create admin user
└── requirements.txt                 # Updated dependencies
```

### Frontend
```
frontend/src/
├── contexts/
│   └── AuthContext.tsx              # Authentication state management
├── components/
│   └── ProtectedRoute.tsx           # Route protection component
├── pages/
│   ├── LoginPage.tsx                # Login form
│   ├── RegisterPage.tsx             # Registration form
│   └── UnauthorizedPage.tsx         # 403 error page
└── App.tsx                          # Updated with auth routes
```

## Support

For issues or questions, please refer to:
- API Documentation: http://localhost:8000/docs
- Project README: [README.md](./README.md)
- Roadmap: [ROADMAP.md](./ROADMAP.md)

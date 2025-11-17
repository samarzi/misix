# Authentication System Documentation

## Overview

MISIX uses JWT (JSON Web Token) based authentication for secure API access. This document describes how to use the authentication system.

## Quick Start

### 1. Register a New User

```bash
curl -X POST http://localhost:8000/api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "telegram_id": null,
  "email_verified": false,
  "created_at": "2025-01-17T10:30:00Z",
  "updated_at": "2025-01-17T10:30:00Z"
}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "email_verified": false,
    "created_at": "2025-01-17T10:30:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

### 3. Access Protected Endpoints

Include the access token in the Authorization header:

```bash
curl -X GET http://localhost:8000/api/v2/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. Refresh Access Token

When the access token expires (after 15 minutes), use the refresh token:

```bash
curl -X POST http://localhost:8000/api/v2/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

## Password Requirements

Passwords must meet the following criteria:
- Minimum 8 characters
- Maximum 100 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*(),.?":{}|<>)

**Valid Examples:**
- `SecurePass123!`
- `MyP@ssw0rd`
- `Str0ng!Pass`

**Invalid Examples:**
- `password` (no uppercase, no digit, no special char)
- `PASSWORD123` (no lowercase, no special char)
- `Pass123` (too short, no special char)

## Token Lifecycle

### Access Token
- **Lifetime:** 15 minutes
- **Purpose:** Authenticate API requests
- **Storage:** Memory or secure storage (not localStorage)
- **Usage:** Include in Authorization header for every API call

### Refresh Token
- **Lifetime:** 7 days
- **Purpose:** Obtain new access tokens
- **Storage:** Secure HTTP-only cookie or secure storage
- **Usage:** Exchange for new access token when it expires

## API Endpoints

### POST /api/v2/auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "telegram_id": 123456789  // optional
}
```

**Status Codes:**
- `201`: User created successfully
- `409`: Email already registered
- `422`: Validation error (invalid email, weak password, etc.)

### POST /api/v2/auth/login
Authenticate user and receive tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Status Codes:**
- `200`: Login successful
- `401`: Invalid credentials

### POST /api/v2/auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Status Codes:**
- `200`: Token refreshed successfully
- `401`: Invalid or expired refresh token

### GET /api/v2/auth/me
Get current user's profile (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Status Codes:**
- `200`: Profile retrieved successfully
- `401`: Not authenticated or invalid token
- `404`: User not found

### POST /api/v2/auth/change-password
Change user's password (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

**Status Codes:**
- `200`: Password changed successfully
- `401`: Current password incorrect or not authenticated
- `422`: New password doesn't meet requirements

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message",
  "details": {
    // Additional error details (optional)
  }
}
```

**Common Errors:**

### 401 Unauthorized
```json
{
  "error": "Invalid or expired token"
}
```

### 409 Conflict
```json
{
  "error": "Email already registered",
  "details": {
    "email": "user@example.com"
  }
}
```

### 422 Validation Error
```json
{
  "error": "Validation failed",
  "details": {
    "errors": {
      "password": ["Password must contain at least one uppercase letter"]
    }
  }
}
```

## Security Best Practices

### For Frontend Developers

1. **Store Tokens Securely**
   - Never store tokens in localStorage (vulnerable to XSS)
   - Use memory storage or secure HTTP-only cookies
   - Consider using a secure token management library

2. **Handle Token Expiration**
   - Implement automatic token refresh before expiration
   - Handle 401 errors gracefully
   - Redirect to login when refresh token expires

3. **Protect Sensitive Operations**
   - Re-authenticate for sensitive actions (password change, etc.)
   - Implement CSRF protection
   - Use HTTPS in production

4. **Logout Properly**
   - Clear all tokens from storage
   - Invalidate refresh token on server (if implemented)
   - Redirect to login page

### For Backend Developers

1. **Protect Endpoints**
   ```python
   from app.api.deps import get_current_user_id, get_current_user
   
   @router.get("/protected")
   async def protected_route(
       user_id: Annotated[str, Depends(get_current_user_id)]
   ):
       return {"user_id": user_id}
   ```

2. **Optional Authentication**
   ```python
   from app.api.deps import get_optional_user_id
   
   @router.get("/public")
   async def public_route(
       user_id: Annotated[Optional[str], Depends(get_optional_user_id)]
   ):
       if user_id:
           return {"message": f"Hello user {user_id}"}
       return {"message": "Hello anonymous"}
   ```

3. **Require Email Verification**
   ```python
   from app.api.deps import require_verified_email
   
   @router.post("/sensitive")
   async def sensitive_action(
       user: Annotated[dict, Depends(require_verified_email)]
   ):
       return {"message": "Action performed"}
   ```

## Testing Authentication

### Using cURL

```bash
# 1. Register
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test User"}')

# 2. Login
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}')

# 3. Extract access token
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.tokens.access_token')

# 4. Access protected endpoint
curl -X GET http://localhost:8000/api/v2/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v2/auth"

# Register
response = requests.post(f"{BASE_URL}/register", json={
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User"
})
print(f"Register: {response.status_code}")

# Login
response = requests.post(f"{BASE_URL}/login", json={
    "email": "test@example.com",
    "password": "Test123!"
})
tokens = response.json()["tokens"]
access_token = tokens["access_token"]

# Access protected endpoint
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/me", headers=headers)
print(f"Profile: {response.json()}")
```

## Migration from Legacy Auth

The new authentication system is available at `/api/v2/auth/*` endpoints.
Legacy endpoints at `/api/auth/*` will be deprecated in a future release.

**Migration Steps:**

1. Update frontend to use new endpoints (`/api/v2/auth/*`)
2. Update token storage to use secure methods
3. Implement automatic token refresh
4. Test all authentication flows
5. Remove legacy auth code

## Troubleshooting

### "Invalid or expired token"
- Token has expired (access tokens expire after 15 minutes)
- Token is malformed or corrupted
- JWT secret key changed on server
- **Solution:** Refresh the access token or login again

### "Email already registered"
- User with this email already exists
- **Solution:** Use a different email or login with existing account

### "Password must contain..."
- Password doesn't meet security requirements
- **Solution:** Follow password requirements listed above

### "Not authenticated"
- No Authorization header provided
- Authorization header format is incorrect
- **Solution:** Include `Authorization: Bearer <token>` header

## Configuration

Authentication settings are configured via environment variables:

```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-min-32-chars  # Required
JWT_ALGORITHM=HS256                          # Optional (default: HS256)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15           # Optional (default: 15)
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7              # Optional (default: 7)
```

**Generate a secure JWT secret:**
```bash
openssl rand -hex 32
```

## Support

For issues or questions:
1. Check this documentation
2. Review API documentation at `/docs`
3. Check application logs
4. Contact the development team

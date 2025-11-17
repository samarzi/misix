# MISIX Migration Guide

## 🎯 Purpose

This guide helps you migrate from the old MISIX codebase to the new refactored version with improved security and architecture.

---

## 📋 Pre-Migration Checklist

Before starting migration:

- [ ] Backup your database
- [ ] Document current API endpoints in use
- [ ] List all environment variables
- [ ] Export user data if needed
- [ ] Test current functionality
- [ ] Review this entire guide

---

## 🔄 Migration Steps

### Step 1: Update Environment Variables

**Old `.env` format:**
```env
YANDEX_GPT_API_KEY=test_key  # ❌ Had default values
JWT_SECRET_KEY=short          # ❌ Too short
```

**New `.env` format:**
```env
# Required (no defaults)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_ANON_KEY=your-anon-key
JWT_SECRET_KEY=your-32-char-minimum-secret
YANDEX_GPT_API_KEY=your-api-key
YANDEX_FOLDER_ID=your-folder-id

# Optional (has safe defaults)
ENVIRONMENT=development
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
RATE_LIMIT_PER_MINUTE=60
```

**Action:**
1. Copy `backend/.env.example` to `backend/.env`
2. Fill in all required values
3. Generate new JWT secret: `openssl rand -hex 32`
4. Remove any old environment variables

### Step 2: Update Dependencies

**Install new dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

**New dependencies added:**
- `redis==5.0.1` (optional, for caching)
- `pytest==7.4.3` (for testing)
- `pytest-asyncio==0.21.1`
- `pytest-cov==4.1.0`

### Step 3: Database Schema Updates

**No breaking changes to existing tables!**

The new system uses the same database schema. However, ensure these tables exist:

```sql
-- Users table (should already exist)
-- No changes needed

-- New: assistant_conversation_summaries (if not exists)
CREATE TABLE IF NOT EXISTS assistant_conversation_summaries (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telegram_id bigint,
    summary text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
```

**Action:**
1. Run database migrations (if any)
2. Verify all tables exist
3. Check indexes are in place

### Step 4: Update API Endpoints

**Authentication endpoints have moved:**

| Old Endpoint | New Endpoint | Status |
|--------------|--------------|--------|
| `/api/auth/login` | `/api/v2/auth/login` | ✅ Use new |
| `/api/auth/register` | `/api/v2/auth/register` | ✅ Use new |
| N/A | `/api/v2/auth/refresh` | ✅ New |
| N/A | `/api/v2/auth/me` | ✅ New |
| N/A | `/api/v2/auth/change-password` | ✅ New |

**Other endpoints remain the same** (for now):
- `/api/tasks/*` - No changes
- `/api/notes/*` - No changes
- `/api/finances/*` - No changes
- `/api/dashboard/*` - No changes

**Action:**
1. Update frontend to use `/api/v2/auth/*` endpoints
2. Update any scripts or integrations
3. Test all endpoints

### Step 5: Update Authentication Flow

**Old flow (insecure):**
```typescript
// ❌ No real authentication
const response = await fetch('/api/chat', {
  body: JSON.stringify({ user_id: 'any-id' })
});
```

**New flow (secure):**
```typescript
// ✅ Proper JWT authentication
// 1. Login
const loginResponse = await fetch('/api/v2/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
const { tokens } = await loginResponse.json();

// 2. Store tokens securely
localStorage.setItem('access_token', tokens.access_token);
localStorage.setItem('refresh_token', tokens.refresh_token);

// 3. Use token in requests
const response = await fetch('/api/v2/auth/me', {
  headers: {
    'Authorization': `Bearer ${tokens.access_token}`
  }
});

// 4. Refresh when expired
if (response.status === 401) {
  const refreshResponse = await fetch('/api/v2/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: tokens.refresh_token })
  });
  // Update tokens and retry
}
```

**Action:**
1. Implement token storage (secure, not localStorage in production)
2. Add Authorization header to all API calls
3. Implement token refresh logic
4. Handle 401 errors properly

### Step 6: Update Frontend Validation

**Old validation (none):**
```typescript
// ❌ No validation
const handleSubmit = (data) => {
  api.post('/endpoint', data);
};
```

**New validation (Zod):**
```typescript
// ✅ Zod validation
import { createTaskSchema } from '@/lib/validation/schemas';

const handleSubmit = (data) => {
  const result = createTaskSchema.safeParse(data);
  if (!result.success) {
    // Show validation errors
    setErrors(result.error.flatten());
    return;
  }
  api.post('/endpoint', result.data);
};
```

**Action:**
1. Import Zod schemas from `frontend/src/lib/validation/schemas.ts`
2. Add validation to all forms
3. Display validation errors to users

### Step 7: Handle Rate Limiting

**New rate limits:**
- General endpoints: 60 requests/minute
- Auth endpoints: 5 requests/minute

**Handle 429 responses:**
```typescript
const response = await fetch('/api/endpoint');

if (response.status === 429) {
  const data = await response.json();
  const retryAfter = data.details.retry_after;
  
  // Wait and retry
  await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
  // Retry request
}
```

**Action:**
1. Implement retry logic for 429 errors
2. Show user-friendly messages
3. Consider request batching

### Step 8: Update Error Handling

**Old errors (inconsistent):**
```json
{
  "error": "Something went wrong"
}
```

**New errors (structured):**
```json
{
  "error": "Validation failed",
  "details": {
    "errors": {
      "email": ["Invalid email format"],
      "password": ["Password too weak"]
    }
  },
  "request_id": "abc-123-def",
  "timestamp": "2025-01-17T10:30:00Z"
}
```

**Action:**
1. Update error parsing logic
2. Display field-level errors
3. Log request_id for debugging

### Step 9: Test Migration

**Run comprehensive tests:**

```bash
# Backend tests
cd backend
pytest

# Manual API tests
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Test authentication flow
./scripts/test_auth.sh  # Create this script

# Test existing functionality
# - Create task
# - Create note
# - Create transaction
# - etc.
```

**Action:**
1. Run all automated tests
2. Manually test critical flows
3. Verify data integrity
4. Check logs for errors

### Step 10: Deploy

**Deployment checklist:**

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Frontend updated
- [ ] Rate limits configured
- [ ] Monitoring set up
- [ ] Backup created
- [ ] Rollback plan ready

**Deployment steps:**
1. Deploy to staging first
2. Run smoke tests
3. Monitor for 24 hours
4. Deploy to production
5. Monitor closely

---

## 🔧 Configuration Changes

### Required Environment Variables

**Must be set (no defaults):**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_ANON_KEY`
- `JWT_SECRET_KEY` (min 32 chars)
- `YANDEX_GPT_API_KEY`
- `YANDEX_FOLDER_ID`

### Optional Environment Variables

**Has safe defaults:**
- `ENVIRONMENT` (default: development)
- `DEBUG` (default: false)
- `LOG_LEVEL` (default: INFO)
- `LOG_FORMAT` (default: json)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default: 15)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` (default: 7)
- `RATE_LIMIT_PER_MINUTE` (default: 60)
- `RATE_LIMIT_AUTH_PER_MINUTE` (default: 5)
- `MAX_UPLOAD_SIZE_MB` (default: 10)
- `REDIS_URL` (optional, for caching)

---

## 🚨 Breaking Changes

### 1. Authentication Required

**Before:** No authentication  
**After:** JWT required for all protected endpoints

**Impact:** All API clients must implement authentication

**Migration:** Add login flow and token management

### 2. Password Requirements

**Before:** Any password accepted  
**After:** Strong password required (8+ chars, mixed case, digit, special char)

**Impact:** Existing weak passwords won't work for new registrations

**Migration:** Users must create new passwords meeting requirements

### 3. API Response Format

**Before:** Inconsistent error responses  
**After:** Structured error responses with request_id

**Impact:** Error parsing logic needs update

**Migration:** Update error handling code

### 4. Rate Limiting

**Before:** No rate limiting  
**After:** 60 req/min general, 5 req/min auth

**Impact:** High-frequency clients may hit limits

**Migration:** Implement retry logic and request batching

### 5. CORS Configuration

**Before:** Wildcard allowed  
**After:** Whitelist only

**Impact:** Requests from unlisted origins will fail

**Migration:** Add your frontend origin to `FRONTEND_ALLOWED_ORIGINS`

---

## 🐛 Troubleshooting

### Issue: "Configuration Error" on startup

**Cause:** Missing required environment variables

**Solution:**
1. Check `.env` file exists
2. Verify all required variables are set
3. Check for typos in variable names
4. Ensure values are not empty

### Issue: "Invalid or expired token"

**Cause:** Token expired or invalid

**Solution:**
1. Check token expiration (15 minutes for access tokens)
2. Implement token refresh
3. Verify JWT_SECRET_KEY hasn't changed
4. Check token format in Authorization header

### Issue: "Rate limit exceeded"

**Cause:** Too many requests

**Solution:**
1. Wait for retry-after period
2. Implement request batching
3. Add caching on client side
4. Increase rate limits if needed (in config)

### Issue: "CORS error"

**Cause:** Origin not in whitelist

**Solution:**
1. Add origin to `FRONTEND_ALLOWED_ORIGINS`
2. Restart backend
3. Clear browser cache
4. Check origin format (include protocol and port)

### Issue: Tests failing

**Cause:** Various reasons

**Solution:**
1. Check database connection
2. Verify test environment variables
3. Run `pytest -v` for detailed output
4. Check test fixtures are set up correctly

---

## 📊 Rollback Plan

If migration fails:

### 1. Immediate Rollback

```bash
# Stop new backend
pm2 stop misix-backend

# Start old backend
pm2 start old-misix-backend

# Revert frontend
git checkout old-version
npm run build
```

### 2. Database Rollback

```sql
-- No schema changes, so no rollback needed
-- But if you added new data, you may want to clean it up
```

### 3. Configuration Rollback

```bash
# Restore old .env
cp .env.backup .env

# Restart services
pm2 restart all
```

### 4. Verify Rollback

- [ ] Old endpoints working
- [ ] Users can access system
- [ ] Data intact
- [ ] No errors in logs

---

## ✅ Post-Migration Checklist

After successful migration:

- [ ] All tests passing
- [ ] Authentication working
- [ ] Rate limiting active
- [ ] Logging configured
- [ ] Monitoring set up
- [ ] Documentation updated
- [ ] Team trained
- [ ] Old code archived
- [ ] Backup verified
- [ ] Performance acceptable

---

## 📞 Support

For migration issues:

1. Check this guide
2. Review logs (`LOG_LEVEL=DEBUG`)
3. Check API docs at `/docs`
4. Review `REFACTORING_SUMMARY.md`
5. Contact development team

---

## 🎯 Success Criteria

Migration is successful when:

✅ All users can authenticate  
✅ All existing features work  
✅ No data loss  
✅ Performance acceptable  
✅ Security improved  
✅ Monitoring active  
✅ Team confident  

---

**Good luck with your migration!** 🚀

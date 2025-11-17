# Deployment Guide for Render

## Prerequisites

1. ✅ Database schema created in Supabase (run `backend/migrations/000_drop_and_recreate.sql`)
2. ✅ Supabase project created and accessible
3. ✅ Yandex Cloud account with GPT API access
4. ✅ Render account
5. ✅ Python 3.11 runtime configured (see Python Version section below)

## Python Version Requirement

**⚠️ Critical:** This application requires Python 3.11 for production deployment.

**Why Python 3.11?**
- Python 3.13 has compatibility issues with `python-telegram-bot` library (weak reference errors)
- Python 3.11 is stable, well-tested, and fully supported by all dependencies
- Python 3.12 may work but is not officially tested

**How to configure:**

The repository includes a `render.yaml` file that automatically sets Python 3.11. If you're configuring manually in Render dashboard:

1. Go to your service → Settings → Environment
2. Add environment variable:
   ```
   PYTHON_VERSION=3.11
   ```
3. Save and redeploy

## Step-by-Step Deployment

### 1. Prepare Supabase Database

Go to your Supabase project → SQL Editor and run:
```sql
-- Copy and paste the contents of backend/migrations/000_drop_and_recreate.sql
```

### 2. Gather Required Credentials

#### From Supabase (Project Settings → API):
- `SUPABASE_URL` - Your project URL (e.g., `https://xxxxx.supabase.co`)
- `SUPABASE_ANON_KEY` - Public anon key
- `SUPABASE_SERVICE_KEY` - Service role key (keep secret!)

#### Generate JWT Secret:
```bash
openssl rand -hex 32
```
Copy the output for `JWT_SECRET_KEY`

#### From Yandex Cloud:
- `YANDEX_GPT_API_KEY` - Your API key
- `YANDEX_FOLDER_ID` - Your folder ID

### 3. Configure Render Service

In Render Dashboard → Your Service → Environment:

#### Required Variables (Must Set All):

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...your-service-key
SUPABASE_ANON_KEY=eyJhbGc...your-anon-key
JWT_SECRET_KEY=your-generated-32-char-secret
YANDEX_GPT_API_KEY=your-yandex-api-key
YANDEX_FOLDER_ID=your-folder-id
```

#### Frontend Origins (Important!):

```bash
FRONTEND_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**⚠️ Important:** 
- Use comma-separated values WITHOUT spaces
- Include your actual frontend domain(s)
- For testing, you can use: `https://yourdomain.com,http://localhost:5173`

#### Optional Variables (Recommended for Production):

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json
RATE_LIMIT_ENABLED=true
```

## Generating Secrets

Generate secure secrets using:

```bash
openssl rand -hex 32
```

### 4. Deploy

After setting all environment variables:
1. Click "Manual Deploy" → "Deploy latest commit"
2. Or push to your connected Git branch
3. Watch the logs for any errors

## Common Deployment Issues

### Issue: "Exited with status 1" / "No open ports detected"

**Cause:** Missing or invalid environment variables

**Solution:** 
1. Check Render logs for the specific error message
2. Verify ALL required variables are set in Environment tab
3. Make sure no variables have trailing spaces or quotes
4. Redeploy after fixing

### Issue: "error parsing value for field frontend_allowed_origins"

**Solution:** Make sure `FRONTEND_ALLOWED_ORIGINS` is set as a string with comma-separated URLs:
- ✅ Correct: `https://app.com,https://www.app.com`
- ❌ Wrong: `["https://app.com", "https://www.app.com"]` (don't use JSON array format)
- ❌ Wrong: `https://app.com, https://www.app.com` (no spaces after comma)

### Issue: "Configuration Error: JWT secret key must be at least 32 characters"

**Solution:** Generate a proper secret key:
```bash
openssl rand -hex 32
```
Copy the entire output (should be 64 characters)

### Issue: "relation does not exist" database errors

**Solution:** 
1. Go to Supabase SQL Editor
2. Run `backend/migrations/000_drop_and_recreate.sql`
3. This creates all required tables with correct schema

### Issue: Missing required environment variables

**Solution:** 
1. Go to Render Dashboard → Your Service → Environment
2. Verify ALL 6 required variables are set:
   - SUPABASE_URL
   - SUPABASE_SERVICE_KEY
   - SUPABASE_ANON_KEY
   - JWT_SECRET_KEY
   - YANDEX_GPT_API_KEY
   - YANDEX_FOLDER_ID
3. Click "Save Changes"
4. Redeploy

## Health Check

After deployment, verify your service is running:

```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-17T10:30:00Z"
}
```

## Startup Validation

The application now includes comprehensive startup validation that checks:

1. **Python Version**: Verifies Python 3.11+ is being used
2. **Environment Variables**: Validates all required configuration is present
3. **Database Connection**: Tests connectivity to Supabase
4. **Database Schema**: Verifies all required tables exist
5. **Write Operations**: Tests that data can be persisted

### Expected Startup Log Output

```
🚀 Starting MISIX application...
📦 Python version: 3.11.x
🖥️  Platform: Linux-x.x.x
🌍 Environment: production
📚 FastAPI: 0.115.0
📚 python-telegram-bot: 21.0.1
📚 supabase: 2.4.4
🔍 Running startup validation checks...
✅ Python Version: Python 3.11.x - compatible
✅ Environment Variables: All 6 required and 3 optional variables present
✅ Phase 1 complete: Configuration validation passed
🔍 Testing database connection...
✅ Database connection successful
📊 Database: db.xxx.supabase.co:443/postgres
🔍 Verifying database schema...
✅ Schema validation passed - all 8 tables exist
🔍 Testing database write operations...
✅ Database write operation test passed
✅ Phase 2 complete: Database validation passed
✅ Telegram bot initialized
✅ Telegram bot started
✅ Scheduler started successfully
✅ Phase 3 complete: Telegram bot initialized
============================================================
✅ MISIX application started successfully
============================================================
```

### Troubleshooting Startup Failures

#### Critical Validation Failures

If you see:
```
❌ Critical validation failures detected. Cannot start application.
```

Check the logs for specific failures:

**Missing Environment Variables:**
```
❌ Environment Variables: Missing required environment variables: JWT_SECRET_KEY, YANDEX_GPT_API_KEY
```
→ Add the missing variables in Render dashboard → Environment

**Python Version Issue:**
```
❌ Python Version: Python 3.13.x detected. Python 3.13+ has known compatibility issues
```
→ Set `PYTHON_VERSION=3.11` in environment variables or use render.yaml

**Database Connection Failed:**
```
❌ Database connection failed. Application cannot start.
```
→ Verify SUPABASE_URL and SUPABASE_SERVICE_KEY are correct
→ Check Supabase project is active and accessible

**Missing Database Tables:**
```
❌ Database schema incomplete. Missing tables: tasks, notes, mood_entries
```
→ Run database migrations (see Database Setup section above)

#### Warning Messages

Warnings allow the application to start but with reduced functionality:

**Optional Environment Variables:**
```
⚠️  Environment Variables: Missing optional environment variables: TELEGRAM_BOT_TOKEN
```
→ Bot functionality will be disabled, but web API will work

**Python 3.13 Warning:**
```
⚠️  Python Version: Python 3.13.x detected. Recommend Python 3.11.
```
→ Application may work but could encounter issues. Recommend downgrading to 3.11.

## Logs

Monitor your deployment logs in Render dashboard to catch any startup errors.

### Key Log Indicators

- ✅ Green checkmarks = successful operations
- ❌ Red X = critical failures (app won't start)
- ⚠️  Warning triangle = non-critical issues (app starts with degraded functionality)
- 🔍 Magnifying glass = validation/testing in progress
- 📊 Chart = informational data

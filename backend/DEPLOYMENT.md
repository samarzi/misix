# Deployment Guide for Render

## Prerequisites

1. ✅ Database schema created in Supabase (run `backend/migrations/000_drop_and_recreate.sql`)
2. ✅ Supabase project created and accessible
3. ✅ Yandex Cloud account with GPT API access
4. ✅ Render account

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

## Logs

Monitor your deployment logs in Render dashboard to catch any startup errors.

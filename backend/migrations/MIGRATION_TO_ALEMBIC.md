# Migration from SQL Files to Alembic

## Overview

The MISIX project has migrated from manual SQL migration files to Alembic for better version control and management of database schema changes.

## What Changed

### Before (Old System)
- Multiple SQL files with inconsistent naming
- No tracking of which migrations were applied
- Manual execution required
- Difficult to rollback changes
- Files: `000_drop_and_recreate.sql`, `001_complete_schema.sql`, etc.

### After (New System)
- Alembic-managed migrations with version tracking
- Automatic migration history
- Easy upgrade/downgrade commands
- Timestamped migration files
- Location: `backend/alembic/versions/`

## Old Migration Files

All old SQL migration files have been archived in `backend/migrations/archive/` for reference.

**DO NOT USE THESE FILES DIRECTLY** - they are kept for historical reference only.

## Using the New System

### For Developers

1. **Create a new migration:**
```bash
cd backend
alembic revision -m "add new column to users table"
```

2. **Edit the generated file** in `alembic/versions/`

3. **Apply the migration:**
```bash
alembic upgrade head
```

### For Deployment

Migrations are applied automatically during deployment via the startup script.

If you need to apply manually:
```bash
cd backend
export DATABASE_URL="your_postgresql_url"
alembic upgrade head
```

## Initial Schema

The complete current schema is captured in the first Alembic migration.

If you're setting up a new database:
```bash
cd backend
alembic upgrade head
```

This will create all tables, indexes, and constraints.

## Rollback

If you need to rollback a migration:
```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all
alembic downgrade base
```

## Migration History

View applied migrations:
```bash
alembic history
alembic current
```

## Troubleshooting

### "alembic_version table doesn't exist"

This means Alembic hasn't been initialized. Run:
```bash
alembic upgrade head
```

### "Can't locate revision"

Make sure you're in the backend directory and DATABASE_URL is set.

### "Multiple heads"

Merge the branches:
```bash
alembic merge heads -m "merge branches"
```

## Questions?

See `backend/alembic/README.md` for more details.

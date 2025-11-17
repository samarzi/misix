# Alembic Database Migrations

This directory contains database migration files managed by Alembic.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set DATABASE_URL environment variable:
```bash
export DATABASE_URL="postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"
```

You can find your database URL in Supabase Dashboard → Project Settings → Database → Connection string.

## Commands

### Create a new migration

```bash
cd backend
alembic revision -m "description of changes"
```

### Apply migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1
```

### View migration history

```bash
alembic history
alembic current
```

## Migration from Old System

Old SQL migration files have been moved to `migrations/archive/`. 

The initial Alembic migration (`001_initial_schema.py`) contains the complete current schema.

## Best Practices

1. **Always test migrations locally first**
2. **Create backups before running migrations in production**
3. **Write both upgrade() and downgrade() functions**
4. **Keep migrations small and focused**
5. **Never edit applied migrations** - create a new one instead
6. **Review generated migrations** - autogenerate isn't perfect

## Troubleshooting

### "DATABASE_URL not set"

Set the environment variable:
```bash
export DATABASE_URL="your_postgresql_url"
```

### "Can't locate revision"

Check that you're in the backend directory:
```bash
cd backend
alembic current
```

### "Multiple heads detected"

Merge the branches:
```bash
alembic merge heads -m "merge branches"
```

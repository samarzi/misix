# Database Migrations

## How to Apply Migrations

### Option 1: Using Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor** in the left sidebar
3. Click **New Query**
4. Copy the contents of `001_complete_schema.sql`
5. Paste into the SQL editor
6. Click **Run** (or press Cmd/Ctrl + Enter)

### Option 2: Using Supabase CLI

```bash
# Install Supabase CLI if you haven't
npm install -g supabase

# Login to Supabase
supabase login

# Link your project
supabase link --project-ref your-project-ref

# Run the migration
supabase db push
```

### Option 3: Using psql

```bash
# Connect to your Supabase database
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"

# Run the migration
\i backend/migrations/001_complete_schema.sql
```

## Migration Files

### For New Databases (Fresh Install)

- `001_complete_schema.sql` - Complete database schema with all tables
  - Creates all tables with proper relationships
  - Safe to run multiple times (uses `IF NOT EXISTS`)
  - Includes all Telegram integration columns

### For Existing Databases (Update)

- `002_add_missing_columns.sql` - Adds missing columns to existing tables
  - Safe to run multiple times
  - Checks if columns exist before adding them
  - Adds all foreign key constraints
  - **Run this if you get "column does not exist" errors**

## Quick Start

### Option A: If you keep getting "column does not exist" errors (RECOMMENDED):

**⚠️ WARNING: This will delete all existing data!**

1. Backup your data if needed
2. Run `000_drop_and_recreate.sql`
3. This drops all tables and recreates them with the correct schema
4. Your database will be clean and ready to use

### Option B: If you have an existing database with some data:

1. Run `002_add_missing_columns.sql`
2. This will add any missing columns to your existing tables
3. May require multiple runs if many columns are missing

### Option C: If you're starting completely fresh:

1. Run `001_complete_schema.sql`
2. This creates everything from scratch using IF NOT EXISTS

## Verifying Migration

After running the migration, verify that all tables were created:

```sql
-- List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Expected tables:
-- - users
-- - note_folders
-- - notes
-- - note_tags
-- - tags
-- - projects
-- - tasks
-- - task_tags
-- - task_subitems
-- - assistant_sessions
-- - assistant_messages
-- - attachments
-- - sleep_sessions
```

## Troubleshooting

### Error: "relation already exists"

This is safe to ignore. The migration uses `IF NOT EXISTS` so it won't fail if tables already exist.

### Error: "foreign key constraint"

Make sure you're running the complete migration file, not partial scripts. The order of table creation matters.

### Error: "permission denied"

Make sure you're using the service role key or have proper database permissions.

## Rolling Back

If you need to drop all tables and start fresh:

```sql
-- WARNING: This will delete ALL data!
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

-- Then run the migration again
```

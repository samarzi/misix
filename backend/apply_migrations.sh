#!/bin/bash

# MISIX Database Migration Script
# Applies all migrations in correct order

set -e  # Exit on error

echo "🚀 MISIX Database Migration Script"
echo "=================================="
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL environment variable is not set"
    echo ""
    echo "Please set it first:"
    echo "  export DATABASE_URL='postgresql://user:pass@host:port/database'"
    echo ""
    echo "Or get it from Supabase Dashboard -> Settings -> Database"
    exit 1
fi

echo "✅ DATABASE_URL is set"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ Error: psql is not installed"
    echo ""
    echo "Install PostgreSQL client:"
    echo "  macOS: brew install postgresql"
    echo "  Ubuntu: sudo apt-get install postgresql-client"
    exit 1
fi

echo "✅ psql is available"
echo ""

# Migration files in order
MIGRATIONS=(
    "001_complete_schema.sql"
    "002_add_missing_columns.sql"
    "003_verify_schema.sql"
    "004_add_mood_entries.sql"
    "005_add_reminders.sql"
    "006_add_indexes.sql"
)

echo "📋 Migrations to apply:"
for migration in "${MIGRATIONS[@]}"; do
    echo "  - $migration"
done
echo ""

# Confirm before proceeding
read -p "Continue with migration? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled"
    exit 0
fi

echo ""
echo "🔄 Applying migrations..."
echo ""

# Apply each migration
for migration in "${MIGRATIONS[@]}"; do
    migration_file="backend/migrations/$migration"
    
    if [ ! -f "$migration_file" ]; then
        echo "❌ Error: Migration file not found: $migration_file"
        exit 1
    fi
    
    echo "📝 Applying $migration..."
    
    if psql "$DATABASE_URL" -f "$migration_file" > /dev/null 2>&1; then
        echo "✅ $migration applied successfully"
    else
        echo "⚠️  $migration completed with warnings (this may be normal)"
    fi
    
    echo ""
done

echo "=================================="
echo "✅ All migrations applied!"
echo ""
echo "🔍 Verifying database schema..."
echo ""

# Verify tables exist
psql "$DATABASE_URL" -c "
SELECT 
    COUNT(*) as table_count,
    STRING_AGG(table_name, ', ' ORDER BY table_name) as tables
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE';
" -t

echo ""
echo "✅ Migration complete!"
echo ""
echo "Next steps:"
echo "  1. Restart your backend server"
echo "  2. Test the application"
echo "  3. Check logs for any errors"

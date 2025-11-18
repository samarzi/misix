#!/bin/bash
# Script to connect to Supabase database via psql

# Supabase connection details
PROJECT_REF="dcxdnrealygulikpuicm"
DB_PASSWORD="your_db_password_here"  # Нужно получить из Supabase Dashboard

# Connection string format:
# postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

DATABASE_URL="postgresql://postgres:${DB_PASSWORD}@db.${PROJECT_REF}.supabase.co:5432/postgres"

echo "Connecting to Supabase database..."
echo "Project: ${PROJECT_REF}"
echo ""

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo "❌ psql is not installed"
    echo ""
    echo "Install PostgreSQL client:"
    echo "  macOS: brew install postgresql"
    echo "  Ubuntu: sudo apt-get install postgresql-client"
    exit 1
fi

# Connect to database
psql "${DATABASE_URL}"

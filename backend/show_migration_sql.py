#!/usr/bin/env python3
"""Show migration SQL for copy-paste into Supabase SQL Editor."""

from pathlib import Path

migration_path = Path(__file__).parent / "migrations" / "009_remove_email_auth.sql"

print("=" * 80)
print("📋 MIGRATION SQL - Copy and paste into Supabase SQL Editor")
print("=" * 80)
print()
print("Instructions:")
print("1. Go to https://app.supabase.com")
print("2. Select your project")
print("3. Click 'SQL Editor' in the left menu")
print("4. Click 'New query'")
print("5. Copy the SQL below and paste it")
print("6. Click 'Run' or press Ctrl+Enter")
print()
print("=" * 80)
print()

with open(migration_path, "r", encoding="utf-8") as f:
    print(f.read())

print()
print("=" * 80)
print("✅ After running the migration, restart your application")
print("=" * 80)

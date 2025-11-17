#!/usr/bin/env python3
"""
Apply SQL migrations to Supabase database.

This script reads SQL migration files and executes them via Supabase client.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.shared.supabase import get_supabase_client


async def apply_migration(client, migration_file: Path) -> bool:
    """Apply a single migration file.
    
    Args:
        client: Supabase client
        migration_file: Path to SQL file
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n📄 Applying migration: {migration_file.name}")
    
    try:
        # Read SQL file
        sql_content = migration_file.read_text()
        
        # Execute via Supabase RPC
        # Note: Supabase doesn't have direct SQL execution via client
        # We need to use the REST API or psycopg2
        
        print(f"⚠️  Cannot apply via Supabase client directly")
        print(f"   Please run this SQL manually in Supabase SQL Editor:")
        print(f"   https://supabase.com/dashboard/project/YOUR_PROJECT/sql")
        print(f"\n   Or use psql:")
        print(f"   psql $DATABASE_URL -f {migration_file}")
        
        return False
        
    except Exception as e:
        print(f"❌ Failed to apply {migration_file.name}: {e}")
        return False


async def main():
    """Main entry point."""
    print("="*60)
    print("🔧 MISIX Database Migration Tool")
    print("="*60)
    
    # Get Supabase client
    try:
        client = get_supabase_client()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        sys.exit(1)
    
    # Find migration files
    migrations_dir = Path(__file__).parent / "migrations"
    migration_files = [
        migrations_dir / "007_fix_missing_tables.sql",
        migrations_dir / "005_add_reminders.sql",
    ]
    
    print(f"\n📋 Found {len(migration_files)} migrations to apply")
    
    # Show instructions
    print("\n" + "="*60)
    print("📝 MANUAL MIGRATION INSTRUCTIONS")
    print("="*60)
    print("\nSupabase doesn't support direct SQL execution via Python client.")
    print("Please apply migrations manually using one of these methods:\n")
    
    print("Method 1: Supabase Dashboard")
    print("-" * 40)
    print("1. Go to: https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Go to SQL Editor")
    print("4. Copy and paste the SQL from each file:")
    
    for mig_file in migration_files:
        if mig_file.exists():
            print(f"   - {mig_file}")
    
    print("\nMethod 2: psql command line")
    print("-" * 40)
    print("If you have DATABASE_URL set:")
    
    for mig_file in migration_files:
        if mig_file.exists():
            print(f"   psql $DATABASE_URL -f {mig_file}")
    
    print("\nMethod 3: Copy SQL content")
    print("-" * 40)
    
    for mig_file in migration_files:
        if mig_file.exists():
            print(f"\n--- {mig_file.name} ---")
            content = mig_file.read_text()
            # Show first 500 chars
            preview = content[:500] + "..." if len(content) > 500 else content
            print(preview)
    
    print("\n" + "="*60)
    print("After applying migrations, run: python3 diagnose.py")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

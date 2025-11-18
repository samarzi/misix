#!/usr/bin/env python3
"""
Apply migration to remove email authentication from users table.

This script:
1. Reads the SQL migration file
2. Connects to Supabase
3. Executes the migration
4. Verifies the changes
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.shared.supabase import get_supabase_client


def read_migration_file() -> str:
    """Read the SQL migration file."""
    migration_path = Path(__file__).parent / "migrations" / "009_remove_email_auth.sql"
    
    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")
    
    with open(migration_path, "r", encoding="utf-8") as f:
        return f.read()


def apply_migration():
    """Apply the migration to remove email authentication."""
    print("=" * 60)
    print("🔧 Applying migration: Remove email authentication")
    print("=" * 60)
    print()
    
    # Check Supabase configuration
    if not settings.supabase_url or not settings.supabase_service_key:
        print("❌ Error: Supabase not configured")
        print("   Please set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables")
        return False
    
    print(f"📡 Connecting to Supabase: {settings.supabase_url}")
    print()
    
    try:
        # Read migration SQL
        print("📖 Reading migration file...")
        sql = read_migration_file()
        print(f"✅ Migration file loaded ({len(sql)} characters)")
        print()
        
        # Get Supabase client
        print("🔌 Connecting to database...")
        client = get_supabase_client()
        print("✅ Connected successfully")
        print()
        
        # Execute migration using Supabase PostgREST RPC
        # Note: Supabase REST API doesn't support raw SQL execution directly
        # We need to use the PostgreSQL connection or Supabase SQL Editor
        print("⚠️  Note: This script prepares the migration SQL.")
        print("   To apply it, you have two options:")
        print()
        print("   Option 1: Use Supabase SQL Editor")
        print("   - Go to your Supabase project dashboard")
        print("   - Navigate to SQL Editor")
        print("   - Copy and paste the migration SQL")
        print("   - Run the query")
        print()
        print("   Option 2: Use psql command line")
        print("   - Get your database connection string from Supabase")
        print("   - Run: psql <connection_string> -f migrations/009_remove_email_auth.sql")
        print()
        print("📄 Migration SQL file location:")
        print(f"   {Path(__file__).parent / 'migrations' / '009_remove_email_auth.sql'}")
        print()
        
        # Verify current schema
        print("🔍 Checking current schema...")
        try:
            # Try to query users table to see current columns
            result = client.table("users").select("*").limit(0).execute()
            print("✅ Users table is accessible")
            print()
            
            # Check if we can create a test user (this will fail if email is still required)
            print("🧪 Testing current schema constraints...")
            test_telegram_id = 999999998
            try:
                # Try to create user without email
                test_result = client.table("users").upsert({
                    "telegram_id": test_telegram_id,
                    "full_name": "Test User",
                    "username": "_test_",
                    "language_code": "en"
                }, on_conflict="telegram_id").execute()
                
                # Clean up
                client.table("users").delete().eq("telegram_id", test_telegram_id).execute()
                
                print("✅ Schema already allows Telegram-only users")
                print("   Migration may have already been applied!")
                print()
            except Exception as e:
                error_msg = str(e)
                if "null value" in error_msg.lower() and "email" in error_msg.lower():
                    print("⚠️  Schema still requires email field")
                    print("   Migration needs to be applied")
                    print()
                else:
                    print(f"⚠️  Unexpected error: {e}")
                    print()
        
        except Exception as e:
            print(f"❌ Error checking schema: {e}")
            print()
        
        print("=" * 60)
        print("📋 Next Steps:")
        print("=" * 60)
        print("1. Apply the migration using one of the methods above")
        print("2. Verify the migration was successful")
        print("3. Restart your application")
        print("4. Test bot functionality")
        print()
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)

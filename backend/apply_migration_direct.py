#!/usr/bin/env python3
"""
Apply migration directly using PostgreSQL connection.

This script uses psycopg2 to connect directly to PostgreSQL and execute the migration.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings


def get_postgres_connection_string() -> str:
    """Build PostgreSQL connection string from Supabase URL."""
    # Supabase URL format: https://PROJECT_ID.supabase.co
    # PostgreSQL connection: postgresql://postgres:[PASSWORD]@db.PROJECT_ID.supabase.co:5432/postgres
    
    if not settings.supabase_url:
        raise ValueError("SUPABASE_URL not configured")
    
    # Extract project ID from Supabase URL
    # Example: https://dcxdnrealygulikpuicm.supabase.co -> dcxdnrealygulikpuicm
    project_id = settings.supabase_url.replace("https://", "").replace(".supabase.co", "")
    
    # Get database password from environment
    db_password = os.getenv("SUPABASE_DB_PASSWORD") or os.getenv("DATABASE_PASSWORD")
    
    if not db_password:
        raise ValueError(
            "Database password not found. Please set SUPABASE_DB_PASSWORD or DATABASE_PASSWORD environment variable"
        )
    
    # Build connection string
    conn_str = f"postgresql://postgres:{db_password}@db.{project_id}.supabase.co:5432/postgres"
    
    return conn_str


def apply_migration_with_psycopg2():
    """Apply migration using psycopg2."""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed")
        print("   Install it with: pip install psycopg2-binary")
        return False
    
    print("=" * 60)
    print("🔧 Applying migration with direct PostgreSQL connection")
    print("=" * 60)
    print()
    
    try:
        # Get connection string
        conn_str = get_postgres_connection_string()
        print("📡 Connecting to PostgreSQL...")
        
        # Read migration file
        migration_path = Path(__file__).parent / "migrations" / "009_remove_email_auth.sql"
        with open(migration_path, "r", encoding="utf-8") as f:
            sql = f.read()
        
        # Connect and execute
        conn = psycopg2.connect(conn_str)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("✅ Connected successfully")
        print()
        print("🚀 Executing migration...")
        print()
        
        # Execute the migration
        cursor.execute(sql)
        
        # Commit the transaction
        conn.commit()
        
        print()
        print("✅ Migration applied successfully!")
        print()
        
        # Verify the changes
        print("🔍 Verifying changes...")
        cursor.execute("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print()
        print("Current users table schema:")
        print("-" * 60)
        for col_name, nullable, data_type in columns:
            null_str = "NULL" if nullable == "YES" else "NOT NULL"
            print(f"  {col_name:20} {data_type:15} {null_str}")
        print()
        
        # Check that email columns are gone
        email_cols = [col for col, _, _ in columns if 'email' in col.lower() or 'password' in col.lower()]
        if email_cols:
            print(f"⚠️  Warning: Email-related columns still exist: {email_cols}")
        else:
            print("✅ All email-related columns removed")
        
        # Check that telegram_id is NOT NULL
        telegram_col = [col for col, nullable, _ in columns if col == 'telegram_id']
        if telegram_col:
            _, nullable, _ = [(c, n, t) for c, n, t in columns if c == 'telegram_id'][0]
            if nullable == 'NO':
                print("✅ telegram_id is NOT NULL")
            else:
                print("⚠️  Warning: telegram_id is still nullable")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Restart your application")
        print("2. Test bot functionality")
        print()
        
        return True
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print()
        print("To apply the migration, you need the database password.")
        print("Set it with: export SUPABASE_DB_PASSWORD='your_password'")
        print()
        print("Or use Supabase SQL Editor:")
        print(f"  File: {Path(__file__).parent / 'migrations' / '009_remove_email_auth.sql'}")
        print()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = apply_migration_with_psycopg2()
    sys.exit(0 if success else 1)

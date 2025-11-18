#!/usr/bin/env python3
"""
Apply users table fix directly via Supabase.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


async def apply_fix():
    """Apply users table fix."""
    print("="*60)
    print("🔧 Applying users table fix...")
    print("="*60)
    
    # Read SQL
    sql_file = Path(__file__).parent / "FIX_USERS_TABLE.sql"
    sql_content = sql_file.read_text()
    
    # Split into individual statements
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
    
    print(f"\n📄 Found {len(statements)} SQL statements to execute\n")
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not service_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return False
    
    # Extract project ref from URL
    # https://dcxdnrealygulikpuicm.supabase.co -> dcxdnrealygulikpuicm
    project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
    
    print(f"🔗 Supabase Project: {project_ref}")
    print(f"🔗 URL: {supabase_url}")
    
    # Use httpx to execute SQL via Supabase REST API
    import httpx
    
    # Supabase doesn't have direct SQL execution via REST API
    # We need to use PostgREST or direct PostgreSQL connection
    
    print("\n⚠️  Supabase REST API doesn't support direct SQL execution")
    print("📝 Applying via ALTER TABLE commands through PostgREST...\n")
    
    # Try to add columns via Supabase client
    from app.shared.supabase import get_supabase_client
    
    client = get_supabase_client()
    
    # Check current schema
    print("1️⃣ Checking current users table schema...")
    try:
        result = client.table('users').select('*').limit(1).execute()
        if result.data:
            print(f"   ✅ Users table exists with {len(result.data[0].keys())} columns")
            print(f"   Columns: {', '.join(result.data[0].keys())}")
    except Exception as e:
        print(f"   ⚠️  Error checking schema: {e}")
    
    print("\n2️⃣ SQL statements to apply:")
    print("-" * 60)
    
    # Show SQL that needs to be applied
    important_statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT",
    ]
    
    for stmt in important_statements:
        print(f"   {stmt}")
    
    print("\n" + "="*60)
    print("📋 MANUAL APPLICATION REQUIRED")
    print("="*60)
    print("\nSupabase REST API doesn't support ALTER TABLE commands.")
    print("Please apply the SQL manually:\n")
    print("Method 1: Supabase Dashboard")
    print("-" * 40)
    print("1. Go to: https://supabase.com/dashboard")
    print(f"2. Select project: {project_ref}")
    print("3. Go to: SQL Editor")
    print("4. Copy and paste from: backend/FIX_USERS_TABLE.sql")
    print("5. Click 'Run'\n")
    
    print("Method 2: Use psql (if you have DATABASE_URL)")
    print("-" * 40)
    print("psql $DATABASE_URL -f backend/FIX_USERS_TABLE.sql\n")
    
    print("Method 3: Copy SQL directly")
    print("-" * 40)
    print("\n--- SQL TO APPLY ---\n")
    print(sql_content[:1000] + "...\n")
    
    return False


if __name__ == "__main__":
    asyncio.run(apply_fix())

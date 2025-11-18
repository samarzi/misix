#!/usr/bin/env python3
"""
Apply users table fix via direct PostgreSQL connection.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

def apply_fix():
    """Apply users table fix via psycopg2."""
    print("="*60)
    print("🔧 Applying users table fix via PostgreSQL...")
    print("="*60)
    
    # Check if we have DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Try to construct from Supabase credentials
        supabase_url = os.getenv('SUPABASE_URL', '')
        service_key = os.getenv('SUPABASE_SERVICE_KEY', '')
        
        if not supabase_url:
            print("\n❌ No DATABASE_URL or SUPABASE_URL found")
            print("\n📋 To apply the fix manually:")
            print("1. Go to https://supabase.com/dashboard")
            print("2. Select your project")
            print("3. Go to SQL Editor")
            print("4. Copy and paste from backend/FIX_USERS_TABLE.sql")
            print("5. Click 'Run'")
            return False
        
        # Extract project ref
        project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
        
        print(f"\n⚠️  DATABASE_URL not set")
        print(f"📝 Project: {project_ref}")
        print("\nTo get your DATABASE_URL:")
        print("1. Go to https://supabase.com/dashboard")
        print(f"2. Select project: {project_ref}")
        print("3. Go to: Settings → Database")
        print("4. Copy 'Connection string' (URI format)")
        print("5. Add to .env: DATABASE_URL=postgresql://...")
        print("\nOr apply SQL manually in SQL Editor")
        return False
    
    # Try to connect and apply
    try:
        import psycopg2
        
        print(f"\n🔗 Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("✅ Connected!")
        
        # Read SQL file
        sql_file = Path(__file__).parent / "FIX_USERS_TABLE.sql"
        sql_content = sql_file.read_text()
        
        print(f"\n📄 Executing SQL from {sql_file.name}...")
        
        # Execute
        cursor.execute(sql_content)
        conn.commit()
        
        print("✅ SQL executed successfully!")
        
        # Verify
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f"\n📊 Users table now has {len(columns)} columns:")
        for col in columns:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            print(f"   - {col[0]}: {col[1]} ({nullable})")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("✅ Fix applied successfully!")
        print("="*60)
        
        return True
        
    except ImportError:
        print("\n❌ psycopg2 not installed")
        print("Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n📋 Please apply manually:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. SQL Editor")
        print("3. Copy from backend/FIX_USERS_TABLE.sql")
        return False


if __name__ == "__main__":
    success = apply_fix()
    sys.exit(0 if success else 1)

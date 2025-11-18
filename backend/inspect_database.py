#!/usr/bin/env python3
"""
Complete database inspection tool
Shows all tables, columns, data, and errors
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import json

# Load environment
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.shared.supabase import get_supabase_client


def main():
    """Run complete database inspection."""
    print("="*80)
    print("🔍 COMPLETE DATABASE INSPECTION")
    print("="*80)
    print()
    
    try:
        client = get_supabase_client()
        print("✅ Connected to Supabase")
        print(f"   URL: {client.supabase_url}")
        print()
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # List of expected tables
    expected_tables = [
        "users",
        "tasks", 
        "finance_entries",
        "notes",
        "note_folders",
        "mood_entries",
        "assistant_messages",
        "user_settings",
        "sleep_tracking",
        "personal_entries"
    ]
    
    print("="*80)
    print("📋 CHECKING ALL TABLES")
    print("="*80)
    print()
    
    existing_tables = []
    missing_tables = []
    
    for table in expected_tables:
        print(f"Checking table: {table}")
        print("-" * 80)
        
        try:
            # Try to get table structure by querying it
            result = client.table(table).select("*").limit(1).execute()
            
            print(f"✅ Table EXISTS: {table}")
            
            # Get record count
            count_result = client.table(table).select("*").execute()
            record_count = len(count_result.data) if count_result.data else 0
            print(f"   Records: {record_count}")
            
            # Show sample data if exists
            if result.data:
                print(f"   Columns: {', '.join(result.data[0].keys())}")
                print(f"   Sample record:")
                for key, value in result.data[0].items():
                    value_str = str(value)[:50]
                    print(f"      {key}: {value_str}")
            else:
                # Try to get columns from empty table
                print(f"   Table is empty, trying to get structure...")
                
            existing_tables.append(table)
            
        except Exception as e:
            print(f"❌ Table MISSING or ERROR: {table}")
            print(f"   Error: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            
            # Try to get more details
            try:
                import traceback
                print(f"   Traceback:")
                traceback.print_exc()
            except:
                pass
                
            missing_tables.append(table)
        
        print()
    
    # Summary
    print("="*80)
    print("📊 SUMMARY")
    print("="*80)
    print()
    print(f"✅ Existing tables ({len(existing_tables)}):")
    for table in existing_tables:
        print(f"   - {table}")
    print()
    
    if missing_tables:
        print(f"❌ Missing tables ({len(missing_tables)}):")
        for table in missing_tables:
            print(f"   - {table}")
        print()
    
    # Test specific operations
    print("="*80)
    print("🧪 TESTING SPECIFIC OPERATIONS")
    print("="*80)
    print()
    
    # Test 1: Can we create a user?
    print("Test 1: User creation")
    print("-" * 40)
    try:
        # Try to get users table structure
        result = client.table("users").select("*").limit(1).execute()
        if result.data:
            print("✅ Users table accessible")
            print(f"   Sample user columns: {list(result.data[0].keys())}")
        else:
            print("⚠️  Users table empty but accessible")
    except Exception as e:
        print(f"❌ Cannot access users table: {e}")
    print()
    
    # Test 2: Can we query messages?
    print("Test 2: Messages query")
    print("-" * 40)
    try:
        result = client.table("assistant_messages").select("*").limit(5).execute()
        print(f"✅ Messages table accessible")
        print(f"   Found {len(result.data)} messages")
        if result.data:
            print(f"   Latest message: {result.data[0].get('content', '')[:50]}...")
    except Exception as e:
        print(f"❌ Cannot access messages: {e}")
    print()
    
    # Test 3: Can we query tasks?
    print("Test 3: Tasks query")
    print("-" * 40)
    try:
        result = client.table("tasks").select("*").limit(5).execute()
        print(f"✅ Tasks table accessible")
        print(f"   Found {len(result.data)} tasks")
        if result.data:
            for task in result.data[:3]:
                print(f"   - {task.get('title', 'No title')} ({task.get('status', 'unknown')})")
    except Exception as e:
        print(f"❌ Cannot access tasks: {e}")
    print()
    
    # Final status
    print("="*80)
    print("🎯 FINAL STATUS")
    print("="*80)
    print()
    
    if len(existing_tables) == len(expected_tables):
        print("✅ ALL TABLES EXIST - Database is complete!")
    else:
        print(f"⚠️  INCOMPLETE - {len(missing_tables)} tables missing")
        print()
        print("Missing tables need to be created:")
        for table in missing_tables:
            print(f"   - {table}")
        print()
        print("Run: backend/SIMPLE_COMPLETE_MIGRATION.sql in Supabase Dashboard")
    
    print()
    print("="*80)


if __name__ == "__main__":
    main()

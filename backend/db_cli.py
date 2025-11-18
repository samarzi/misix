#!/usr/bin/env python3
"""
Database CLI tool for MISIX
Connect to Supabase database and run SQL queries
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.shared.supabase import get_supabase_client


def main():
    """Main CLI interface."""
    print("="*60)
    print("🗄️  MISIX Database CLI")
    print("="*60)
    print()
    
    try:
        client = get_supabase_client()
        print("✅ Connected to Supabase")
        print(f"   URL: {client.supabase_url[:40]}...")
        print()
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    print("Available commands:")
    print("  1. List all tables")
    print("  2. Count records in each table")
    print("  3. Show users")
    print("  4. Show tasks")
    print("  5. Show recent messages")
    print("  6. Run custom query")
    print("  0. Exit")
    print()
    
    while True:
        try:
            choice = input("Enter command (0-6): ").strip()
            print()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
                
            elif choice == "1":
                list_tables(client)
                
            elif choice == "2":
                count_records(client)
                
            elif choice == "3":
                show_users(client)
                
            elif choice == "4":
                show_tasks(client)
                
            elif choice == "5":
                show_messages(client)
                
            elif choice == "6":
                run_custom_query(client)
                
            else:
                print("❌ Invalid choice")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print()


def list_tables(client):
    """List all tables."""
    print("📋 Tables in database:")
    print("-" * 40)
    
    tables = [
        "users", "tasks", "finance_entries", "notes", "note_folders",
        "mood_entries", "assistant_messages", "user_settings",
        "sleep_tracking", "personal_entries"
    ]
    
    for table in tables:
        try:
            result = client.table(table).select("*", count="exact").limit(0).execute()
            count = result.count if hasattr(result, 'count') else "?"
            print(f"  ✅ {table:<25} ({count} records)")
        except Exception as e:
            print(f"  ❌ {table:<25} (error: {str(e)[:30]})")


def count_records(client):
    """Count records in each table."""
    print("📊 Record counts:")
    print("-" * 40)
    
    tables = [
        "users", "tasks", "finance_entries", "notes",
        "mood_entries", "assistant_messages"
    ]
    
    for table in tables:
        try:
            result = client.table(table).select("id").execute()
            count = len(result.data) if result.data else 0
            print(f"  {table:<25} {count:>6} records")
        except Exception as e:
            print(f"  {table:<25} ERROR")


def show_users(client):
    """Show users."""
    print("👥 Users:")
    print("-" * 60)
    
    try:
        result = client.table("users").select("id, telegram_id, username, first_name, created_at").limit(10).execute()
        
        if not result.data:
            print("  No users found")
            return
        
        for user in result.data:
            print(f"  ID: {user.get('id')}")
            print(f"  Telegram: {user.get('telegram_id')} (@{user.get('username', 'N/A')})")
            print(f"  Name: {user.get('first_name', 'N/A')}")
            print(f"  Created: {user.get('created_at', 'N/A')[:10]}")
            print()
            
    except Exception as e:
        print(f"  ❌ Error: {e}")


def show_tasks(client):
    """Show tasks."""
    print("📋 Tasks:")
    print("-" * 60)
    
    try:
        result = client.table("tasks").select("id, title, status, priority, deadline").limit(10).execute()
        
        if not result.data:
            print("  No tasks found")
            return
        
        for task in result.data:
            status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(task.get('status'), "❓")
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get('priority'), "⚪")
            
            print(f"  {status_emoji} {priority_emoji} {task.get('title')}")
            print(f"     Status: {task.get('status')}, Deadline: {task.get('deadline', 'None')}")
            print()
            
    except Exception as e:
        print(f"  ❌ Error: {e}")


def show_messages(client):
    """Show recent messages."""
    print("💬 Recent messages:")
    print("-" * 60)
    
    try:
        result = client.table("assistant_messages").select("role, content, created_at").order("created_at", desc=True).limit(5).execute()
        
        if not result.data:
            print("  No messages found")
            return
        
        for msg in result.data:
            role_emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(msg.get('role'), "❓")
            content = msg.get('content', '')[:60]
            
            print(f"  {role_emoji} {msg.get('role')}: {content}...")
            print(f"     {msg.get('created_at', 'N/A')[:19]}")
            print()
            
    except Exception as e:
        print(f"  ❌ Error: {e}")


def run_custom_query(client):
    """Run custom query."""
    print("⚠️  Custom queries via Supabase client are limited")
    print("For complex SQL, use psql or Supabase Dashboard")
    print()
    
    table = input("Enter table name: ").strip()
    if not table:
        return
    
    try:
        result = client.table(table).select("*").limit(5).execute()
        
        if not result.data:
            print(f"  No data in {table}")
            return
        
        print(f"\n📊 First 5 records from {table}:")
        print("-" * 60)
        
        for i, record in enumerate(result.data, 1):
            print(f"\nRecord {i}:")
            for key, value in record.items():
                value_str = str(value)[:50]
                print(f"  {key}: {value_str}")
                
    except Exception as e:
        print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    main()

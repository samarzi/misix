#!/usr/bin/env python3
import sys
sys.path.append('backend')
from app.shared.supabase import get_supabase_client

def create_test_user():
    supabase = get_supabase_client()
    # Create test user with telegram_id 123456789
    user_data = {
        "telegram_id": 123456789,
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com"
    }
    response = supabase.table("users").insert(user_data).execute()
    print("Created test user:", response.data)

if __name__ == "__main__":
    create_test_user()

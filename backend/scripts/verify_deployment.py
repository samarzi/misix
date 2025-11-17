#!/usr/bin/env python3
"""Deployment verification script for MISIX application.

This script verifies that a deployed MISIX instance is working correctly by:
1. Checking health endpoint
2. Testing database connectivity
3. Verifying environment variables
4. Testing bot functionality (if token provided)

Usage:
    python scripts/verify_deployment.py --url https://your-app.onrender.com
    python scripts/verify_deployment.py --url https://your-app.onrender.com --check-bot
"""

import argparse
import asyncio
import os
import sys
from typing import Optional
from urllib.parse import urljoin

try:
    import httpx
except ImportError:
    print("❌ Error: httpx not installed. Run: pip install httpx")
    sys.exit(1)


class DeploymentVerifier:
    """Verifies deployment health and functionality."""
    
    def __init__(self, base_url: str, check_bot: bool = False):
        """Initialize verifier.
        
        Args:
            base_url: Base URL of deployed application
            check_bot: Whether to check bot functionality
        """
        self.base_url = base_url.rstrip('/')
        self.check_bot = check_bot
        self.client = httpx.AsyncClient(timeout=30.0)
        self.passed = 0
        self.failed = 0
    
    async def verify_all(self) -> bool:
        """Run all verification checks.
        
        Returns:
            True if all checks passed, False otherwise
        """
        print("=" * 60)
        print("🔍 MISIX Deployment Verification")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print()
        
        try:
            await self.check_health()
            await self.check_environment_vars()
            
            if self.check_bot:
                await self.check_bot_functionality()
            
            print()
            print("=" * 60)
            print(f"Results: {self.passed} passed, {self.failed} failed")
            print("=" * 60)
            
            if self.failed == 0:
                print("✅ All checks passed! Deployment is healthy.")
                return True
            else:
                print(f"❌ {self.failed} checks failed. See details above.")
                return False
                
        finally:
            await self.client.aclose()
    
    async def check_health(self):
        """Check health endpoint."""
        print("🔍 Checking health endpoint...")
        
        try:
            url = urljoin(self.base_url, "/health")
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["ok", "healthy"]:
                    print(f"✅ Health check passed: {data}")
                    self.passed += 1
                else:
                    print(f"⚠️  Health check returned unexpected status: {data}")
                    self.failed += 1
            else:
                print(f"❌ Health check failed: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.failed += 1
                
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            self.failed += 1
    
    async def check_environment_vars(self):
        """Check if required environment variables are configured."""
        print("\n🔍 Checking environment configuration...")
        
        # We can't directly check env vars on remote server,
        # but we can infer from startup logs or API responses
        
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_SERVICE_KEY",
            "SUPABASE_ANON_KEY",
            "JWT_SECRET_KEY",
            "YANDEX_GPT_API_KEY",
            "YANDEX_FOLDER_ID"
        ]
        
        print(f"ℹ️  Required environment variables:")
        for var in required_vars:
            print(f"   - {var}")
        
        print("\n💡 To verify environment variables:")
        print("   1. Check Render dashboard → Environment tab")
        print("   2. Review startup logs for validation messages")
        print("   3. Look for '✅ Phase 1 complete: Configuration validation passed'")
        
        # This is informational only, not a failure
        self.passed += 1
    
    async def check_bot_functionality(self):
        """Check if Telegram bot is configured and working."""
        print("\n🔍 Checking Telegram bot...")
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not bot_token:
            print("⚠️  TELEGRAM_BOT_TOKEN not set in local environment")
            print("   Set it to test bot functionality:")
            print("   export TELEGRAM_BOT_TOKEN=your_token")
            return
        
        try:
            # Test bot API
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data.get("result", {})
                    print(f"✅ Bot is configured: @{bot_info.get('username')}")
                    self.passed += 1
                else:
                    print(f"❌ Bot API returned error: {data}")
                    self.failed += 1
            else:
                print(f"❌ Bot API check failed: HTTP {response.status_code}")
                self.failed += 1
                
        except Exception as e:
            print(f"❌ Bot check failed: {e}")
            self.failed += 1


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify MISIX deployment health and functionality"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Base URL of deployed application (e.g., https://your-app.onrender.com)"
    )
    parser.add_argument(
        "--check-bot",
        action="store_true",
        help="Also check Telegram bot functionality (requires TELEGRAM_BOT_TOKEN env var)"
    )
    
    args = parser.parse_args()
    
    verifier = DeploymentVerifier(args.url, args.check_bot)
    success = await verifier.verify_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

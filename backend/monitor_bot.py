#!/usr/bin/env python3
"""
Bot monitoring script - shows all errors and database operations in real-time
"""

import asyncio
import logging
from dotenv import load_dotenv
import sys

# Load environment
load_dotenv()

# Setup detailed logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,  # Show ALL logs including DEBUG
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Start bot with detailed monitoring."""
    from app.bot import get_application
    
    print("="*80)
    print("🔍 MISIX Bot - Detailed Monitoring Mode")
    print("="*80)
    print()
    print("This will show ALL errors, warnings, and database operations")
    print()
    
    # Get application
    app = get_application()
    
    if app is None:
        print("❌ Failed to create bot application")
        return
    
    try:
        # Initialize
        print("📡 Initializing bot...")
        await app.initialize()
        
        print(f"✅ Bot initialized: @{app.bot.username}")
        print(f"✅ Handlers registered: {len(app.handlers)}")
        print()
        
        # Start
        print("🚀 Starting bot...")
        await app.start()
        
        # Start polling
        print("📡 Starting polling...")
        await app.updater.start_polling()
        
        print()
        print("="*80)
        print("✅ Bot is running in MONITORING MODE")
        print("="*80)
        print()
        print("📊 Watching for:")
        print("   - All incoming messages")
        print("   - Database operations")
        print("   - Errors and exceptions")
        print("   - AI service calls")
        print()
        print("⏹  Press Ctrl+C to stop")
        print("="*80)
        print()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹  Stopping bot...")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        print(f"\n❌ Bot crashed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            print("👋 Bot stopped")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

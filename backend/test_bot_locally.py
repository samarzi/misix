#!/usr/bin/env python3
"""
Test bot locally in polling mode.

This script starts the bot in polling mode for local testing.
"""

import asyncio
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    """Start bot in polling mode."""
    from app.bot import get_application
    
    print("="*60)
    print("🤖 Starting MISIX Bot (Local Testing Mode)")
    print("="*60)
    
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
        
        # Start
        print("🚀 Starting bot...")
        await app.start()
        
        # Start polling
        print("📡 Starting polling...")
        await app.updater.start_polling()
        
        print("\n" + "="*60)
        print("✅ Bot is running!")
        print("="*60)
        print("\n💬 Send a message to @misix_helpbot to test")
        print("\n📋 Test commands:")
        print("  /start - Start bot")
        print("  /help - Show help")
        print("  /tasks - Show tasks")
        print("  /finances - Show finances")
        print("  /mood - Show mood")
        print("\n💡 Test natural language:")
        print("  'напомни купить молоко'")
        print("  'потратил 500₽ на кофе'")
        print("  'отличное настроение'")
        print("\n⏹  Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹  Stopping bot...")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
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

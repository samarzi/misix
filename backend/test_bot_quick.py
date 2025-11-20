#!/usr/bin/env python3
"""Quick bot test script."""

import asyncio
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_bot():
    """Test bot functionality."""
    try:
        # Import bot
        from app.bot import get_application, get_polling_manager
        
        logger.info("🤖 Initializing bot...")
        app = get_application()
        
        if not app:
            logger.error("❌ Failed to create bot application")
            return False
        
        # Initialize application
        await app.initialize()
        logger.info("✅ Bot initialized")
        
        # Get bot info
        bot = app.bot
        me = await bot.get_me()
        logger.info(f"✅ Bot username: @{me.username}")
        logger.info(f"✅ Bot name: {me.first_name}")
        
        # Start polling
        polling_manager = get_polling_manager()
        if not polling_manager:
            logger.error("❌ Failed to create polling manager")
            return False
        
        logger.info("🚀 Starting polling...")
        await polling_manager.start_polling()
        
        logger.info("✅ Bot is running! Send messages to test.")
        logger.info("Press Ctrl+C to stop")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n⏹️  Stopping bot...")
            await polling_manager.stop_polling()
            await app.shutdown()
            logger.info("✅ Bot stopped")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_bot())
    sys.exit(0 if success else 1)

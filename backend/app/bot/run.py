from app.bot import application
import os
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv('.env.local')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main bot startup function with better error handling."""
    print("🤖 Starting MISIX Bot...")

    try:
        # Check environment variables
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not found in environment!")
            return

        print(f"✅ Bot token configured: {bot_token[:10]}...")

        # Determine run mode
        webhook_url = os.getenv('BACKEND_BASE_URL')
        is_local = webhook_url and 'localhost' in webhook_url

        if is_local:
            print("🏠 Running in LOCAL MODE (polling)")
            await run_local_mode()
        else:
            print("🌐 Running in PRODUCTION MODE (webhook)")
            await run_production_mode(webhook_url)

    except Exception as e:
        logger.error(f"❌ Bot startup failed: {e}")
        print(f"❌ Bot startup failed: {e}")

async def run_local_mode():
    """Run bot in local polling mode for development."""
    print("📡 Starting polling mode...")

    try:
        await application.initialize()
        await application.start()
        print("✅ Bot started successfully!")

        # Start polling
        await application.updater.start_polling()
        print("✅ Polling started - bot is listening for messages!")

        # Keep running
        while True:
            await asyncio.sleep(30)
            print("💓 Bot is active (polling)...")

    except Exception as e:
        logger.error(f"Polling mode failed: {e}")
        print(f"❌ Polling mode failed: {e}")
    finally:
        try:
            await application.stop()
            print("👋 Bot stopped")
        except Exception as stop_error:
            logger.warning(f"Error stopping application: {stop_error}")

async def run_production_mode(webhook_url):
    """Run bot in production webhook mode."""
    print(f"🚀 Setting webhook to: {webhook_url}/bot/webhook")

    try:
        await application.bot.set_webhook(f"{webhook_url}/bot/webhook")
        print("✅ Webhook set successfully")

        await application.start()
        print("✅ Bot started in webhook mode")

        # Keep running
        while True:
            await asyncio.sleep(60)
            print("💓 Bot is active (webhook)...")

    except Exception as e:
        logger.error(f"Webhook mode failed: {e}")
        print(f"❌ Webhook mode failed: {e}")
        print("🔄 Falling back to polling mode...")
        await run_local_mode()
    finally:
        try:
            await application.stop()
            print("👋 Bot stopped")
        except Exception as stop_error:
            logger.warning(f"Error stopping application: {stop_error}")

if __name__ == "__main__":
    asyncio.run(main())

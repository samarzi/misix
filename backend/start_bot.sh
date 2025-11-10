#!/bin/bash
# Simple bot launcher script

cd "$(dirname "$0")"

# Load environment variables
if [ -f ".env.local" ]; then
    export $(grep -v '^#' .env.local | xargs)
    echo "✅ Environment variables loaded from .env.local"
else
    echo "⚠️  .env.local not found"
fi

echo "🤖 Starting MOZG Bot..."
PYTHONPATH=/Users/samarzi/Desktop/windsurf-project/backend python3 -c "
import asyncio
from app.bot import application

async def run_bot():
    print('📡 Starting bot with polling...')
    try:
        await application.initialize()
        await application.start()
        print('✅ Bot started successfully!')
        print('💬 Bot is now listening for messages in Telegram')

        # Start polling with better settings
        await application.updater.start_polling(
            allowed_updates=['message', 'callback_query'],
            drop_pending_updates=True
        )

        # Keep running
        while True:
            await asyncio.sleep(30)
            print('💓 Bot is active...')

    except KeyboardInterrupt:
        print('🛑 Shutting down...')
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await application.stop()
        print('👋 Bot stopped')

asyncio.run(run_bot())
" 2>&1 | tee bot.log

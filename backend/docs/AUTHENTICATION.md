# Authentication System Documentation

## Overview

MISIX uses Telegram-based authentication. Users interact with the application through the Telegram bot, and authentication is handled automatically via Telegram user IDs (`telegram_id`).

**Note:** Email/password authentication has been removed from the application. All authentication is now handled through Telegram.

## How It Works

1. **User Interaction**: Users interact with MISIX through the Telegram bot
2. **Automatic Registration**: When a user first messages the bot, they are automatically registered using their Telegram ID
3. **User Identification**: All subsequent interactions are authenticated using the Telegram ID
4. **No Passwords**: No passwords or email addresses are required

## User Data Structure

Users in the database have the following structure:

```python
{
  "id": "123e4567-e89b-12d3-a456-426614174000",  # UUID
  "telegram_id": 123456789,                       # Telegram user ID (required)
  "username": "john_doe",                         # Telegram username (optional)
  "full_name": "John Doe",                        # User's full name
  "language_code": "en",                          # Telegram language preference
  "created_at": "2025-01-17T10:30:00Z",
  "updated_at": "2025-01-17T10:30:00Z"
}
```

## Getting Started

### For Users

1. Open Telegram
2. Search for the MISIX bot
3. Send `/start` command
4. Start using the bot - you're automatically authenticated!

### For Developers

Users are automatically created when they interact with the bot. The bot handlers in `backend/app/bot/handlers/` manage user creation and authentication.

**Example: Getting or Creating a User**

```python
from app.repositories.user import UserRepository

async def get_or_create_user(telegram_id: int, username: str, full_name: str):
    """Get existing user or create new one from Telegram data."""
    user_repo = UserRepository()
    
    # Try to get existing user
    user = await user_repo.get_by_telegram_id(telegram_id)
    
    if not user:
        # Create new user
        user = await user_repo.create({
            "telegram_id": telegram_id,
            "username": username,
            "full_name": full_name,
            "language_code": "en"
        })
    
    return user
```

## Bot Configuration

The Telegram bot is configured via environment variables:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather  # Required
TELEGRAM_WEBHOOK_URL=https://your-domain.com      # Optional (for webhook mode)
```

**Getting a Bot Token:**

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token provided by BotFather
5. Set it as `TELEGRAM_BOT_TOKEN` environment variable

## Security Considerations

### Telegram Authentication Security

- **Telegram ID Verification**: Telegram IDs are unique and cannot be spoofed
- **Bot Token Security**: Keep your bot token secret - never commit it to version control
- **Webhook Security**: If using webhooks, ensure your webhook URL uses HTTPS
- **User Privacy**: Respect Telegram user privacy - only store necessary data

### Best Practices

1. **Secure Bot Token**
   - Store bot token in environment variables
   - Never expose bot token in logs or error messages
   - Rotate bot token if compromised

2. **Validate Telegram Data**
   - Always validate that messages come from Telegram
   - Check webhook signatures if using webhooks
   - Validate user data before storing

3. **Handle User Data Responsibly**
   - Only store necessary user information
   - Comply with GDPR and data protection regulations
   - Provide users with data deletion options

## Troubleshooting

### Bot Not Responding

**Possible Causes:**
- Bot token is incorrect or expired
- Bot is not running (check application logs)
- Network connectivity issues
- Telegram API is down

**Solutions:**
1. Check bot token in environment variables
2. Verify bot is running: check application logs
3. Test bot token with Telegram API:
   ```bash
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
   ```
4. Check Telegram API status

### User Not Created

**Possible Causes:**
- Database connection issues
- Missing required fields (telegram_id)
- Database schema not applied

**Solutions:**
1. Check database connection in logs
2. Verify database schema is up to date
3. Check that telegram_id is being passed correctly
4. Review application logs for errors

### Database Validation Fails

**Possible Causes:**
- Email/password columns still exist in database
- telegram_id column is nullable
- Migration not applied

**Solutions:**
1. Apply the migration: `migrations/009_remove_email_auth.sql`
2. Verify schema with:
   ```sql
   SELECT column_name, is_nullable 
   FROM information_schema.columns 
   WHERE table_name = 'users';
   ```
3. Ensure telegram_id is NOT NULL

## Development

### Testing the Bot Locally

1. Set up environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="your-bot-token"
   export SUPABASE_URL="your-supabase-url"
   export SUPABASE_SERVICE_KEY="your-service-key"
   ```

2. Run the application:
   ```bash
   cd backend
   python -m uvicorn app.web.main:app --reload
   ```

3. Send a message to your bot in Telegram

4. Check logs to see user creation and message processing

### Bot Handlers

Bot handlers are located in `backend/app/bot/handlers/`:
- `command.py` - Command handlers (/start, /help, etc.)
- `message.py` - Text message handlers
- `sleep.py` - Sleep tracking handlers

## API Integration (Optional)

If you need to integrate with the API programmatically, you can use Telegram ID for authentication:

```python
import requests

# Get user by Telegram ID
telegram_id = 123456789
response = requests.get(
    f"http://localhost:8000/api/users/telegram/{telegram_id}"
)
user = response.json()
print(f"User: {user['full_name']}")
```

**Note:** API endpoints for Telegram authentication can be added as needed in `backend/app/api/routers/`.

## Support

For issues or questions:
1. Check application logs in `backend/logs/`
2. Review Telegram bot documentation: https://core.telegram.org/bots
3. Check database schema and migrations
4. Contact the development team

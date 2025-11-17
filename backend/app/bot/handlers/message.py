"""Message handlers for Telegram bot."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.repositories.user import get_user_repository
from app.services.conversation_service import get_conversation_service
from app.services.ai_service import get_ai_service

logger = logging.getLogger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages from users.
    
    Processes user messages through AI service with conversation context.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    try:
        # 1. Extract data from Telegram Update
        user_telegram = update.effective_user
        message_text = update.message.text
        
        logger.info(f"Received message from user {user_telegram.id}: {message_text[:50]}...")
        
        # 2. Get or create user
        user_repo = get_user_repository()
        try:
            user = await user_repo.get_or_create_by_telegram_id(
                telegram_id=user_telegram.id,
                username=user_telegram.username,
                first_name=user_telegram.first_name,
                last_name=user_telegram.last_name
            )
            user_id = str(user["id"])
        except Exception as e:
            # Fallback: use telegram_id as user_id if database is unavailable
            logger.warning(f"Database unavailable, using telegram_id as user_id: {e}")
            user_id = str(user_telegram.id)
        
        # 3. Get conversation context
        conv_service = get_conversation_service()
        conversation_context = await conv_service.get_conversation_context(user_id)
        
        # 4. Save user message to history
        await conv_service.add_message(
            user_id=user_id,
            role="user",
            content=message_text,
            telegram_id=user_telegram.id
        )
        
        # 5. Generate AI response
        ai_service = get_ai_service()
        response = await ai_service.generate_response(
            user_message=message_text,
            conversation_context=conversation_context
        )
        
        logger.info(f"Generated response for user {user_telegram.id} (length: {len(response)})")
        
        # 6. Save assistant response to history
        await conv_service.add_message(
            user_id=user_id,
            role="assistant",
            content=response,
            telegram_id=user_telegram.id
        )
        
        # 7. Send reply to user
        await update.message.reply_text(response)
        
    except Exception as e:
        # Handle any unexpected errors
        logger.error(f"Message processing failed for user {update.effective_user.id}: {e}", exc_info=True)
        
        # Send user-friendly error message
        try:
            await update.message.reply_text(
                "Извините, произошла ошибка при обработке вашего сообщения. Пожалуйста, попробуйте позже."
            )
        except Exception as reply_error:
            logger.error(f"Failed to send error message: {reply_error}")


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice messages from users.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    user = update.effective_user
    
    logger.info(f"Received voice message from user {user.id}")
    
    # TODO: Implement voice transcription
    await update.message.reply_text(
        "Голосовые сообщения будут поддерживаться после завершения рефакторинга."
    )

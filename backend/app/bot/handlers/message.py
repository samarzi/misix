"""Message handlers for Telegram bot."""

import logging
import copy
import asyncio
import time
from telegram import Update, Message
from telegram.ext import ContextTypes

from app.repositories.user import get_user_repository
from app.services.conversation_service import get_conversation_service
from app.services.ai_service import get_ai_service
from app.bot.intent_processor import get_intent_processor
from app.bot.response_builder import get_response_builder
from app.bot.yandex_speech import get_yandex_speech_kit

logger = logging.getLogger(__name__)

# Timeouts for voice processing
VOICE_DOWNLOAD_TIMEOUT = 10  # seconds
VOICE_TRANSCRIPTION_TIMEOUT = 30  # seconds


def create_mock_text_update(voice_update: Update, text: str) -> Update:
    """Create mock text update from voice update for processing.
    
    Creates a new Update object with a text message instead of modifying
    the original immutable Telegram objects.
    
    Args:
        voice_update: Original update with voice message
        text: Transcribed text
        
    Returns:
        New update with text message
    """
    from telegram import Message as TelegramMessage, Chat, User
    
    # Get original message data
    original_msg = voice_update.message
    
    # Create new Message object with text (set during construction)
    # We need to provide all required fields for Message
    mock_message = TelegramMessage(
        message_id=original_msg.message_id,
        date=original_msg.date,
        chat=original_msg.chat,
        from_user=original_msg.from_user,
        text=text,  # Set text during construction
    )
    
    # Create new Update with the new message
    mock_update = Update(
        update_id=voice_update.update_id,
        message=mock_message,
    )
    
    return mock_update


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
        user_id = None
        try:
            user = await user_repo.get_or_create_by_telegram_id(
                telegram_id=user_telegram.id,
                username=user_telegram.username,
                first_name=user_telegram.first_name,
                last_name=user_telegram.last_name
            )
            user_id = str(user["id"])
            logger.info(f"User loaded/created: {user_id}")
        except Exception as e:
            # Database unavailable - continue without saving to DB
            logger.error(f"Failed to get/create user: {e}", exc_info=True)
            logger.warning("Continuing in fallback mode - data will not be saved")
            # Don't use telegram_id as UUID - it will cause errors
            user_id = None
        
        # 3. Get conversation context (skip if no user_id)
        conv_service = get_conversation_service()
        if user_id is not None:
            conversation_context = await conv_service.get_conversation_context(user_id)
        else:
            # Fallback mode: no conversation history
            conversation_context = []
            logger.info("Using empty conversation context (fallback mode)")
        
        # 4. Save user message to history (skip if no user_id)
        if user_id is not None:
            await conv_service.add_message(
                user_id=user_id,
                role="user",
                content=message_text,
                telegram_id=user_telegram.id
            )
        else:
            logger.info("Skipping message save (fallback mode)")
        
        # 5. NEW: Classify intents
        ai_service = get_ai_service()
        intent_result = await ai_service.classify_intent(message_text)
        intents = intent_result.get("intents", [])
        
        # 6. NEW: Process intents and create entities
        created_entities = []
        if intents:
            intent_processor = get_intent_processor()
            created_entities = await intent_processor.process_intents(
                intents=intents,
                message=message_text,
                user_id=user_id
            )
            logger.info(f"Created {len(created_entities)} entities from intents")
        
        # 7. NEW: Build confirmations
        response_builder = get_response_builder()
        confirmations = response_builder.build_confirmation(created_entities)
        
        # 8. Generate AI response with confirmations
        system_prompt = None
        if confirmations:
            system_prompt = f"""
Ты только что выполнил следующие действия для пользователя:
{confirmations}

Ответь естественно, подтверждая выполненные действия. Будь дружелюбным и кратким.
"""
        
        response = await ai_service.generate_response(
            user_message=message_text,
            conversation_context=conversation_context,
            system_prompt=system_prompt
        )
        
        logger.info(f"Generated response for user {user_telegram.id} (length: {len(response)})")
        
        # 9. Save assistant response to history (skip if no user_id)
        if user_id is not None:
            await conv_service.add_message(
                user_id=user_id,
                role="assistant",
                content=response,
                telegram_id=user_telegram.id
            )
        else:
            logger.info("Skipping response save (fallback mode)")
        
        # 10. Send reply to user
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
    """Handle voice messages with transcription and processing.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    start_time = time.time()
    
    try:
        user = update.effective_user
        voice = update.message.voice
        
        logger.info(f"Received voice message from user {user.id} (duration: {voice.duration}s)")
        
        # 1. Send "typing" indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # 2. Download voice file with timeout
        try:
            voice_file = await context.bot.get_file(voice.file_id)
            audio_bytes = await asyncio.wait_for(
                voice_file.download_as_bytearray(),
                timeout=VOICE_DOWNLOAD_TIMEOUT
            )
            logger.info(f"Downloaded voice file: {len(audio_bytes)} bytes")
        except asyncio.TimeoutError:
            logger.error(f"Voice download timeout after {VOICE_DOWNLOAD_TIMEOUT}s")
            await update.message.reply_text(
                "Не удалось скачать голосовое сообщение (таймаут). Попробуйте еще раз."
            )
            return
        except Exception as e:
            logger.error(f"Failed to download voice file: {e}")
            await update.message.reply_text(
                "Не удалось скачать голосовое сообщение. Попробуйте еще раз."
            )
            return
        
        # 3. Transcribe with Yandex SpeechKit with timeout
        try:
            speech_kit = get_yandex_speech_kit()
            transcription = await asyncio.wait_for(
                speech_kit.transcribe_audio(bytes(audio_bytes)),
                timeout=VOICE_TRANSCRIPTION_TIMEOUT
            )
            
            if not transcription or not transcription.strip():
                logger.warning("Empty transcription result")
                await update.message.reply_text(
                    "Не удалось распознать речь. Попробуйте говорить четче или отправьте текстом."
                )
                return
            
            logger.info(f"Transcription successful: '{transcription[:50]}...'")
            
        except asyncio.TimeoutError:
            logger.error(f"Transcription timeout after {VOICE_TRANSCRIPTION_TIMEOUT}s")
            await update.message.reply_text(
                "Распознавание речи заняло слишком много времени. Попробуйте короче или отправьте текстом."
            )
            return
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            await update.message.reply_text(
                "Произошла ошибка при распознавании речи. Попробуйте позже."
            )
            return
        
        # 4. Show transcription to user
        await update.message.reply_text(
            f"🎤 Распознано: \"{transcription}\"\n\nОбрабатываю..."
        )
        
        # 5. Process as text message
        try:
            mock_update = create_mock_text_update(update, transcription)
            await handle_text_message(mock_update, context)
        except Exception as e:
            logger.error(f"Failed to process transcribed message: {e}")
            await update.message.reply_text(
                "Распознал, но не смог обработать. Попробуйте еще раз."
            )
        
        # Log total processing time
        elapsed_time = time.time() - start_time
        logger.info(f"Voice message processed in {elapsed_time:.2f}s")
        
    except Exception as e:
        # Handle any unexpected errors
        logger.error(f"Voice message processing failed for user {update.effective_user.id}: {e}", exc_info=True)
        
        try:
            await update.message.reply_text(
                "Произошла ошибка при обработке голосового сообщения. Попробуйте позже."
            )
        except Exception as reply_error:
            logger.error(f"Failed to send error message: {reply_error}")
            return
        
        # 3. Transcribe with Yandex SpeechKit with timeout
        try:
            speech_kit = get_yandex_speech_kit()
            transcription = await asyncio.wait_for(
                speech_kit.transcribe_audio(bytes(audio_bytes)),
                timeout=VOICE_TRANSCRIPTION_TIMEOUT
            )
            
            if not transcription or not transcription.strip():
                logger.warning("Empty transcription result")
                await update.message.reply_text(
                    "Не удалось распознать речь. Попробуйте говорить четче или отправьте текстом."
                )
                return
            
            logger.info(f"Transcription successful: '{transcription[:50]}...'")
            
        except asyncio.TimeoutError:
            logger.error(f"Transcription timeout after {VOICE_TRANSCRIPTION_TIMEOUT}s")
            await update.message.reply_text(
                "Распознавание речи заняло слишком много времени. Попробуйте короче или отправьте текстом."
            )
            return
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            await update.message.reply_text(
                "Произошла ошибка при распознавании речи. Попробуйте позже."
            )
            return
        
        # 4. Show transcription to user
        await update.message.reply_text(
            f"🎤 Распознано: \"{transcription}\"\n\nОбрабатываю..."
        )
        
        # 5. Process as text message
        try:
            mock_update = create_mock_text_update(update, transcription)
            await handle_text_message(mock_update, context)
        except Exception as e:
            logger.error(f"Failed to process transcribed message: {e}")
            await update.message.reply_text(
                "Распознал, но не смог обработать. Попробуйте еще раз."
            )
        
        # Log total processing time
        elapsed_time = time.time() - start_time
        logger.info(f"Voice message processed in {elapsed_time:.2f}s")
        
    except Exception as e:
        # Handle any unexpected errors
        logger.error(f"Voice message processing failed for user {update.effective_user.id}: {e}", exc_info=True)
        
        try:
            await update.message.reply_text(
                "Произошла ошибка при обработке голосового сообщения. Попробуйте позже."
            )
        except Exception as reply_error:
            logger.error(f"Failed to send error message: {reply_error}")

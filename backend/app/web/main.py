from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import logging
from telegram import Update

# Import AI functions from bot handlers
from app.bot.handlers import get_ai_response, get_fallback_response
from app.shared.config import settings
from app.shared.supabase import get_supabase_client, supabase_available

# Import Telegram bot application
from app.bot import application

# Import API routers
from .routers import (
    auth_router,
    notes_router,
    tasks_router,
    assistant_router,
    finances_router,
    personal_router,
    health_router,
    dashboard_router,
)

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(title="MISIX Backend", version="0.1.0")

    # Add CORS middleware for frontend
    default_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "https://misix.netlify.app",
    ]
    configured_origins = settings.frontend_allowed_origins or []
    allowed_origins = [
        origin
        for origin in default_origins + configured_origins
        if origin
    ]

    # Extra safety net for Netlify deploy previews and subdomains
    netlify_origin_regex = r"https://[\w.-]*netlify\.app"

    logger.info("Configured CORS origins: %s", allowed_origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(dict.fromkeys(allowed_origins)),  # Preserve order, remove duplicates
        allow_origin_regex=netlify_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "misix-backend"}

    # Telegram bot webhook (if needed)
    # app.include_router(bot_router, prefix="/bot", tags=["telegram"])

    # Telegram bot webhook endpoint
    @app.post("/bot/webhook")
    async def bot_webhook(request: Request) -> Response:
        """Handle Telegram bot webhook requests."""
        try:
            # Get the JSON data from Telegram
            data = await request.json()

            if not application.initialized:
                await application.initialize()
            if not application.running:
                await application.start()

            # Process the update with the bot application
            update = Update.de_json(data, application.bot)
            await application.process_update(update)

            return Response(status_code=200)
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return Response(status_code=500)

    # Voice transcription endpoint for web app
    @app.post("/api/voice/transcribe")
    async def transcribe_voice(request: Request) -> dict:
        """Transcribe voice audio for web app."""
        try:
            form = await request.form()
            audio_file = form.get("audio")

            if not audio_file:
                return {"error": "No audio file provided"}

            # Convert to bytes
            audio_data = await audio_file.read()

            # Import speech kit
            from app.bot.yandex_speech import get_yandex_speech_kit

            speech_kit = get_yandex_speech_kit()
            transcription = await speech_kit.transcribe_audio(audio_data)

            if transcription:
                return {"transcription": transcription}
            else:
                return {"error": "Failed to transcribe audio"}

        except Exception as e:
            logger.error(f"Voice transcription API error: {e}")
            return {"error": "Transcription failed"}

    # Chat endpoint for web app
    @app.post("/api/chat")
    async def chat_with_ai(request: Request) -> dict:
        """Chat with AI assistant for web app."""
        try:
            data = await request.json()
            message = data.get("message")
            user_id = data.get("user_id")

            if not message or not user_id:
                return {"error": "Message and user_id required"}

            # Simple response for now
            return {
                "status": "Message received",
                "message": f"🤖 Сообщение получено: {message}",
                "user_id": user_id
            }

        except Exception as e:
            logger.error(f"Chat API error: {e}")
            return {"error": "Chat failed"}

    # Assistant messages endpoint with proper AI integration
    @app.post("/api/assistant/send-message")
    async def send_assistant_message(request: Request) -> dict:
        """Send message to AI assistant with proper Yandex GPT integration."""
        try:
            data = await request.json()
            message = data.get("message", "").strip()
            user_id = data.get("user_id")

            logger.info(f"Received message: {message} from user: {user_id}")

            if not message or not user_id:
                return {"error": "Message and user_id required"}

            # Log user message to database
            if supabase_available():
                try:
                    supabase = get_supabase_client()
                    supabase.table("assistant_messages").insert({
                        "user_id": user_id,
                        "role": "user",
                        "content": message
                    }).execute()
                except Exception as log_error:
                    logger.warning(f"Failed to log user message: {log_error}")

            # Get conversation history for context
            conversation_history = []
            if supabase_available():
                try:
                    from app.bot.handlers import get_conversation_history
                    conversation_history = await get_conversation_history(user_id, limit=20)
                except Exception as hist_error:
                    logger.warning(f"Failed to get conversation history: {hist_error}")

            # Get AI response using Yandex GPT with conversation context
            try:
                response_message = await get_ai_response(message, conversation_history)
            except Exception as ai_error:
                logger.warning(f"AI failed, using fallback: {ai_error}")
                response_message = get_fallback_response(message)

            # Log assistant response to database
            if supabase_available():
                try:
                    supabase = get_supabase_client()
                    supabase.table("assistant_messages").insert({
                        "user_id": user_id,
                        "role": "assistant",
                        "content": response_message
                    }).execute()
                except Exception as log_error:
                    logger.warning(f"Failed to log assistant response: {log_error}")

            # Process and save structured data (tasks, notes, finances, etc.)
            try:
                from app.bot.handlers import process_and_save_structured_data
                # Create a mock message object for compatibility
                class MockMessage:
                    def __init__(self, text):
                        self.text = text

                mock_message = MockMessage(message)
                await process_and_save_structured_data(mock_message, user_id, message)
            except Exception as struct_error:
                logger.warning(f"Failed to process structured data: {struct_error}")

            logger.info(f"Generated response: {response_message}")

            return {
                "status": "Message processed",
                "message": response_message,
                "user_id": user_id
            }

        except Exception as e:
            logger.error(f"Send message API error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": f"Send message failed: {str(e)}"}

    # Get messages for web app
    @app.get("/api/messages")
    async def get_messages(user_id: str) -> dict:
        """Get chat messages for web app."""
        try:
            from app.shared.supabase import get_supabase_client
            supabase = get_supabase_client()

            response = supabase.table("assistant_messages")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(50)\
                .execute()

            messages = response.data or []
            return {"messages": messages[::-1]}  # Reverse to chronological order

        except Exception as e:
            logger.error(f"Get messages API error: {e}")
            return {"error": "Failed to get messages"}

    # Authentication
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

    # Web API endpoints
    app.include_router(notes_router, prefix="/api", tags=["notes"])
    app.include_router(tasks_router, prefix="/api", tags=["tasks"])
    app.include_router(assistant_router, prefix="/api", tags=["assistant"])
    app.include_router(finances_router, prefix="/api", tags=["finances"])
    app.include_router(personal_router, prefix="/api", tags=["personal"])
    app.include_router(health_router, prefix="/api", tags=["health"])
    app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])

    return app


app = create_app()

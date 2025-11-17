from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update

# Configure logging first
from app.core.logging import configure_logging, get_logger
configure_logging()

logger = get_logger(__name__)

# Import new service layer
from app.services.ai_service import get_ai_service
from app.services.conversation_service import get_conversation_service
from app.repositories.user import get_user_repository
from app.shared.config import settings
from app.shared.supabase import get_supabase_client, supabase_available

# Import Telegram bot application
from app.bot import application, start_bot_with_scheduler, stop_bot_with_scheduler

# Import new auth router
from app.api.routers.auth import router as new_auth_router

# Import API routers (legacy)
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with proper startup and shutdown."""
    # ========================================================================
    # STARTUP
    # ========================================================================
    logger.info("🚀 Starting MISIX application...")
    
    # Start Telegram bot
    if application:
        try:
            if not getattr(application, "_initialized", False):
                await application.initialize()
                logger.info("✅ Telegram bot initialized")
            
            if not getattr(application, "_running", False):
                await application.start()
                logger.info("✅ Telegram bot started")
            
            # Start scheduler for reminders
            try:
                start_bot_with_scheduler()
                logger.info("✅ Scheduler started successfully")
            except Exception as e:
                logger.error(f"⚠️  Failed to start scheduler: {e}", exc_info=True)
                logger.warning("Continuing without scheduler - reminders will not work")
        
        except Exception as e:
            logger.error(f"❌ Failed to start Telegram bot: {e}", exc_info=True)
            logger.warning("Continuing without Telegram bot")
    else:
        logger.info("ℹ️  Telegram bot not configured (TELEGRAM_BOT_TOKEN not set)")
    
    logger.info("✅ MISIX application started successfully")
    
    yield
    
    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    logger.info("🛑 Shutting down MISIX application...")
    
    # Stop scheduler
    if application:
        try:
            stop_bot_with_scheduler()
            logger.info("✅ Scheduler stopped")
        except Exception as e:
            logger.error(f"⚠️  Error stopping scheduler: {e}")
    
    # Stop Telegram bot
    if application:
        try:
            if getattr(application, "_running", False):
                await application.stop()
                logger.info("✅ Telegram bot stopped")
            
            if getattr(application, "_initialized", False):
                await application.shutdown()
                logger.info("✅ Telegram bot shutdown complete")
        except Exception as e:
            logger.error(f"⚠️  Error stopping Telegram bot: {e}")
    
    logger.info("✅ MISIX application shutdown complete")

def create_app() -> FastAPI:
    app = FastAPI(
        title="MISIX Backend",
        version="1.0.0",
        description="AI Personal Assistant API",
        docs_url="/docs" if not settings.is_production else None,  # Disable docs in production
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,  # Use lifespan context manager
    )

    # ========================================================================
    # CORS Configuration (Secure)
    # ========================================================================
    
    # Get allowed origins from configuration
    allowed_origins = settings.get_cors_origins()
    
    # In production, never allow wildcard
    if settings.is_production and "*" in allowed_origins:
        logger.error("Wildcard CORS origin not allowed in production!")
        raise ValueError("Wildcard CORS origin not allowed in production")
    
    # Log CORS configuration
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"CORS allowed origins: {allowed_origins}")
    
    # Configure CORS middleware
    cors_config = {
        "allow_origins": allowed_origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": [
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "User-Agent",
            "DNT",
            "Cache-Control",
            "X-Requested-With",
        ],
        "expose_headers": [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After",
        ],
        "max_age": 600,  # Cache preflight requests for 10 minutes
    }
    
    # Add origin regex for Netlify deploy previews (only in non-production)
    if not settings.is_production:
        cors_config["allow_origin_regex"] = r"https://[\w.-]*netlify\.app"
    
    app.add_middleware(CORSMiddleware, **cors_config)
    
    # ========================================================================
    # Request Logging Middleware
    # ========================================================================
    
    from app.middleware.logging import RequestLoggingMiddleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # ========================================================================
    # Rate Limiting Middleware
    # ========================================================================
    
    from app.middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)
    
    # ========================================================================
    # Error Handlers
    # ========================================================================
    
    from app.middleware.error_handler import register_exception_handlers
    register_exception_handlers(app)

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "misix-backend"}

    # Telegram bot webhook (if needed)
    # app.include_router(bot_router, prefix="/bot", tags=["telegram"])

    # Lifecycle management moved to lifespan context manager above

    # Telegram bot webhook endpoint
    @app.post("/bot/webhook")
    async def bot_webhook(request: Request) -> Response:
        """Handle Telegram bot webhook requests."""
        try:
            # Get the JSON data from Telegram
            data = await request.json()

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

            # Get conversation service
            conv_service = get_conversation_service()
            
            # Get conversation context
            conversation_context = await conv_service.get_conversation_context(user_id)
            
            # Save user message
            await conv_service.add_message(
                user_id=user_id,
                role="user",
                content=message
            )

            # Get AI response using new service
            ai_service = get_ai_service()
            response_message = await ai_service.generate_response(
                user_message=message,
                conversation_context=conversation_context
            )
            
            # Save assistant response
            await conv_service.add_message(
                user_id=user_id,
                role="assistant",
                content=response_message
            )

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

    # Authentication (New secure implementation)
    app.include_router(new_auth_router, prefix="/api/v2/auth", tags=["auth-v2"])
    
    # Authentication (Legacy - will be deprecated)
    app.include_router(auth_router, prefix="/api/auth", tags=["auth-legacy"])

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

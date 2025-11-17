# Design Document: MISIX Critical Issues Fix

## Overview

This design addresses critical architectural gaps in MISIX by integrating existing components into a cohesive message processing pipeline, implementing proper database migration management, and adding essential production features. The solution leverages existing code (IntentProcessor, ExtractionService, ResponseBuilder) and connects them into the main message flow.

## Architecture

### High-Level Flow

```
User Message (Text/Voice)
    ↓
[Message Handler]
    ↓
[Intent Classification] ← AI Service
    ↓
[Intent Processor]
    ↓
┌─────────┬──────────┬──────────┬──────────┐
│ Task    │ Finance  │ Note     │ Mood     │
│ Handler │ Handler  │ Handler  │ Handler  │
└─────────┴──────────┴──────────┴──────────┘
    ↓
[Extraction Service] ← AI Service
    ↓
[Create Entities] → Database
    ↓
[Response Builder]
    ↓
[Send to User]
```

### Component Integration

```
┌─────────────────────────────────────────┐
│         Message Handler                  │
│  (backend/app/bot/handlers/message.py)  │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│          AI Service                      │
│  - classify_intent()                     │
│  - generate_response()                   │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       Intent Processor                   │
│  - process_intents()                     │
│  - _handle_create_task()                 │
│  - _handle_finance()                     │
│  - _handle_save_note()                   │
│  - _handle_track_mood()                  │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      Extraction Service                  │
│  - extract_task_data()                   │
│  - extract_finance_data()                │
│  - extract_note_data()                   │
│  - extract_mood_data()                   │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       Response Builder                   │
│  - build_response()                      │
│  - format_entities()                     │
└─────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Enhanced Message Handler

**File:** `backend/app/bot/handlers/message.py`

**Current State:**
- Only generates AI responses
- Doesn't process intents
- Doesn't create entities

**New Design:**

```python
async def handle_text_message(update, context):
    """Process text message with intent classification."""
    user_id = str(update.effective_user.id)
    message = update.message.text
    
    # Step 1: Classify intents
    ai_service = get_ai_service()
    intent_result = await ai_service.classify_intent(message)
    intents = intent_result.get("intents", [])
    
    # Step 2: Process intents and create entities
    created_entities = []
    if intents:
        intent_processor = get_intent_processor()
        created_entities = await intent_processor.process_intents(
            intents=intents,
            message=message,
            user_id=user_id
        )
    
    # Step 3: Build response
    if created_entities:
        # Format entity confirmations
        response_builder = get_response_builder()
        response = response_builder.build_response(created_entities)
    else:
        # Generate conversational response
        conversation_service = get_conversation_service()
        context_text = await conversation_service.get_context(user_id)
        response = await ai_service.generate_response(
            user_message=message,
            conversation_context=context_text
        )
    
    # Step 4: Save conversation
    await conversation_service.save_message(user_id, message, response)
    
    # Step 5: Send response
    await update.message.reply_text(response)
```

**Key Changes:**
- Add intent classification before AI response
- Process intents to create entities
- Use ResponseBuilder for entity confirmations
- Fallback to conversational AI if no entities

### 2. Voice Message Integration

**File:** `backend/app/bot/handlers/message.py`

**Design:**

```python
async def handle_voice_message(update, context):
    """Process voice message with transcription and intent classification."""
    user_id = str(update.effective_user.id)
    
    # Step 1: Transcribe voice
    try:
        text = await transcribe_voice_message(update.message.voice)
        await update.message.reply_text(f"🎤 Распознано: \"{text}\"")
    except Exception as e:
        logger.error(f"Voice transcription failed: {e}")
        await update.message.reply_text(
            "Извините, не удалось распознать голосовое сообщение. "
            "Попробуйте еще раз или напишите текстом."
        )
        return
    
    # Step 2: Process as text message
    # (Reuse text message logic)
    await process_message_text(update, context, text, is_voice=True)
```

### 3. Scheduler Lifecycle Integration

**File:** `backend/app/web/main.py`

**Current State:**
- Scheduler initialized but not started
- No lifecycle hooks

**New Design:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting MISIX application...")
    
    # Start Telegram bot
    if telegram_app:
        await start_telegram_application(telegram_app)
        logger.info("Telegram bot started")
    
    # Start scheduler
    from app.bot import start_bot_with_scheduler
    start_bot_with_scheduler()
    logger.info("Scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MISIX application...")
    
    # Stop scheduler
    from app.bot import stop_bot_with_scheduler
    stop_bot_with_scheduler()
    logger.info("Scheduler stopped")
    
    # Stop Telegram bot
    if telegram_app:
        await stop_telegram_application(telegram_app)
        logger.info("Telegram bot stopped")

app = FastAPI(lifespan=lifespan)
```

### 4. Database Migration System

**Tool:** Alembic

**Structure:**
```
backend/
├── alembic/
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_mood_entries.py
│   │   ├── 003_add_reminders.py
│   │   └── 004_add_indexes.py
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
└── migrations/  # Old migrations (archive)
```

**Configuration:**

```python
# alembic/env.py
from app.core.config import settings
from app.shared.supabase import get_supabase_client

def get_url():
    """Get database URL from Supabase."""
    client = get_supabase_client()
    # Extract connection string
    return f"postgresql://{settings.supabase_url}/postgres"
```

**Commands:**
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Show history
alembic history
```

### 5. Rate Limiting Integration

**File:** `backend/app/web/main.py`

**Design:**

```python
from app.middleware.rate_limit import RateLimitMiddleware

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    redis_url=settings.redis_url,
    default_limit=settings.rate_limit_per_minute,
    auth_limit=settings.rate_limit_auth_per_minute,
)
```

**Middleware Logic:**

```python
class RateLimitMiddleware:
    def __init__(self, app, redis_url=None, default_limit=60, auth_limit=5):
        self.app = app
        self.redis_client = redis.from_url(redis_url) if redis_url else None
        self.default_limit = default_limit
        self.auth_limit = auth_limit
        self.memory_store = {}  # Fallback
    
    async def __call__(self, request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Determine limit
        is_auth = request.url.path.startswith("/api/v2/auth")
        limit = self.auth_limit if is_auth else self.default_limit
        
        # Check rate limit
        if not await self.check_rate_limit(client_ip, limit):
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"},
                headers={"Retry-After": "60"}
            )
        
        return await call_next(request)
```

### 6. Configuration Consolidation

**Strategy:**
1. Keep `app.core.config` as the single source of truth
2. Create deprecation wrapper in `app.shared.config`
3. Migrate all imports gradually
4. Remove `app.shared.config` in future release

**File:** `app.shared.config.py`

```python
"""DEPRECATED: Use app.core.config instead."""
import warnings
from app.core.config import settings as _settings

warnings.warn(
    "app.shared.config is deprecated. Use app.core.config instead.",
    DeprecationWarning,
    stacklevel=2
)

settings = _settings
```

### 7. Enhanced Logging

**File:** `backend/app/core/logging.py`

**Design:**

```python
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(log_level: str = "INFO", log_format: str = "json"):
    """Configure application logging."""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Create formatter
    if log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s '
            '%(request_id)s %(user_id)s %(duration_ms)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

## Data Models

### Intent Classification Result

```python
{
    "intents": [
        {
            "type": "create_task",
            "confidence": 0.95
        },
        {
            "type": "add_expense",
            "confidence": 0.85
        }
    ]
}
```

### Created Entity

```python
{
    "type": "task",  # or "finance", "note", "mood"
    "data": {
        "id": "uuid",
        "title": "купить молоко",
        "deadline": "2025-11-18T09:00:00Z",
        "priority": "medium",
        "status": "new"
    },
    "title": "купить молоко",
    "deadline": "2025-11-18T09:00:00Z"
}
```

## Error Handling

### Error Recovery Strategy

```python
try:
    # Try intent-based processing
    intents = await ai_service.classify_intent(message)
    entities = await intent_processor.process_intents(intents, message, user_id)
    response = response_builder.build_response(entities)
except AIServiceError:
    # AI unavailable - use fallback
    logger.warning("AI service unavailable, using fallback")
    response = "Извините, сейчас я не могу обработать ваш запрос."
except DatabaseError as e:
    # Database error - inform user
    logger.error(f"Database error: {e}")
    response = "Произошла ошибка при сохранении данных. Попробуйте позже."
except Exception as e:
    # Unknown error - log and continue
    logger.error(f"Unexpected error: {e}", exc_info=True)
    response = "Произошла непредвиденная ошибка. Мы уже работаем над исправлением."
```

### Graceful Degradation

1. **AI Service Down**: Use keyword-based fallback responses
2. **Database Down**: Queue operations for retry, inform user
3. **Scheduler Down**: Log error, continue bot operation
4. **Redis Down**: Use in-memory rate limiting

## Testing Strategy

### Unit Tests

**Coverage Target:** 50%

**Priority Areas:**
1. Intent classification logic
2. Entity extraction
3. Response building
4. Error handling

**Example:**

```python
@pytest.mark.asyncio
async def test_message_handler_with_task_intent():
    """Test message handler creates task from intent."""
    # Arrange
    mock_ai = create_mock_ai_service()
    mock_ai.classify_intent.return_value = {
        "intents": [{"type": "create_task", "confidence": 0.95}]
    }
    
    # Act
    response = await handle_text_message(update, context)
    
    # Assert
    assert "Создал задачу" in response
    mock_task_service.create.assert_called_once()
```

### Integration Tests

**Critical Flows:**
1. Text message → Task creation → Confirmation
2. Voice message → Transcription → Expense creation
3. Multiple intents → Multiple entities → Combined response
4. AI failure → Fallback response

### Performance Tests

**Targets:**
- Message processing: < 2 seconds
- Intent classification: < 1 second
- Database operations: < 500ms

## Deployment Strategy

### Phase 1: Core Integration (Week 1)
1. Integrate intent processing into message handler
2. Add scheduler lifecycle management
3. Deploy to staging
4. Test with real users

### Phase 2: Infrastructure (Week 2)
1. Set up Alembic migrations
2. Migrate existing SQL files
3. Add rate limiting
4. Consolidate configuration

### Phase 3: Monitoring (Week 3)
1. Enhanced logging
2. Error tracking
3. Performance monitoring
4. Deploy to production

### Rollback Plan

If critical issues occur:
1. Revert to previous message handler (AI-only responses)
2. Disable scheduler if causing issues
3. Remove rate limiting if blocking legitimate traffic
4. Keep database migrations (forward-only)

## Security Considerations

1. **Rate Limiting**: Prevent API abuse and cost overruns
2. **Input Validation**: Sanitize all user inputs before processing
3. **Error Messages**: Don't expose internal details to users
4. **Logging**: Don't log sensitive user data (passwords, tokens)
5. **Database**: Use parameterized queries (already implemented)

## Performance Optimizations

1. **Caching**: Cache AI responses for common queries
2. **Async Processing**: All I/O operations are async
3. **Connection Pooling**: Reuse database connections
4. **Batch Operations**: Process multiple intents in parallel
5. **Lazy Loading**: Load conversation context only when needed

## Monitoring and Observability

### Key Metrics

1. **Message Processing Time**: p50, p95, p99
2. **Intent Classification Accuracy**: % of successful classifications
3. **Entity Creation Rate**: Tasks, expenses, notes per hour
4. **Error Rate**: % of failed message processing
5. **AI Service Availability**: Uptime percentage

### Alerts

1. **High Error Rate**: > 5% of messages failing
2. **Slow Processing**: p95 > 3 seconds
3. **AI Service Down**: No successful calls in 5 minutes
4. **Database Issues**: Connection errors
5. **Scheduler Failures**: Jobs not running

## Future Enhancements

1. **Caching Layer**: Redis for AI response caching
2. **Message Queue**: RabbitMQ for async processing
3. **A/B Testing**: Test different AI prompts
4. **Analytics Dashboard**: User behavior insights
5. **Multi-language Support**: Detect and process multiple languages

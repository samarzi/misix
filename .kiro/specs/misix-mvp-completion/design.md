# Design Document: MISIX MVP Completion

## Overview

Этот документ описывает архитектурное решение для завершения MVP проекта MISIX. Дизайн фокусируется на создании полноценного естественного общения с автоматическим извлечением данных, интеграции всех модулей и улучшении пользовательского опыта.

### Goals

1. Реализовать автоматическое извлечение структурированных данных из естественного языка
2. Интегрировать все модули (задачи, финансы, заметки, настроение) с Telegram ботом
3. Обеспечить полноценную работу голосовых сообщений
4. Создать систему напоминаний о задачах
5. Улучшить веб-дашборд с визуализацией данных
6. Достичь test coverage > 70%

### Non-Goals

- Модуль "Здоровье" (отложен на следующую итерацию)
- Модуль "Хранилище" с шифрованием (отложен)
- Расширенный профиль пользователя (отложен)
- Выбор тона общения (отложен)

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interfaces                       │
├──────────────────────────┬──────────────────────────────────┤
│   Telegram Bot           │      Web Dashboard               │
│   (text + voice)         │      (React + TypeScript)        │
└──────────┬───────────────┴──────────────┬───────────────────┘
           │                               │
           │                               │
┌──────────▼───────────────────────────────▼───────────────────┐
│                    FastAPI Backend                            │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Message Processing Pipeline                │    │
│  │                                                       │    │
│  │  1. Message Handler                                  │    │
│  │  2. Intent Classifier (Yandex GPT)                   │    │
│  │  3. Intent Router                                    │    │
│  │  4. Data Extractor (Yandex GPT)                      │    │
│  │  5. Service Layer (create entities)                  │    │
│  │  6. Response Builder                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Service Layer                           │    │
│  │  - AIService (intent + extraction)                   │    │
│  │  - TaskService                                       │    │
│  │  - FinanceService                                    │    │
│  │  - NoteService                                       │    │
│  │  - MoodService                                       │    │
│  │  - ConversationService                               │    │
│  │  - ReminderService                                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Repository Layer                           │    │
│  │  - BaseRepository (CRUD + pagination)                │    │
│  │  - TaskRepository                                    │    │
│  │  - FinanceRepository                                 │    │
│  │  - NoteRepository                                    │    │
│  │  - MoodRepository                                    │    │
│  │  - UserRepository                                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                    External Services                          │
├───────────────────────────────────────────────────────────────┤
│  - Supabase (PostgreSQL)                                      │
│  - Yandex GPT (intent classification + data extraction)       │
│  - Yandex SpeechKit (voice transcription)                     │
│  - APScheduler (task reminders)                               │
└───────────────────────────────────────────────────────────────┘
```

### Message Processing Flow

```
User Message (text/voice)
    │
    ▼
┌─────────────────────┐
│  Message Handler    │
│  - Validate input   │
│  - Get user context │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Voice Processing?   │
│ (if voice message)  │
│ - Download audio    │
│ - Transcribe        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Intent Classifier   │
│ (Yandex GPT)        │
│ - Analyze message   │
│ - Return intents[]  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Intent Router      │
│ - Filter by conf.   │
│ - Route to handlers │
└──────────┬──────────┘
           │
           ├─────────────────┬─────────────────┬─────────────────┐
           ▼                 ▼                 ▼                 ▼
    ┌──────────┐      ┌──────────┐     ┌──────────┐     ┌──────────┐
    │  Task    │      │ Finance  │     │   Note   │     │   Mood   │
    │ Handler  │      │ Handler  │     │ Handler  │     │ Handler  │
    └────┬─────┘      └────┬─────┘     └────┬─────┘     └────┬─────┘
         │                 │                 │                 │
         ▼                 ▼                 ▼                 ▼
    ┌──────────┐      ┌──────────┐     ┌──────────┐     ┌──────────┐
    │   Data   │      │   Data   │     │   Data   │     │   Data   │
    │Extractor │      │Extractor │     │Extractor │     │Extractor │
    └────┬─────┘      └────┬─────┘     └────┬─────┘     └────┬─────┘
         │                 │                 │                 │
         ▼                 ▼                 ▼                 ▼
    ┌──────────┐      ┌──────────┐     ┌──────────┐     ┌──────────┐
    │  Task    │      │ Finance  │     │   Note   │     │   Mood   │
    │ Service  │      │ Service  │     │ Service  │     │ Service  │
    └────┬─────┘      └────┬─────┘     └────┬─────┘     └────┬─────┘
         │                 │                 │                 │
         └─────────────────┴─────────────────┴─────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │ Response Builder│
                          │ - Format reply  │
                          │ - Add emojis    │
                          └────────┬────────┘
                                   │
                                   ▼
                            User receives reply
```

## Components and Interfaces

### 1. Message Handler (`backend/app/bot/handlers/message.py`)

**Responsibility:** Главный обработчик всех входящих сообщений

**Interface:**
```python
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all incoming text messages."""
    
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice messages with transcription."""
```

**Key Functions:**
- Получение сообщения от пользователя
- Определение типа сообщения (текст/голос)
- Получение или создание пользователя
- Вызов intent classification
- Маршрутизация к соответствующим обработчикам
- Отправка ответа пользователю

### 2. Intent Processor (`backend/app/bot/intent_processor.py`)

**Responsibility:** Обработка классифицированных намерений

**Interface:**
```python
class IntentProcessor:
    async def process_intents(
        self,
        intents: List[dict],
        message: str,
        user_id: str
    ) -> List[dict]:
        """Process list of intents and create entities."""
    
    async def _process_single_intent(
        self,
        intent_type: str,
        message: str,
        user_id: str
    ) -> Optional[dict]:
        """Process single intent."""
```

**Supported Intents:**
- `create_task` → TaskService
- `add_expense` → FinanceService
- `add_income` → FinanceService
- `save_note` → NoteService
- `track_mood` → MoodService
- `general_chat` → AIService (conversational response)

### 3. Extraction Service (`backend/app/services/extraction_service.py`)

**Responsibility:** Извлечение структурированных данных из текста

**Interface:**
```python
class ExtractionService:
    async def extract_task_data(self, message: str) -> Optional[dict]:
        """Extract task information from message."""
        # Returns: {title, description, deadline, priority}
    
    async def extract_finance_data(self, message: str) -> Optional[dict]:
        """Extract finance information from message."""
        # Returns: {amount, type, category, description}
    
    async def extract_note_data(self, message: str) -> Optional[dict]:
        """Extract note information from message."""
        # Returns: {title, content}
    
    async def extract_mood_data(self, message: str) -> Optional[dict]:
        """Extract mood information from message."""
        # Returns: {mood, intensity, note}
```

**Implementation:**
- Использует Yandex GPT для извлечения данных
- Промпты оптимизированы для русского языка
- Возвращает JSON с структурированными данными
- Обрабатывает ошибки парсинга

### 4. Response Builder (`backend/app/bot/response_builder.py`)

**Responsibility:** Формирование красивых ответов пользователю

**Interface:**
```python
class ResponseBuilder:
    def build_task_created(self, task: dict) -> str:
        """Build response for created task."""
    
    def build_finance_created(self, finance: dict) -> str:
        """Build response for created finance entry."""
    
    def build_note_created(self, note: dict) -> str:
        """Build response for created note."""
    
    def build_mood_saved(self, mood: dict) -> str:
        """Build response for saved mood."""
    
    def build_multiple_entities(self, entities: List[dict]) -> str:
        """Build response for multiple created entities."""
```

**Features:**
- Использует эмодзи для наглядности
- Форматирует даты и суммы
- Группирует множественные действия
- Добавляет контекстные подсказки

### 5. Command Handlers (`backend/app/bot/handlers/command.py`)

**Responsibility:** Обработка команд бота

**Commands:**
```python
async def start_command(update, context):
    """Handle /start command - onboarding."""

async def help_command(update, context):
    """Handle /help command - show available commands."""

async def tasks_command(update, context):
    """Handle /tasks command - show user tasks."""

async def finances_command(update, context):
    """Handle /finances command - show finance summary."""

async def mood_command(update, context):
    """Handle /mood command - show mood history."""

async def settings_command(update, context):
    """Handle /settings command - user settings."""

async def reminders_command(update, context):
    """Handle /reminders command - reminder settings."""
```

### 6. Reminder Service (`backend/app/services/reminder_service.py`)

**Responsibility:** Управление напоминаниями о задачах

**Interface:**
```python
class ReminderService:
    async def check_upcoming_tasks(self) -> List[dict]:
        """Check for tasks with upcoming deadlines."""
    
    async def send_task_reminder(self, task: dict, user: dict) -> bool:
        """Send reminder for specific task."""
    
    async def send_daily_summary(self, user_id: str) -> bool:
        """Send daily task summary."""
    
    async def get_user_settings(self, user_id: str) -> dict:
        """Get reminder settings for user."""
```

**Scheduler Jobs:**
- Check tasks every 5 minutes
- Send reminders 1 hour before deadline
- Send reminders at deadline time
- Send daily summary at 9:00 AM

### 7. Voice Processing (`backend/app/bot/yandex_speech.py`)

**Responsibility:** Транскрипция голосовых сообщений

**Interface:**
```python
class YandexSpeechKit:
    async def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio to text using Yandex SpeechKit."""
```

**Features:**
- Timeout защита (30 сек)
- Обработка ошибок
- Логирование времени обработки
- Поддержка русского языка

## Data Models

### Intent Classification Response

```python
{
    "intents": [
        {
            "type": "add_expense",
            "confidence": 0.95
        },
        {
            "type": "create_task",
            "confidence": 0.85
        }
    ]
}
```

### Extracted Task Data

```python
{
    "title": "купить молоко",
    "description": None,
    "deadline": "2025-11-18T00:00:00",  # ISO 8601
    "priority": "medium"  # low/medium/high
}
```

### Extracted Finance Data

```python
{
    "amount": 500.0,
    "type": "expense",  # expense/income
    "category": "еда и напитки",
    "description": "кофе"
}
```

### Extracted Note Data

```python
{
    "title": "Встреча в офисе",
    "content": "Встреча в офисе на Ленина 5"
}
```

### Extracted Mood Data

```python
{
    "mood": "отличное",  # отличное/хорошее/нормальное/плохое/ужасное
    "intensity": 9,  # 1-10
    "note": "сегодня отличное настроение"
}
```

### Created Entity Response

```python
{
    "type": "task",  # task/finance/note/mood
    "data": {...},  # full entity object
    "title": "купить молоко",
    "deadline": "2025-11-18T00:00:00"
}
```

## Error Handling

### Error Types

1. **AI Service Errors**
   - Yandex GPT unavailable → Use fallback responses
   - Intent classification failed → Treat as general_chat
   - Data extraction failed → Ask user to rephrase

2. **Database Errors**
   - Connection failed → Retry 3 times with exponential backoff
   - Constraint violation → Return user-friendly error
   - Timeout → Queue for later processing

3. **Voice Processing Errors**
   - Download timeout (>10s) → Ask to resend
   - Transcription failed → Suggest text message
   - Audio format unsupported → Inform user

4. **Validation Errors**
   - Invalid data format → Ask for clarification
   - Missing required fields → Request additional info
   - Out of range values → Suggest valid range

### Error Response Format

```python
{
    "error": True,
    "message": "Понятное сообщение для пользователя",
    "suggestion": "Попробуйте переформулировать запрос",
    "retry": True  # Can user retry?
}
```

## Testing Strategy

### Unit Tests (Target: 70% coverage)

**Services:**
- `test_ai_service.py` - Intent classification, data extraction
- `test_extraction_service.py` - All extraction methods
- `test_task_service.py` - CRUD operations
- `test_finance_service.py` - CRUD operations
- `test_note_service.py` - CRUD operations
- `test_mood_service.py` - CRUD operations
- `test_reminder_service.py` - Reminder logic

**Repositories:**
- `test_base_repository.py` - CRUD operations
- `test_task_repository.py` - Task-specific queries
- `test_finance_repository.py` - Finance-specific queries

**Bot Handlers:**
- `test_message_handler.py` - Message processing flow
- `test_command_handler.py` - All commands
- `test_intent_processor.py` - Intent routing

### Integration Tests

**API Endpoints:**
- `test_auth_api.py` ✅ (exists)
- `test_tasks_api.py` - Task CRUD via API
- `test_finances_api.py` - Finance CRUD via API
- `test_dashboard_api.py` - Dashboard summary

**Bot Integration:**
- `test_bot_integration.py` - End-to-end message flow
- `test_voice_integration.py` - Voice message processing

### Test Data

**Sample Messages:**
```python
SAMPLE_MESSAGES = {
    "task": [
        "напомни завтра купить молоко",
        "добавь задачу позвонить партнеру",
        "нужно сделать презентацию к пятнице"
    ],
    "expense": [
        "потратил 500₽ на кофе",
        "купил продукты за 2000 рублей",
        "оплатил такси 300р"
    ],
    "income": [
        "получил зарплату 50000₽",
        "заработал 1000 рублей"
    ],
    "note": [
        "запомни что встреча в офисе на Ленина 5",
        "сохрани: пароль от wifi - 12345"
    ],
    "mood": [
        "сегодня отличное настроение",
        "чувствую себя плохо",
        "настроение на 8 из 10"
    ],
    "multiple": [
        "потратил 200₽ на такси и напомни купить молоко",
        "заработал 5000₽ и добавь задачу отправить отчет"
    ]
}
```

## Performance Optimization

### Database Indexes

```sql
-- Already implemented in 006_add_indexes.sql
CREATE INDEX idx_tasks_user_status ON tasks (user_id, status);
CREATE INDEX idx_tasks_deadline ON tasks (deadline) WHERE status != 'completed';
CREATE INDEX idx_finance_user_date ON finance_entries (user_id, date DESC);
CREATE INDEX idx_notes_user_created ON notes (user_id, created_at DESC);
CREATE INDEX idx_mood_user_created ON mood_entries (user_id, created_at DESC);
```

### Caching Strategy

```python
# User settings cache (Redis)
cache_key = f"user_settings:{user_id}"
ttl = 3600  # 1 hour

# Conversation context cache
cache_key = f"conversation:{user_id}"
ttl = 86400  # 24 hours

# Intent classification cache (for identical messages)
cache_key = f"intent:{hash(message)}"
ttl = 300  # 5 minutes
```

### Response Time Targets

- Text message processing: < 3 seconds
- Voice message processing: < 40 seconds
- API endpoint response: < 200ms
- Database query: < 100ms

## Security Considerations

### Input Validation

- Sanitize all user input before processing
- Validate extracted data before saving
- Limit message length (max 4000 chars)
- Rate limit: 100 messages/minute per user

### Data Protection

- Store user_id as UUID
- Use JWT for web authentication
- Apply CORS restrictions
- Log security events

### API Security

- Require authentication for all endpoints
- Validate JWT tokens
- Apply rate limiting
- Use HTTPS only

## Deployment Strategy

### Phase 1: Core Integration (Week 1)
1. Implement intent classification in message handler
2. Create extraction service
3. Integrate intent processor with services
4. Add response builder
5. Deploy and test with real users

### Phase 2: Voice & Commands (Week 2)
1. Implement voice transcription
2. Migrate all commands to new architecture
3. Add inline keyboards for commands
4. Deploy and test

### Phase 3: Reminders & Testing (Week 3)
1. Implement reminder service
2. Add scheduler integration
3. Write unit tests (target 70% coverage)
4. Write integration tests
5. Deploy to production

### Phase 4: Web Dashboard (Week 4)
1. Improve dashboard UI
2. Add charts and graphs
3. Implement real-time sync
4. Final testing and optimization

## Monitoring and Metrics

### Key Metrics

- **Message Processing Time**: p50, p95, p99
- **Intent Classification Accuracy**: % correct classifications
- **Data Extraction Success Rate**: % successful extractions
- **Voice Transcription Success Rate**: % successful transcriptions
- **Error Rate**: errors per 1000 messages
- **User Engagement**: messages per user per day

### Logging

```python
# Structured logging format
{
    "timestamp": "2025-11-17T10:30:00Z",
    "level": "INFO",
    "message": "Intent classified",
    "user_id": "uuid",
    "intents": [...],
    "confidence": 0.95,
    "processing_time_ms": 1234
}
```

### Alerts

- Error rate > 5% → Notify team
- Response time > 5s → Investigate
- Voice transcription failure > 20% → Check Yandex SpeechKit
- Database connection errors → Critical alert

## Migration Plan

### Remove Legacy Code

1. **Backup old handlers.py** → `handlers.py.backup`
2. **Remove imports** from main.py
3. **Test all functionality** with new handlers
4. **Delete old file** after 1 week of stable operation

### Database Migrations

All required migrations already exist:
- ✅ `005_add_reminders.sql` - Reminder support
- ✅ `006_add_indexes.sql` - Performance indexes

### Configuration Changes

No breaking changes to configuration.
All existing environment variables remain valid.

## Future Enhancements (Post-MVP)

1. **Модуль "Здоровье"** - Tracking weight, sleep, activity
2. **Расширенный профиль** - Age, city, goals
3. **Выбор тона общения** - Formal, friendly, neutral
4. **Проактивные предложения** - AI suggests actions
5. **Аналитика и инсайты** - Patterns and trends
6. **Модуль "Хранилище"** - Encrypted document storage

# Design Document

## Overview

Данный документ описывает дизайн системы обработки текстовых сообщений в Telegram боте MISIX. Система интегрирует AI сервис (Yandex GPT) для генерации интеллектуальных ответов и сервис управления историей разговоров для поддержания контекста между сообщениями.

Основная цель - заменить текущую заглушку в `handle_text_message` на полноценную обработку с использованием существующих сервисов `AIService` и `ConversationService`.

## Architecture

### High-Level Flow

```
Telegram User Message
        ↓
MessageHandler (handle_text_message)
        ↓
    ┌───┴───┐
    ↓       ↓
UserRepo  ConversationService
    ↓       ↓
    └───┬───┘
        ↓
    AIService
        ↓
  Yandex GPT API
        ↓
    Response
        ↓
ConversationService (save)
        ↓
  Telegram Reply
```

### Component Interaction

1. **MessageHandler** - точка входа, координирует весь процесс
2. **UserRepository** - получает/создает пользователя по telegram_id
3. **ConversationService** - управляет историей сообщений
4. **AIService** - генерирует ответы через Yandex GPT
5. **Telegram API** - отправляет ответ пользователю

## Components and Interfaces

### 1. MessageHandler (handle_text_message)

**Файл:** `backend/app/bot/handlers/message.py`

**Обязанности:**
- Извлечение данных из Telegram Update
- Координация между сервисами
- Обработка ошибок
- Отправка ответа пользователю

**Интерфейс:**
```python
async def handle_text_message(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle text messages from users."""
```

**Зависимости:**
- `UserRepository` - для работы с пользователями
- `ConversationService` - для истории разговоров
- `AIService` - для генерации ответов

### 2. UserRepository

**Файл:** `backend/app/repositories/user.py`

**Существующие методы:**
- `get_by_telegram_id(telegram_id: int) -> Optional[dict]` - получить пользователя
- `create(data: dict) -> dict` - создать нового пользователя (из BaseRepository)

**Новый метод (если нужен):**
```python
async def get_or_create_by_telegram_id(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
) -> dict:
    """Get existing user or create new one by Telegram ID."""
```

### 3. ConversationService

**Файл:** `backend/app/services/conversation_service.py`

**Используемые методы:**
- `get_conversation_context(user_id: str) -> str` - получить контекст
- `add_message(user_id: str, role: str, content: str, telegram_id: Optional[int]) -> None` - сохранить сообщение

**Поведение:**
- Хранит последние 6 сообщений в памяти
- Сохраняет в БД если доступна
- Возвращает контекст для AI

### 4. AIService

**Файл:** `backend/app/services/ai_service.py`

**Используемые методы:**
- `generate_response(user_message: str, conversation_context: Optional[str], system_prompt: Optional[str]) -> str`

**Поведение:**
- Использует Yandex GPT если доступен
- Fallback на keyword-based ответы если недоступен
- Включает контекст разговора в запрос

## Data Models

### User Data (from database)

```python
{
    "id": "uuid",
    "telegram_id": int,
    "username": Optional[str],
    "first_name": Optional[str],
    "last_name": Optional[str],
    "email": Optional[str],
    "created_at": datetime,
    "updated_at": datetime
}
```

### Message Data (ConversationService)

```python
{
    "role": "user" | "assistant",
    "text": str,
    "timestamp": str  # ISO format
}
```

### Telegram Update Data

```python
update.effective_user.id: int
update.effective_user.username: Optional[str]
update.effective_user.first_name: Optional[str]
update.effective_user.last_name: Optional[str]
update.message.text: str
```

## Error Handling

### Error Scenarios

1. **База данных недоступна**
   - UserRepository возвращает None
   - Создаем временного пользователя с telegram_id как строковым ID
   - Продолжаем работу с ограниченной функциональностью

2. **Yandex GPT недоступен**
   - AIService автоматически использует fallback ответы
   - Логируем предупреждение
   - Пользователь получает базовый ответ

3. **ConversationService не может сохранить**
   - Логируем предупреждение
   - Продолжаем работу (сообщение в памяти)
   - Не блокируем ответ пользователю

4. **Telegram API недоступен**
   - Логируем ошибку
   - Выбрасываем исключение (Telegram SDK обработает)

### Error Handling Strategy

```python
try:
    # Main processing logic
    user = await get_or_create_user()
    context = await get_conversation_context()
    response = await generate_ai_response()
    await save_messages()
    await send_reply()
except Exception as e:
    logger.error(f"Message processing failed: {e}")
    await send_error_message()
```

## Implementation Details

### Message Processing Flow

```python
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 1. Extract data
    user_telegram = update.effective_user
    message_text = update.message.text
    
    # 2. Get or create user
    user_repo = get_user_repository()
    user = await user_repo.get_or_create_by_telegram_id(
        telegram_id=user_telegram.id,
        username=user_telegram.username,
        first_name=user_telegram.first_name,
        last_name=user_telegram.last_name
    )
    user_id = str(user["id"])
    
    # 3. Get conversation context
    conv_service = get_conversation_service()
    conversation_context = await conv_service.get_conversation_context(user_id)
    
    # 4. Save user message
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
    
    # 6. Save assistant response
    await conv_service.add_message(
        user_id=user_id,
        role="assistant",
        content=response,
        telegram_id=user_telegram.id
    )
    
    # 7. Send reply
    await update.message.reply_text(response)
```

### UserRepository Enhancement

Добавить метод `get_or_create_by_telegram_id`:

```python
async def get_or_create_by_telegram_id(
    self,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
) -> dict:
    """Get existing user or create new one by Telegram ID."""
    
    # Try to get existing user
    user = await self.get_by_telegram_id(telegram_id)
    if user:
        return user
    
    # Create new user
    user_data = {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
    }
    
    return await self.create(user_data)
```

### Fallback Strategy

Если база данных недоступна:

```python
try:
    user = await user_repo.get_or_create_by_telegram_id(...)
    user_id = str(user["id"])
except Exception as e:
    logger.warning(f"Database unavailable, using telegram_id as user_id: {e}")
    user_id = str(user_telegram.id)
```

## Testing Strategy

### Unit Tests

1. **test_handle_text_message_success**
   - Mock все зависимости
   - Проверить правильный порядок вызовов
   - Проверить отправку ответа

2. **test_handle_text_message_db_unavailable**
   - Mock UserRepository для выброса исключения
   - Проверить fallback на telegram_id
   - Проверить что обработка продолжается

3. **test_handle_text_message_ai_unavailable**
   - Mock AIService для возврата fallback ответа
   - Проверить что пользователь получает ответ

4. **test_get_or_create_by_telegram_id_existing**
   - Проверить возврат существующего пользователя

5. **test_get_or_create_by_telegram_id_new**
   - Проверить создание нового пользователя

### Integration Tests

1. **test_full_message_flow**
   - Реальная база данных (test DB)
   - Mock только Yandex GPT API
   - Проверить сохранение в БД

2. **test_conversation_context_preserved**
   - Отправить несколько сообщений
   - Проверить что контекст передается в AI

### Manual Testing

1. Отправить сообщение в бота
2. Проверить получение осмысленного ответа
3. Отправить несколько сообщений подряд
4. Проверить что бот помнит контекст
5. Проверить работу при отключенном Yandex GPT

## Performance Considerations

1. **Async/Await** - все операции асинхронные
2. **In-Memory Buffer** - быстрый доступ к последним сообщениям
3. **Database Fallback** - не блокирует работу при недоступности БД
4. **Retry Logic** - Yandex GPT клиент имеет встроенные retry (3 попытки)
5. **Timeout** - HTTP клиент имеет timeout 30 секунд

## Security Considerations

1. **API Keys** - хранятся в переменных окружения
2. **User Data** - минимальная информация из Telegram
3. **Logging** - не логируем полные сообщения пользователей (только первые 50 символов)
4. **Error Messages** - не раскрываем внутренние детали пользователю

## Deployment Notes

1. **Environment Variables Required:**
   - `YANDEX_GPT_API_KEY` - для AI ответов
   - `YANDEX_FOLDER_ID` - для Yandex GPT
   - `SUPABASE_URL` и `SUPABASE_KEY` - для БД

2. **Database Migration:**
   - Таблица `users` должна иметь поле `telegram_id`
   - Таблица `assistant_messages` должна существовать

3. **Graceful Degradation:**
   - Работает без БД (ограниченная функциональность)
   - Работает без Yandex GPT (fallback ответы)

## Future Enhancements

1. **Intent Classification** - использовать `AIService.classify_intent()` для определения намерений
2. **Structured Data Extraction** - использовать `AIService.extract_structured_data()` для создания задач/расходов
3. **Voice Messages** - реализовать `handle_voice_message`
4. **Rich Responses** - добавить кнопки и inline keyboard
5. **Rate Limiting** - ограничить количество запросов от одного пользователя

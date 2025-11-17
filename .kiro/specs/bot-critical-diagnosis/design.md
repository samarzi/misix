# Design Document: Bot Critical Diagnosis and Fix

## Overview

Проект MISIX имеет критические проблемы с работой Telegram-бота. Несмотря на то что код выглядит правильно, бот не функционирует должным образом - не работают команды, кнопки, память и веб-приложение. Этот документ описывает подход к диагностике и исправлению всех проблем.

## Root Cause Analysis

### Возможные причины проблем:

1. **База данных не подключена или таблицы не созданы**
   - Миграции не применены
   - Неправильные credentials
   - Таблицы отсутствуют

2. **Бот не запущен или запущен неправильно**
   - Handlers не зарегистрированы
   - Application не инициализирован
   - Webhook/polling не настроен

3. **Ошибки в runtime не логируются**
   - Exceptions проглатываются
   - Логи не выводятся
   - Нет мониторинга

4. **Проблемы с зависимостями**
   - Python 3.13 несовместимость
   - Отсутствующие пакеты
   - Конфликты версий

## Architecture

### Diagnostic Flow

```
1. Environment Check
   ↓
2. Database Connection Test
   ↓
3. Database Schema Validation
   ↓
4. Bot Initialization Test
   ↓
5. Handlers Registration Check
   ↓
6. AI Service Test
   ↓
7. End-to-End Message Test
   ↓
8. Generate Diagnostic Report
```

### Fix Flow

```
1. Apply Database Migrations
   ↓
2. Fix Bot Initialization
   ↓
3. Register All Handlers
   ↓
4. Test Each Command
   ↓
5. Test Callback Handlers
   ↓
6. Test Memory/Context
   ↓
7. Verify Web App Connection
   ↓
8. Deploy and Monitor
```

## Components and Interfaces

### 1. Diagnostic Script (`backend/diagnose.py`)

**Purpose:** Проверить все компоненты системы и выявить проблемы

**Interface:**
```python
class SystemDiagnostics:
    async def check_environment(self) -> DiagnosticResult
    async def check_database(self) -> DiagnosticResult
    async def check_database_schema(self) -> DiagnosticResult
    async def check_bot_initialization(self) -> DiagnosticResult
    async def check_handlers(self) -> DiagnosticResult
    async def check_ai_service(self) -> DiagnosticResult
    async def run_full_diagnostic(self) -> DiagnosticReport
```

**Output:**
```
✅ Environment Variables: OK
✅ Database Connection: OK
❌ Database Schema: MISSING TABLES (tasks, notes, mood_entries)
✅ Bot Initialization: OK
❌ Handlers Registration: MISSING (sleep handlers)
✅ AI Service: OK
⚠️  Overall Status: NEEDS FIXES
```

### 2. Database Migration Script (`backend/apply_all_migrations.py`)

**Purpose:** Применить все миграции и создать недостающие таблицы

**Interface:**
```python
class MigrationManager:
    async def check_existing_tables(self) -> List[str]
    async def apply_migration(self, migration_file: str) -> bool
    async def verify_schema(self) -> bool
    async def create_missing_tables(self) -> bool
```

**Migrations to apply:**
1. `001_complete_schema.sql` - Основные таблицы
2. `002_add_missing_columns.sql` - Дополнительные поля
3. `004_add_mood_entries.sql` - Таблица настроения
4. `005_add_reminders.sql` - Настройки напоминаний
5. `006_add_indexes.sql` - Индексы для производительности

### 3. Bot Startup Validator (`backend/app/bot/validator.py`)

**Purpose:** Проверить что бот правильно инициализирован перед запуском

**Interface:**
```python
class BotValidator:
    def validate_environment(self) -> ValidationResult
    def validate_handlers(self, app: Application) -> ValidationResult
    def validate_database(self) -> ValidationResult
    async def validate_full_startup(self) -> ValidationResult
```

**Checks:**
- Все environment variables установлены
- Все handlers зарегистрированы
- База данных доступна
- AI сервис доступен

### 4. Enhanced Logging

**Purpose:** Детальное логирование для отладки

**Changes:**
```python
# В каждом handler добавить:
logger.info(f"Handler called: {handler_name}, user: {user_id}")
logger.debug(f"Input data: {data}")
logger.error(f"Error in {handler_name}: {error}", exc_info=True)

# В bot/__init__.py добавить:
logger.info(f"Registered handlers: {[h.name for h in app.handlers]}")
logger.info(f"Bot username: {app.bot.username}")
```

### 5. Test Commands Script (`backend/test_bot_commands.py`)

**Purpose:** Автоматически протестировать все команды бота

**Interface:**
```python
class BotCommandTester:
    async def test_command(self, command: str) -> TestResult
    async def test_all_commands(self) -> List[TestResult]
    async def test_callback_handlers(self) -> List[TestResult]
```

**Tests:**
- `/start` - должен вернуть приветствие
- `/help` - должен вернуть справку
- `/tasks` - должен вернуть список задач или сообщение "нет задач"
- `/finances` - должен вернуть финансовую сводку
- `/mood` - должен вернуть историю настроения
- Callback кнопки - должны обработаться

## Data Models

### DiagnosticResult

```python
@dataclass
class DiagnosticResult:
    component: str
    status: str  # "OK", "WARNING", "ERROR"
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

### DiagnosticReport

```python
@dataclass
class DiagnosticReport:
    results: List[DiagnosticResult]
    overall_status: str  # "HEALTHY", "DEGRADED", "CRITICAL"
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_markdown(self) -> str:
        """Generate markdown report"""
```

## Error Handling

### Strategy

1. **Graceful Degradation**
   - Если БД недоступна → работать с in-memory
   - Если AI недоступен → использовать fallback ответы
   - Если handler fails → логировать и показать пользователю понятное сообщение

2. **Detailed Logging**
   - Каждая ошибка логируется с stack trace
   - Каждый handler логирует вход и выход
   - Каждый API call логирует request/response

3. **User-Friendly Messages**
   - Не показывать технические детали пользователю
   - Предлагать альтернативные действия
   - Давать понятные инструкции

### Error Recovery

```python
try:
    # Main logic
    result = await process_message(message)
except DatabaseError as e:
    logger.error(f"Database error: {e}", exc_info=True)
    # Fallback to in-memory
    result = await process_message_in_memory(message)
except AIServiceError as e:
    logger.error(f"AI service error: {e}", exc_info=True)
    # Use fallback response
    result = get_fallback_response(message)
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    # Show user-friendly message
    await send_error_message(user, "Произошла ошибка. Попробуйте позже.")
```

## Testing Strategy

### 1. Unit Tests

Test each component in isolation:
- Database connection
- Handler registration
- AI service calls
- Message processing

### 2. Integration Tests

Test components working together:
- Message → Handler → Service → Database
- Command → Handler → Response
- Callback → Handler → Database update

### 3. End-to-End Tests

Test full user scenarios:
- User sends message → Bot responds
- User sends /tasks → Bot shows tasks
- User clicks button → Bot updates state

### 4. Manual Testing Checklist

```markdown
- [ ] Отправить /start - получить приветствие
- [ ] Отправить /help - получить справку
- [ ] Отправить "напомни купить молоко" - создать задачу
- [ ] Отправить /tasks - увидеть задачу
- [ ] Отправить "потратил 500₽" - создать расход
- [ ] Отправить /finances - увидеть расход
- [ ] Отправить "отличное настроение" - создать запись
- [ ] Отправить /mood - увидеть настроение
- [ ] Нажать кнопку в /reminders - обработать callback
- [ ] Отправить голосовое - распознать и обработать
- [ ] Открыть веб-приложение - загрузиться
- [ ] Войти в веб-приложение - получить токен
```

## Deployment Plan

### Phase 1: Diagnosis (30 минут)

1. Запустить diagnostic script
2. Проанализировать результаты
3. Определить критические проблемы
4. Создать план исправления

### Phase 2: Database Fixes (1 час)

1. Проверить подключение к Supabase
2. Применить все миграции
3. Проверить наличие всех таблиц
4. Создать тестовые данные
5. Проверить CRUD операции

### Phase 3: Bot Fixes (1 час)

1. Исправить bot initialization
2. Зарегистрировать все handlers
3. Добавить детальное логирование
4. Протестировать каждую команду
5. Протестировать callback handlers

### Phase 4: Memory/Context Fixes (30 минут)

1. Проверить сохранение сообщений
2. Проверить загрузку контекста
3. Протестировать память в диалоге
4. Проверить лимиты истории

### Phase 5: Web App Check (30 минут)

1. Проверить CORS настройки
2. Проверить API endpoints
3. Проверить аутентификацию
4. Протестировать загрузку данных

### Phase 6: Monitoring Setup (30 минут)

1. Настроить structured logging
2. Добавить health check endpoint
3. Настроить alerts
4. Создать dashboard

## Success Criteria

### Must Have

- ✅ Все команды бота работают
- ✅ Кнопки и callbacks обрабатываются
- ✅ Память/контекст сохраняется
- ✅ Данные сохраняются в БД
- ✅ Веб-приложение подключается к API

### Should Have

- ✅ Детальное логирование
- ✅ Diagnostic script работает
- ✅ Graceful degradation при ошибках
- ✅ User-friendly error messages

### Nice to Have

- ⏳ Automated tests
- ⏳ Monitoring dashboard
- ⏳ Performance metrics
- ⏳ Error tracking (Sentry)

## Risks and Mitigation

### Risk 1: База данных недоступна

**Mitigation:**
- Использовать in-memory fallback
- Логировать все операции для последующей синхронизации
- Показывать пользователю что данные временные

### Risk 2: Python 3.13 несовместимость

**Mitigation:**
- Downgrade до Python 3.11
- Обновить requirements.txt
- Протестировать все зависимости

### Risk 3: Миграции конфликтуют

**Mitigation:**
- Создать backup БД перед миграциями
- Применять миграции по одной
- Проверять схему после каждой миграции

### Risk 4: Handlers не регистрируются

**Mitigation:**
- Добавить validation при старте
- Логировать все зарегистрированные handlers
- Fail fast если критические handlers отсутствуют

## Monitoring and Maintenance

### Metrics to Track

1. **Bot Health**
   - Uptime
   - Response time
   - Error rate
   - Active users

2. **Database Health**
   - Connection pool usage
   - Query performance
   - Failed queries
   - Storage usage

3. **AI Service Health**
   - API calls count
   - Response time
   - Error rate
   - Cost per day

### Alerts

1. **Critical**
   - Bot down > 5 minutes
   - Database connection lost
   - Error rate > 10%

2. **Warning**
   - Response time > 3 seconds
   - Memory usage > 80%
   - Disk usage > 80%

3. **Info**
   - New user registered
   - Daily summary sent
   - Backup completed

## Next Steps

После исправления критических проблем:

1. Увеличить test coverage до 70%
2. Добавить CI/CD pipeline
3. Настроить автоматический deployment
4. Добавить performance monitoring
5. Реализовать недостающие функции (модуль здоровья, хранилище и т.д.)

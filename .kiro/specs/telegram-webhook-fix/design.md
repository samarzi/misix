# Design Document: Telegram Webhook Fix

## Overview

Система не получает сообщения от Telegram, потому что webhook не установлен в Telegram API. Приложение запускается в webhook mode (определяется функцией `should_use_polling()`), но webhook URL не регистрируется в Telegram. Необходимо добавить автоматическую установку webhook при старте приложения и корректную обработку lifecycle.

## Architecture

### Current Flow (Broken)
```
1. App starts → lifespan() начинается
2. should_use_polling() возвращает False (webhook URL есть)
3. Polling НЕ запускается
4. Webhook НЕ устанавливается в Telegram
5. Telegram не знает куда отправлять обновления
6. Сообщения накапливаются в очереди Telegram
```

### Fixed Flow
```
1. App starts → lifespan() начинается
2. should_use_polling() проверяет конфигурацию
3. Если webhook mode:
   a. Устанавливаем webhook в Telegram API
   b. Проверяем статус установки
   c. Обрабатываем накопившиеся обновления
4. Если polling mode:
   a. Удаляем webhook из Telegram (если был)
   b. Запускаем polling
5. App shutdown → корректно очищаем webhook/polling
```

## Components and Interfaces

### 1. WebhookManager (New Component)

Новый компонент для управления webhook lifecycle:

```python
class WebhookManager:
    """Manages Telegram webhook lifecycle."""
    
    def __init__(self, application: Application):
        self.application = application
        self.webhook_url: Optional[str] = None
        self.is_set: bool = False
    
    async def set_webhook(self, url: str) -> bool:
        """Set webhook URL in Telegram API."""
        
    async def delete_webhook(self) -> bool:
        """Delete webhook from Telegram API."""
        
    async def get_webhook_info(self) -> dict:
        """Get current webhook status from Telegram."""
        
    async def process_pending_updates(self) -> int:
        """Process any pending updates after webhook setup."""
```

### 2. Modified bot/__init__.py

Добавляем функции для работы с webhook:

```python
def get_webhook_manager() -> Optional[WebhookManager]:
    """Get or create webhook manager."""
    
def get_webhook_url() -> Optional[str]:
    """Determine webhook URL from configuration."""
```

### 3. Modified web/main.py lifespan

Обновляем lifecycle для установки webhook:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing startup code ...
    
    # Phase 3: Initialize Telegram Bot
    if should_use_polling():
        # Delete webhook if exists
        # Start polling
    else:
        # Set webhook
        # Process pending updates
    
    yield
    
    # Shutdown
    if webhook_mode:
        # Optionally delete webhook
    else:
        # Stop polling
```

## Data Models

### WebhookInfo
```python
@dataclass
class WebhookInfo:
    """Information about current webhook status."""
    url: str
    has_custom_certificate: bool
    pending_update_count: int
    last_error_date: Optional[int]
    last_error_message: Optional[str]
    max_connections: Optional[int]
    allowed_updates: Optional[list[str]]
```

### WebhookSetupResult
```python
@dataclass
class WebhookSetupResult:
    """Result of webhook setup operation."""
    success: bool
    webhook_url: str
    pending_updates_processed: int
    error_message: Optional[str]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Acceptance Criteria Testing Prework

1.1 WHEN приложение запускается в production окружении THEN система SHALL установить webhook URL в Telegram API
Thoughts: Это проверяемое свойство - для любого production окружения с валидным webhook URL, после старта приложения webhook должен быть установлен в Telegram API
Testable: yes - property

1.2 WHEN Telegram отправляет обновление на webhook endpoint THEN система SHALL успешно обработать обновление и отправить ответ пользователю
Thoughts: Это интеграционный тест - можно отправить mock update на endpoint и проверить, что он обработан
Testable: yes - example

1.3 WHEN webhook URL недоступен или невалиден THEN система SHALL автоматически переключиться на polling mode
Thoughts: Это проверяемое свойство - для любого невалидного URL система должна переключиться на polling
Testable: yes - property

1.4 WHEN приложение останавливается THEN система SHALL корректно удалить webhook из Telegram API
Thoughts: Это специфичный сценарий shutdown - можно проверить примером
Testable: yes - example

1.5 WHEN webhook установлен THEN система SHALL логировать успешную установку с URL адресом
Thoughts: Это проверка логирования - можно проверить, что лог содержит нужную информацию
Testable: yes - property

2.1 WHEN приложение запускается THEN система SHALL проверить текущий статус webhook в Telegram API
Thoughts: Это проверяемое свойство - при любом старте должна быть проверка статуса
Testable: yes - property

2.2 WHEN webhook установлен успешно THEN система SHALL логировать URL webhook и количество ожидающих обновлений
Thoughts: Это проверка логирования после успешной установки
Testable: yes - property

2.3 WHEN webhook не установлен THEN система SHALL логировать предупреждение и причину
Thoughts: Это проверка логирования в случае неудачи
Testable: yes - property

2.4 WHEN происходит ошибка при установке webhook THEN система SHALL логировать детальную информацию об ошибке
Thoughts: Это проверка обработки ошибок и логирования
Testable: yes - property

2.5 WHEN система переключается между webhook и polling THEN система SHALL логировать причину переключения
Thoughts: Это проверка логирования при изменении режима
Testable: yes - property

3.1 WHEN переменная TELEGRAM_WEBHOOK_URL установлена THEN система SHALL использовать этот URL для webhook
Thoughts: Это проверка конфигурации - для любого валидного URL в переменной, система должна его использовать
Testable: yes - property

3.2 WHEN переменная TELEGRAM_WEBHOOK_URL не установлена THEN система SHALL автоматически сформировать URL из BACKEND_BASE_URL
Thoughts: Это проверка fallback логики
Testable: yes - property

3.3 WHEN BACKEND_BASE_URL указывает на localhost THEN система SHALL использовать polling вместо webhook
Thoughts: Это edge case для локальной разработки
Testable: edge-case

3.4 WHEN webhook URL не начинается с https:// THEN система SHALL отклонить URL и использовать polling
Thoughts: Это валидация URL - для любого non-HTTPS URL должен быть polling
Testable: yes - property

3.5 WHEN все необходимые переменные окружения установлены THEN система SHALL успешно настроить webhook при старте
Thoughts: Это интеграционный тест полного flow
Testable: yes - example

4.1 WHEN webhook устанавливается и есть ожидающие обновления THEN система SHALL обработать все накопившиеся обновления
Thoughts: Это проверяемое свойство - для любого количества ожидающих обновлений, все должны быть обработаны
Testable: yes - property

4.2 WHEN обработка ожидающих обновлений завершается THEN система SHALL логировать количество обработанных обновлений
Thoughts: Это проверка логирования после обработки
Testable: yes - property

4.3 WHEN обработка обновления завершается с ошибкой THEN система SHALL логировать ошибку но продолжить обработку остальных обновлений
Thoughts: Это проверка error handling - система должна быть устойчива к ошибкам в отдельных обновлениях
Testable: yes - property

4.4 WHEN все обновления обработаны THEN система SHALL подтвердить готовность к приему новых обновлений
Thoughts: Это проверка финального состояния после обработки
Testable: yes - example

4.5 WHEN система переключается с polling на webhook THEN система SHALL корректно завершить polling перед установкой webhook
Thoughts: Это проверка корректного перехода между режимами
Testable: yes - property

### Property Reflection

Reviewing all properties for redundancy:

- Properties 2.2, 2.3, 2.4, 2.5 все проверяют логирование в разных сценариях - можно объединить в одно свойство "система логирует все важные события webhook lifecycle"
- Properties 1.1 и 3.5 частично перекрываются - оба проверяют успешную установку webhook
- Properties 1.3 и 3.4 оба проверяют fallback на polling при проблемах с webhook
- Property 4.2 можно объединить с 4.1 - обработка обновлений включает логирование

После рефлексии оставляем ключевые свойства:

### Correctness Properties

Property 1: Webhook установка в production
*For any* production environment with valid HTTPS webhook URL, after application startup, the webhook SHALL be registered in Telegram API with that URL
**Validates: Requirements 1.1, 3.1, 3.5**

Property 2: Fallback на polling при невалидном webhook
*For any* webhook URL that is not HTTPS or points to localhost, the system SHALL use polling mode instead of webhook mode
**Validates: Requirements 1.3, 3.3, 3.4**

Property 3: Обработка накопившихся обновлений
*For any* number of pending updates when webhook is set, all updates SHALL be processed and the count SHALL be logged
**Validates: Requirements 4.1, 4.2**

Property 4: Устойчивость к ошибкам обработки
*For any* update that fails to process, the system SHALL log the error and continue processing remaining updates without stopping
**Validates: Requirements 4.3**

Property 5: Корректный lifecycle webhook
*For any* application shutdown, if webhook mode is active, the webhook SHALL be properly cleaned up (optionally deleted from Telegram)
**Validates: Requirements 1.4**

Property 6: Полное логирование webhook операций
*For any* webhook operation (set, delete, check status, mode switch), the system SHALL log the operation with relevant details (URL, status, reason)
**Validates: Requirements 1.5, 2.1, 2.2, 2.3, 2.4, 2.5**

Property 7: Корректный переход между режимами
*For any* transition from polling to webhook or vice versa, the previous mode SHALL be properly stopped before starting the new mode
**Validates: Requirements 4.5**

## Error Handling

### Webhook Setup Errors

1. **Network Errors**: Retry with exponential backoff, fallback to polling after 3 attempts
2. **Invalid Token**: Log critical error, fail application startup
3. **Invalid URL**: Log error, automatically switch to polling
4. **Telegram API Errors**: Log detailed error, retry or fallback to polling

### Update Processing Errors

1. **Individual Update Fails**: Log error, continue with next update
2. **Handler Exception**: Catch, log, send user-friendly error message
3. **Timeout**: Log warning, skip update, continue

### Configuration Errors

1. **Missing TELEGRAM_BOT_TOKEN**: Skip bot initialization, log warning
2. **Invalid BACKEND_BASE_URL**: Use polling mode
3. **Conflicting Configuration**: Prefer explicit TELEGRAM_WEBHOOK_URL over derived URL

## Testing Strategy

### Unit Tests

1. **WebhookManager Tests**:
   - Test webhook URL validation
   - Test webhook set/delete operations with mocked Telegram API
   - Test pending updates processing
   - Test error handling

2. **Configuration Tests**:
   - Test `get_webhook_url()` with various env var combinations
   - Test `should_use_polling()` logic
   - Test URL validation

3. **Lifecycle Tests**:
   - Test startup sequence with webhook mode
   - Test startup sequence with polling mode
   - Test shutdown cleanup

### Integration Tests

1. **End-to-End Webhook Flow**:
   - Start app with webhook configuration
   - Verify webhook is set in Telegram
   - Send test update to webhook endpoint
   - Verify update is processed
   - Shutdown app
   - Verify cleanup

2. **Polling Fallback**:
   - Start app with invalid webhook URL
   - Verify polling starts
   - Verify webhook is not set

3. **Pending Updates**:
   - Set webhook with pending updates
   - Verify all updates are processed
   - Verify count is logged

### Property-Based Tests

Using `pytest` with `hypothesis` library:

1. **Property 1**: Test webhook setup with various valid production URLs
2. **Property 2**: Test polling fallback with various invalid URLs
3. **Property 3**: Test pending updates processing with random counts
4. **Property 4**: Test error resilience with random failing updates
5. **Property 6**: Test logging with various webhook operations

Each property test should run minimum 100 iterations.

## Implementation Notes

### Phase 1: Create WebhookManager
- New file: `backend/app/bot/webhook.py`
- Implement WebhookManager class
- Add comprehensive logging
- Add error handling

### Phase 2: Update bot/__init__.py
- Add `get_webhook_manager()` function
- Add `get_webhook_url()` function
- Export new functions

### Phase 3: Update web/main.py
- Modify lifespan() to use WebhookManager
- Add webhook setup in Phase 3
- Add proper cleanup in shutdown
- Add detailed logging

### Phase 4: Update Configuration
- Add TELEGRAM_WEBHOOK_URL to render.yaml
- Update .env.example
- Document webhook configuration

### Phase 5: Testing
- Write unit tests
- Write integration tests
- Manual testing with real Telegram bot

## Deployment Plan

1. **Deploy Code Changes**: Push webhook manager implementation
2. **Set Environment Variable**: Add `TELEGRAM_WEBHOOK_URL=https://misix.onrender.com/bot/webhook` to Render
3. **Restart Application**: Trigger redeploy on Render
4. **Verify Webhook**: Check logs for successful webhook setup
5. **Test Bot**: Send test message to bot
6. **Monitor**: Watch logs for any errors

## Rollback Plan

If webhook setup fails:
1. Remove `TELEGRAM_WEBHOOK_URL` from environment
2. Application will automatically fallback to polling
3. Bot will continue working via polling
4. Investigate and fix webhook issues
5. Re-enable webhook when ready

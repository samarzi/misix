# Design Document

## Overview

The Telegram bot successfully initializes but does not receive messages because the polling mechanism is not started. The code in `telegram.py` contains polling functions (`_start_polling`, `_poll_updates`) but they are never called from `main.py`. The application lifecycle in `main.py` only calls `application.initialize()` and `application.start()` but does not trigger the polling loop.

The solution is to integrate the existing polling mechanism from `telegram.py` into the application startup flow in `main.py`.

## Architecture

### Current Flow (Broken)
```
main.py:lifespan()
  ├─> get_application() → creates Application
  ├─> application.initialize()
  ├─> application.start()
  └─> ❌ No polling started
```

### Fixed Flow
```
main.py:lifespan()
  ├─> get_application() → creates Application
  ├─> application.initialize()
  ├─> application.start()
  └─> start_polling_if_needed(application) → starts polling loop
      ├─> Check if webhook configured
      ├─> If no webhook → start polling
      └─> Create asyncio task for _poll_updates()
```

## Components and Interfaces

### 1. Polling Manager Module (`backend/app/bot/polling.py`)

New module to manage polling lifecycle:

```python
class PollingManager:
    """Manages Telegram bot polling lifecycle."""
    
    def __init__(self, application: Application):
        self.application = application
        self.polling_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start_polling(self) -> None:
        """Start the polling loop if not already running."""
        
    async def stop_polling(self) -> None:
        """Stop the polling loop gracefully."""
        
    async def _poll_updates(self) -> None:
        """Internal polling loop that fetches updates from Telegram."""
```

### 2. Integration Points

**In `backend/app/bot/__init__.py`:**
- Add `get_polling_manager()` function
- Store polling manager as module-level variable

**In `backend/app/web/main.py`:**
- Import polling manager
- Start polling after `application.start()`
- Stop polling before `application.stop()`

### 3. Configuration Detection

The system will automatically detect whether to use webhook or polling:

```python
def should_use_polling() -> bool:
    """Determine if polling should be used based on configuration."""
    # Check if webhook URL is configured
    webhook_url = settings.telegram_webhook_url or settings.backend_base_url
    
    # If no webhook URL or it's not a valid HTTPS endpoint, use polling
    if not webhook_url:
        return True
    
    # Check if URL is valid HTTPS
    if not webhook_url.startswith("https://"):
        return True
    
    # Check if it's localhost/example (not valid for webhook)
    if "localhost" in webhook_url or "127.0.0.1" in webhook_url:
        return True
    
    return False
```

## Data Models

### PollingState

```python
@dataclass
class PollingState:
    """State of the polling mechanism."""
    is_running: bool
    last_update_id: int
    updates_received: int
    errors_count: int
    last_error: Optional[str]
    started_at: Optional[datetime]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Polling starts when webhook is not configured

*For any* application startup where webhook URL is not configured, the polling mechanism should be started automatically.

**Validates: Requirements 3.2**

### Property 2: Updates are processed in order

*For any* sequence of Telegram updates received, they should be processed in the order determined by their update_id field.

**Validates: Requirements 1.3**

### Property 3: Polling recovers from errors

*For any* error encountered during polling, the system should log the error and retry after 5 seconds without crashing.

**Validates: Requirements 1.4, 3.5**

### Property 4: Polling stops cleanly on shutdown

*For any* application shutdown, the polling task should be cancelled and awaited before the application stops.

**Validates: Requirements 1.5**

### Property 5: Only one polling loop runs at a time

*For any* application instance, at most one polling task should be running concurrently.

**Validates: Requirements 3.3**

## Error Handling

### Network Errors
- **Timeout**: Retry immediately with exponential backoff (5s, 10s, 20s, max 60s)
- **Connection Error**: Log error, wait 5 seconds, retry
- **Rate Limit**: Respect Retry-After header from Telegram

### API Errors
- **Invalid Token**: Log critical error, stop polling, raise exception
- **Conflict (409)**: Another instance is running, log error, stop polling
- **Server Error (5xx)**: Temporary issue, retry after 10 seconds

### Handler Errors
- **Exception in Handler**: Log error with full traceback, continue processing next update
- **Timeout in Handler**: Log warning, continue to next update

### Graceful Degradation
- If polling fails to start: Log error but don't crash application
- If updates can't be processed: Log error, skip update, continue polling
- If database is unavailable: Continue processing but log warnings

## Testing Strategy

### Unit Tests

**Test File**: `backend/tests/unit/test_polling_manager.py`

Tests to implement:
1. `test_polling_starts_when_no_webhook` - Verify polling starts when webhook URL is None
2. `test_polling_stops_gracefully` - Verify polling task is cancelled and awaited
3. `test_updates_processed_in_order` - Mock updates and verify order
4. `test_error_recovery` - Simulate network error and verify retry
5. `test_only_one_polling_loop` - Call start_polling twice, verify only one task

### Property-Based Tests

**Test File**: `backend/tests/property/test_polling_properties.py`

Using `hypothesis` library for property-based testing:

1. **Property 1 Test**: Generate random configurations, verify polling starts when webhook is invalid
2. **Property 2 Test**: Generate random sequences of update IDs, verify they're processed in order
3. **Property 3 Test**: Generate random errors, verify system recovers
4. **Property 5 Test**: Generate random concurrent start attempts, verify only one loop runs

### Integration Tests

**Test File**: `backend/tests/integration/test_bot_polling.py`

Tests to implement:
1. `test_bot_receives_messages_via_polling` - Send test message, verify it's received
2. `test_polling_survives_network_interruption` - Simulate network failure, verify recovery
3. `test_application_lifecycle_with_polling` - Start and stop application, verify clean shutdown

## Implementation Notes

### Asyncio Task Management

The polling loop must be managed as an asyncio task:

```python
# Start
self.polling_task = asyncio.create_task(self._poll_updates())

# Stop
if self.polling_task:
    self.polling_task.cancel()
    try:
        await self.polling_task
    except asyncio.CancelledError:
        pass  # Expected
```

### Update Offset Tracking

The `offset` parameter in `getUpdates` must be managed correctly:

```python
offset = 0
while True:
    updates = await bot.get_updates(offset=offset, timeout=30)
    for update in updates:
        offset = max(offset, update.update_id + 1)
        await application.process_update(update)
```

### Logging Best Practices

- Log polling start/stop at INFO level
- Log each batch of updates at DEBUG level
- Log errors at ERROR level with full context
- Include update_id in all update-related logs

### Production Considerations

- **Timeout**: Use 30-second timeout for long polling
- **Batch Size**: Telegram returns up to 100 updates per request
- **Memory**: Clear processed updates to avoid memory leaks
- **Monitoring**: Log metrics (updates/minute, errors/hour)

## Dependencies

- `python-telegram-bot>=20.0` - Already installed
- `asyncio` - Python standard library
- No new dependencies required

## Migration Path

1. Create `backend/app/bot/polling.py` with `PollingManager` class
2. Update `backend/app/bot/__init__.py` to export polling manager
3. Update `backend/app/web/main.py` to start/stop polling
4. Test locally with polling
5. Deploy to production
6. Monitor logs for successful message reception

## Rollback Plan

If polling causes issues:
1. Revert changes to `main.py`
2. Application will run without polling (current state)
3. No data loss or corruption risk
4. Can investigate and fix issues offline

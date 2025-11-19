# Design Document: Bot Memory and Voice Message Fix

## Overview

This design addresses three critical bugs preventing the bot from functioning correctly:
1. User creation fails due to NULL full_name constraint violation
2. Bot has no memory because user_id is lost (becomes None)
3. Voice messages fail with immutable object modification error

The solution involves fixing the User Repository to generate full_name, ensuring user_id persistence throughout the message flow, and properly handling Telegram's immutable Update objects.

## Architecture

### Current Flow (Broken)
```
Telegram Update → Message Handler → User Repository (FAILS: full_name=NULL)
                                  → user_id = None
                                  → Conversation Service (FAILS: user_id="None")
                                  → No memory!

Voice Update → Voice Handler → create_mock_text_update (FAILS: immutable object)
```

### Fixed Flow
```
Telegram Update → Message Handler → User Repository (✓ generates full_name)
                                  → user_id = UUID string
                                  → Conversation Service (✓ valid UUID)
                                  → Memory works!

Voice Update → Voice Handler → Create new Update properly (✓ no mutation)
                            → Text Handler → Normal flow
```

## Components and Interfaces

### 1. UserRepository (backend/app/repositories/user.py)

**Modified Method:**
```python
async def get_or_create_by_telegram_id(
    self,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
) -> dict:
    """Get existing user or create new one by Telegram ID.
    
    Now generates full_name from available data.
    """
```

**New Helper Method:**
```python
def _generate_full_name(
    first_name: Optional[str],
    last_name: Optional[str],
    username: Optional[str]
) -> str:
    """Generate full_name from available user data.
    
    Priority:
    1. first_name + last_name
    2. first_name only
    3. last_name only  
    4. username
    5. "Telegram User" (fallback)
    """
```

### 2. Message Handler (backend/app/bot/handlers/message.py)

**Modified: handle_text_message**
- Ensure user_id is always UUID string or None
- Skip DB operations when user_id is None
- Don't pass None to Conversation Service DB methods

**Key Changes:**
```python
# Before (broken):
user_id = None  # Then passed to DB queries → ERROR

# After (fixed):
if user_id is None:
    # Skip DB operations
    conversation_context = []  # Empty context
    # Don't call add_message with None user_id
else:
    # Normal flow with valid UUID
    conversation_context = await conv_service.get_conversation_context(user_id)
    await conv_service.add_message(user_id=user_id, ...)
```

### 3. Voice Handler (backend/app/bot/handlers/message.py)

**Modified: create_mock_text_update**
- Don't modify immutable Telegram objects
- Create new Update with new Message properly

**Key Changes:**
```python
# Before (broken):
mock_message = copy.copy(voice_update.message)
mock_message.text = text  # ERROR: can't set attribute!

# After (fixed):
# Create new Message object with text
from telegram import Message as TelegramMessage
mock_message = TelegramMessage(
    message_id=voice_update.message.message_id,
    date=voice_update.message.date,
    chat=voice_update.message.chat,
    from_user=voice_update.message.from_user,
    text=text  # Set during construction
)
```

### 4. Conversation Service (backend/app/services/conversation_service.py)

**Modified Methods:**
- `get_conversation_context(user_id)` - handle None gracefully
- `add_message(user_id, ...)` - skip if user_id is None
- `_get_latest_summary(user_id)` - return empty if None

**Key Changes:**
```python
async def get_conversation_context(self, user_id: Optional[str]) -> list:
    """Get conversation context.
    
    Returns empty list if user_id is None (fallback mode).
    """
    if user_id is None:
        return []
    # ... normal flow
    
async def add_message(self, user_id: Optional[str], ...):
    """Add message to history.
    
    Skips DB operation if user_id is None (fallback mode).
    """
    if user_id is None:
        logger.warning("Skipping message save - no user_id (fallback mode)")
        return
    # ... normal flow
```

## Data Models

### User Model (users table)

**Current Schema:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,  -- ❌ PROBLEM: can be NULL from code
    email TEXT,
    password_hash TEXT,
    telegram_id BIGINT UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**No schema changes needed** - we fix the code to always provide full_name.

### Message Flow Data

**User ID Type:**
- Database: UUID
- Python: `str` (UUID as string) or `None` (fallback mode)
- Never: `"None"` string or integer telegram_id

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: full_name generation from names
*For any* user creation with first_name and/or last_name, the generated full_name should contain the provided names in correct order
**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Username fallback for full_name
*For any* user creation with null names but valid username, the full_name should equal the username
**Validates: Requirements 1.4**

### Property 3: user_id is valid UUID string
*For any* successful user creation or retrieval, the user_id should be a valid UUID string format
**Validates: Requirements 2.1, 2.2**

### Property 4: No None in database queries
*For any* database operation, if user_id is None, the operation should be skipped and no query should execute with None parameter
**Validates: Requirements 2.3, 2.4, 2.5**

### Property 5: Voice message creates valid text update
*For any* voice message transcription, the resulting Update object should have a valid text message that can be processed normally
**Validates: Requirements 3.1, 3.3**

### Property 6: Original Telegram objects unchanged
*For any* voice message processing, the original Update and Message objects should remain unmodified after creating mock update
**Validates: Requirements 3.2**

### Property 7: Transcription shown to user
*For any* successful voice transcription, a message containing the transcribed text should be sent to the user before processing
**Validates: Requirements 3.5**

## Error Handling

### 1. User Creation Failure
```python
try:
    user = await user_repo.get_or_create_by_telegram_id(...)
    user_id = str(user["id"])
except Exception as e:
    logger.error(f"Failed to get/create user: {e}")
    logger.warning("Continuing in fallback mode - data will not be saved")
    user_id = None  # Fallback mode
    # Continue processing but skip DB operations
```

### 2. Voice Processing Failure
```python
try:
    transcription = await speech_kit.transcribe_audio(audio_bytes)
    if not transcription:
        await update.message.reply_text("Не удалось распознать речь...")
        return
except Exception as e:
    logger.error(f"Transcription failed: {e}")
    await update.message.reply_text("Произошла ошибка при распознавании речи...")
    return
```

### 3. Fallback Mode Behavior
When `user_id is None`:
- ✓ Bot still responds to messages
- ✓ AI generates responses
- ✗ No conversation history saved
- ✗ No memory between messages
- ✓ User gets clear responses
- ✓ No crashes or errors

## Testing Strategy

### Unit Tests
- Test `_generate_full_name()` with various input combinations
- Test user creation with different name/username scenarios
- Test fallback mode behavior (user_id=None)
- Test voice Update creation without mutation
- Test conversation service with None user_id

### Property-Based Tests
We will use `pytest` with `hypothesis` for property-based testing in Python.

**Configuration:**
- Minimum 100 iterations per property test
- Use `hypothesis.strategies` for generating test data
- Tag each test with the property number from design doc

**Test Structure:**
```python
from hypothesis import given, strategies as st
import pytest

@given(
    first_name=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    last_name=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    username=st.one_of(st.none(), st.text(min_size=1, max_size=50))
)
@pytest.mark.property_test
def test_property_1_full_name_generation(first_name, last_name, username):
    """Property 1: full_name generation from names
    
    Feature: bot-memory-and-voice-fix, Property 1
    """
    # Test implementation
    pass
```

### Integration Tests
- Test full message flow with real Telegram Update objects
- Test voice message end-to-end flow
- Test fallback mode doesn't break the bot
- Test memory works after fix (multiple messages from same user)

### Manual Testing Checklist
1. Send text message → verify user created with full_name
2. Send multiple messages → verify bot remembers context
3. Send voice message → verify transcription shown and processed
4. Check database → verify no NULL full_name values
5. Check logs → verify no "invalid input syntax for type uuid: None" errors

## Implementation Notes

### Priority Order
1. **CRITICAL**: Fix full_name generation (blocks user creation)
2. **CRITICAL**: Fix user_id persistence (blocks memory)
3. **HIGH**: Fix voice message handling (feature broken)

### Deployment Strategy
1. Deploy code changes
2. No database migration needed
3. Existing users with NULL full_name will be fixed on next interaction
4. Monitor logs for errors
5. Test with real Telegram messages

### Rollback Plan
If issues occur:
1. Revert code changes
2. Bot returns to previous state (broken but stable)
3. No data loss (no schema changes)

## Dependencies

- `python-telegram-bot` - Telegram API wrapper
- `hypothesis` - Property-based testing library
- `pytest` - Testing framework
- Supabase/PostgreSQL - Database

## Performance Considerations

- full_name generation is O(1) string concatenation
- No additional database queries
- Voice processing unchanged (same flow)
- Fallback mode slightly faster (skips DB calls)

## Security Considerations

- No security changes
- User data handling unchanged
- No new attack vectors
- Fallback mode doesn't expose sensitive data

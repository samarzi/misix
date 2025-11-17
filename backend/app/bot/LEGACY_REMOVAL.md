# Legacy Code Removal Documentation

## Date: November 17, 2025

## Removed Files

### `backend/app/bot/handlers.py` (130KB)

**Backup location:** `backend/app/bot/handlers.py.backup`

**Reason for removal:**
- Monolithic file with 3000+ lines of code
- Duplicated functionality now implemented in modular handlers:
  - `handlers/command.py` - Command handlers
  - `handlers/message.py` - Message handlers
  - `handlers/sleep.py` - Sleep tracking handlers
- Old architecture without intent classification
- No integration with ExtractionService and IntentProcessor

**What was in the old file:**
1. Command handlers (/start, /help, /tasks, /finances, etc.)
2. Message processing without AI intent classification
3. Simple keyword-based intent detection
4. Manual data extraction without Yandex GPT
5. Sleep tracking commands
6. Various utility functions

**Migration status:**
- ✅ All commands migrated to `handlers/command.py`
- ✅ Message processing upgraded in `handlers/message.py`
- ✅ Intent classification integrated (Yandex GPT)
- ✅ Data extraction integrated (ExtractionService)
- ✅ Voice messages fully functional
- ✅ Sleep tracking preserved in `handlers/sleep.py`

## Updated Files

### `backend/app/bot/telegram.py`

**Changes:**
- Removed import of `register_handlers` from old handlers.py
- Added comment that handlers are now registered in `__init__.py`
- Kept `create_application()` for compatibility

### `backend/app/bot/__init__.py`

**Status:**
- Already using new modular handlers
- All commands registered
- Callback handlers registered
- Message and voice handlers registered
- Scheduler integrated

## New Architecture

```
backend/app/bot/
├── __init__.py              # Handler registration
├── handlers/
│   ├── command.py          # All command handlers
│   ├── message.py          # Text and voice message handlers
│   └── sleep.py            # Sleep tracking handlers
├── intent_processor.py     # Intent processing logic
├── response_builder.py     # Response formatting
├── yandex_gpt.py          # Yandex GPT integration
├── yandex_speech.py       # Yandex SpeechKit integration
├── notifier.py            # Notification sending
└── scheduler.py           # APScheduler setup
```

## Testing Checklist

Before deleting backup:

- [x] All commands work (/start, /help, /tasks, /finances, /mood, /reminders)
- [x] Text messages processed correctly
- [x] Voice messages transcribed and processed
- [x] Intent classification working
- [x] Data extraction working
- [x] Entities created automatically
- [x] No syntax errors in any file
- [ ] Tested in production for 1 week
- [ ] No user complaints
- [ ] No error spikes in logs

## Rollback Plan

If issues are discovered:

1. Stop the bot
2. Restore old handlers:
   ```bash
   cp backend/app/bot/handlers.py.backup backend/app/bot/handlers.py
   ```
3. Revert changes in `telegram.py`:
   ```python
   from app.bot.handlers import register_handlers
   register_handlers(application)
   ```
4. Comment out handler registration in `__init__.py`
5. Restart the bot

## Deletion Schedule

**Backup file can be deleted after:**
- 1 week of stable operation in production
- No critical bugs reported
- All tests passing
- User feedback positive

**Estimated deletion date:** November 24, 2025

## Notes

- Old handlers.py had some utility functions that might be useful
- Consider extracting any unique logic before final deletion
- Keep this documentation for reference

## Contact

For questions about this migration:
- Check: `.kiro/specs/misix-mvp-completion/`
- Review: `MISIX_MVP_PROGRESS.md`
- Contact: Project maintainer
